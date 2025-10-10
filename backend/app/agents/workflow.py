"""LangGraph workflow orchestration for multi-agent system."""

import logging
from typing import Any, Dict, List, Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.agents.state import AgentNodes, AgentState, WorkflowConfig

logger = logging.getLogger(__name__)


class MedSearchWorkflow:
    """Multi-agent workflow orchestrator using LangGraph."""

    def __init__(self, config: WorkflowConfig = WorkflowConfig()) -> None:
        """Initialize workflow with configuration."""
        self.config = config
        self.graph = self._build_graph()
        self.checkpointer = MemorySaver()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow graph."""
        # Create workflow graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node(AgentNodes.ANALYZE_QUERY, self._analyze_query_node)
        workflow.add_node(AgentNodes.RESEARCH_AGENT, self._research_agent_node)
        workflow.add_node(AgentNodes.CLINICAL_AGENT, self._clinical_agent_node)
        workflow.add_node(AgentNodes.DRUG_AGENT, self._drug_agent_node)
        workflow.add_node(AgentNodes.SYNTHESIZE, self._synthesize_node)

        # Set entry point
        workflow.set_entry_point(AgentNodes.ANALYZE_QUERY)

        # Add conditional edges from query analysis
        workflow.add_conditional_edges(
            AgentNodes.ANALYZE_QUERY,
            self._route_after_analysis,
            {
                "research": AgentNodes.RESEARCH_AGENT,
                "clinical": AgentNodes.CLINICAL_AGENT,
                "drug": AgentNodes.DRUG_AGENT,
                "all": AgentNodes.RESEARCH_AGENT,  # Start with research for "all"
            },
        )

        # Add edges from research agent
        workflow.add_conditional_edges(
            AgentNodes.RESEARCH_AGENT,
            self._route_after_research,
            {
                "clinical": AgentNodes.CLINICAL_AGENT,
                "drug": AgentNodes.DRUG_AGENT,
                "synthesize": AgentNodes.SYNTHESIZE,
            },
        )

        # Add edges from clinical agent
        workflow.add_conditional_edges(
            AgentNodes.CLINICAL_AGENT,
            self._route_after_clinical,
            {
                "drug": AgentNodes.DRUG_AGENT,
                "synthesize": AgentNodes.SYNTHESIZE,
            },
        )

        # Add edge from drug agent to synthesis
        workflow.add_edge(AgentNodes.DRUG_AGENT, AgentNodes.SYNTHESIZE)

        # Add edge from synthesis to end
        workflow.add_edge(AgentNodes.SYNTHESIZE, END)

        return workflow

    async def _analyze_query_node(self, state: AgentState) -> Dict[str, Any]:
        """Analyze query to determine intent and extract entities."""
        from app.agents.query_analyzer import analyze_query_async

        logger.info(f"Analyzing query: {state['query'][:50]}...")

        try:
            # Build conversation context from messages
            conversation_context = None
            if state.get("messages"):
                conversation_context = {"messages": state["messages"]}

            analysis = await analyze_query_async(
                query=state["query"],
                conversation_context=conversation_context,
            )

            # Use expanded query if available (for follow-up questions)
            effective_query = analysis.expanded_query or state["query"]

            return {
                "query": effective_query,  # Update query with expanded version
                "intent": analysis.intent,
                "entities": analysis.entities,
                "current_step": "query_analysis",
                "progress": 10,
                "messages": [{"role": "system", "content": f"Intent: {analysis.intent}, Expanded: {effective_query}"}],
            }

        except Exception as e:
            logger.error(f"Error in query analysis: {e}")
            return {
                "errors": state.get("errors", []) + [f"Query analysis failed: {str(e)}"],
                "current_step": "query_analysis_error",
            }

    async def _research_agent_node(self, state: AgentState) -> Dict[str, Any]:
        """Execute research agent for PubMed search."""
        from app.agents.research_agent import execute_research_agent

        logger.info("Executing research agent...")

        try:
            results = await execute_research_agent(
                query=state["query"],
                query_embedding=state.get("query_embedding"),
                filters=state.get("filters"),
                max_results=self.config.max_results_per_agent,
            )

            agents_used = state.get("agents_used", [])
            if "research_agent" not in agents_used:
                agents_used.append("research_agent")

            return {
                "research_results": results,
                "agents_used": agents_used,
                "current_step": "research_search",
                "progress": 40,
            }

        except Exception as e:
            logger.error(f"Error in research agent: {e}")
            return {
                "errors": state.get("errors", []) + [f"Research agent failed: {str(e)}"],
                "research_results": [],
            }

    async def _clinical_agent_node(self, state: AgentState) -> Dict[str, Any]:
        """Execute clinical trials agent."""
        from app.agents.clinical_agent import execute_clinical_agent

        logger.info("Executing clinical trials agent...")

        try:
            results = await execute_clinical_agent(
                query=state["query"],
                query_embedding=state.get("query_embedding"),
                filters=state.get("filters"),
                max_results=self.config.max_results_per_agent,
            )

            agents_used = state.get("agents_used", [])
            if "clinical_agent" not in agents_used:
                agents_used.append("clinical_agent")

            return {
                "clinical_results": results,
                "agents_used": agents_used,
                "current_step": "clinical_search",
                "progress": 60,
            }

        except Exception as e:
            logger.error(f"Error in clinical agent: {e}")
            return {
                "errors": state.get("errors", []) + [f"Clinical agent failed: {str(e)}"],
                "clinical_results": [],
            }

    async def _drug_agent_node(self, state: AgentState) -> Dict[str, Any]:
        """Execute drug information agent."""
        from app.agents.drug_agent import execute_drug_agent

        logger.info("Executing drug information agent...")

        try:
            results = await execute_drug_agent(
                query=state["query"],
                query_embedding=state.get("query_embedding"),
                filters=state.get("filters"),
                max_results=self.config.max_results_per_agent,
            )

            agents_used = state.get("agents_used", [])
            if "drug_agent" not in agents_used:
                agents_used.append("drug_agent")

            return {
                "drug_results": results,
                "agents_used": agents_used,
                "current_step": "drug_search",
                "progress": 80,
            }

        except Exception as e:
            logger.error(f"Error in drug agent: {e}")
            return {
                "errors": state.get("errors", []) + [f"Drug agent failed: {str(e)}"],
                "drug_results": [],
            }

    async def _synthesize_node(self, state: AgentState) -> Dict[str, Any]:
        """Synthesize results from all agents."""
        from app.agents.synthesis_agent import synthesize_results

        logger.info("Synthesizing results...")

        try:
            # Get conversation history from messages
            conversation_history = []
            messages = state.get("messages", [])
            for msg in messages:
                # Handle both dict and LangChain message objects
                if isinstance(msg, dict):
                    role = msg.get("role")
                    content = msg.get("content", "")
                else:
                    # Skip non-dict messages (e.g., SystemMessage objects)
                    continue

                if role == "user":
                    conversation_history.append({
                        "query": content,
                        "response": ""
                    })
                elif role == "assistant" and conversation_history:
                    conversation_history[-1]["response"] = content

            synthesis = await synthesize_results(
                query=state["query"],
                research_results=state.get("research_results", []),
                clinical_results=state.get("clinical_results", []),
                drug_results=state.get("drug_results", []),
                use_escalation=self.config.use_escalation_model,
                conversation_history=conversation_history,
            )

            return {
                "final_response": synthesis.final_response,
                "citations": synthesis.citations,
                "confidence_score": synthesis.confidence_score,
                "current_step": "synthesis",
                "progress": 100,
            }

        except Exception as e:
            logger.error(f"Error in synthesis: {e}")
            return {
                "errors": state.get("errors", []) + [f"Synthesis failed: {str(e)}"],
                "final_response": "An error occurred while synthesizing results.",
                "confidence_score": 0.0,
            }

    def _route_after_analysis(
        self, state: AgentState
    ) -> Literal["research", "clinical", "drug", "all"]:
        """Route to appropriate agents based on query intent."""
        intent = state.get("intent", "general")

        if intent == "research":
            return "research"
        elif intent == "clinical_trial":
            return "clinical"
        elif intent == "drug_info":
            return "drug"
        else:
            # For general queries, use all agents
            return "all"

    def _route_after_research(
        self, state: AgentState
    ) -> Literal["clinical", "drug", "synthesize"]:
        """Route after research agent based on intent."""
        intent = state.get("intent", "general")

        if intent == "general":
            # Continue to clinical agent
            return "clinical"
        else:
            # Skip to synthesis
            return "synthesize"

    def _route_after_clinical(
        self, state: AgentState
    ) -> Literal["drug", "synthesize"]:
        """Route after clinical agent based on intent."""
        intent = state.get("intent", "general")

        if intent == "general":
            # Continue to drug agent
            return "drug"
        else:
            # Skip to synthesis
            return "synthesize"

    def compile(self) -> Any:
        """Compile the workflow graph."""
        return self.graph.compile(checkpointer=self.checkpointer)

    async def execute(
        self, query: str, search_id: str, user_id: str, filters: Dict[str, Any] = None, messages: List[Dict[str, str]] = None
    ) -> AgentState:
        """
        Execute the workflow for a search query.

        Args:
            query: User query
            search_id: Unique search identifier
            user_id: User identifier
            filters: Optional search filters
            messages: Conversation history

        Returns:
            Final agent state with results
        """
        # Initialize state
        initial_state: AgentState = {
            "query": query,
            "search_id": search_id,
            "user_id": user_id,
            "conversation_id": None,
            "filters": filters,
            "intent": None,
            "entities": None,
            "query_embedding": None,
            "research_results": None,
            "clinical_results": None,
            "drug_results": None,
            "final_response": None,
            "citations": None,
            "confidence_score": None,
            "agents_used": [],
            "errors": [],
            "current_step": None,
            "progress": 0,
            "messages": messages or [],
        }

        # Compile and execute workflow
        app = self.compile()

        # Execute with checkpointing
        config = {"configurable": {"thread_id": search_id}}

        final_state = initial_state
        async for state in app.astream(initial_state, config):
            # astream returns dict with node name as key, extract the actual state
            for node_name, node_state in state.items():
                final_state.update(node_state)
            logger.debug(f"Workflow state: {final_state}")

        return final_state


# Global workflow instance
_workflow: MedSearchWorkflow = None


def get_workflow() -> MedSearchWorkflow:
    """Get global workflow instance."""
    global _workflow
    if _workflow is None:
        _workflow = MedSearchWorkflow()
    return _workflow

