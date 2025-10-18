"""Mock data service for development when Elasticsearch is unavailable."""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class MockDataService:
    """Provides sample medical data for development/demo purposes."""

    @staticmethod
    def get_pubmed_results(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Get mock PubMed results."""
        # Sample PubMed articles about common medical topics
        sample_articles = [
            {
                "_id": "pmid_38123456",
                "_score": 0.95,
                "pmid": "38123456",
                "title": "Metformin and Cardiovascular Outcomes in Type 2 Diabetes: A Meta-Analysis",
                "abstract": "Background: Metformin is the first-line treatment for type 2 diabetes mellitus. This meta-analysis evaluates its cardiovascular effects. Methods: We analyzed 25 randomized controlled trials involving 15,000 patients. Results: Metformin reduced cardiovascular events by 15% (HR 0.85, 95% CI 0.78-0.92, p<0.001). Conclusion: Metformin demonstrates significant cardiovascular benefits beyond glycemic control.",
                "authors": ["Smith JA", "Johnson MB", "Williams CD"],
                "journal": "New England Journal of Medicine",
                "publication_date": "2024-01-15",
                "doi": "10.1056/NEJMoa2024001",
                "mesh_terms": ["Diabetes Mellitus, Type 2", "Metformin", "Cardiovascular Diseases"],
                "keywords": ["metformin", "type 2 diabetes", "cardiovascular outcomes", "meta-analysis"],
            },
            {
                "_id": "pmid_38123457",
                "_score": 0.92,
                "pmid": "38123457",
                "title": "SGLT2 Inhibitors in Heart Failure: Current Evidence and Future Directions",
                "abstract": "Sodium-glucose cotransporter-2 (SGLT2) inhibitors have emerged as a breakthrough therapy for heart failure. This review summarizes evidence from major trials including DAPA-HF and EMPEROR-Reduced. SGLT2 inhibitors reduce hospitalizations by 30% and improve quality of life. Mechanisms include diuretic effects, metabolic benefits, and direct cardiac protection.",
                "authors": ["Brown KL", "Davis RM", "Anderson PJ"],
                "journal": "Circulation",
                "publication_date": "2023-11-20",
                "doi": "10.1161/CIRCULATIONAHA.123.067890",
                "mesh_terms": ["Heart Failure", "SGLT2 Inhibitors", "Dapagliflozin"],
                "keywords": ["SGLT2 inhibitors", "heart failure", "dapagliflozin", "empagliflozin"],
            },
            {
                "_id": "pmid_38123458",
                "_score": 0.88,
                "pmid": "38123458",
                "title": "GLP-1 Receptor Agonists for Weight Management in Obesity: Systematic Review",
                "abstract": "Objective: To evaluate the efficacy and safety of GLP-1 receptor agonists for weight management. Methods: Systematic review of 18 RCTs with 12,000 participants. Results: GLP-1 agonists achieved mean weight loss of 12.4% (95% CI 10.8-14.0%). Semaglutide 2.4mg showed superior efficacy with 15% weight reduction. Adverse events were mainly gastrointestinal and transient.",
                "authors": ["Martinez EF", "Thompson GH", "Lee IJ"],
                "journal": "The Lancet",
                "publication_date": "2023-09-10",
                "doi": "10.1016/S0140-6736(23)01234-5",
                "mesh_terms": ["Obesity", "GLP-1 Receptor Agonists", "Weight Loss"],
                "keywords": ["GLP-1", "semaglutide", "obesity", "weight loss"],
            },
            {
                "_id": "pmid_38123459",
                "_score": 0.85,
                "pmid": "38123459",
                "title": "Insulin Therapy Optimization in Elderly Patients with Type 2 Diabetes",
                "abstract": "Background: Elderly patients with type 2 diabetes require careful insulin management to avoid hypoglycemia. This study evaluated simplified insulin regimens. Methods: 500 patients aged >65 years were randomized to basal-only vs basal-bolus insulin. Results: Basal-only insulin achieved similar HbA1c reduction (1.2% vs 1.3%, p=0.45) with 60% fewer hypoglycemic events. Conclusion: Simplified regimens are safer and equally effective in elderly patients.",
                "authors": ["Wilson KL", "Garcia MN", "Chen OP"],
                "journal": "Diabetes Care",
                "publication_date": "2023-07-05",
                "doi": "10.2337/dc23-0456",
                "mesh_terms": ["Diabetes Mellitus, Type 2", "Insulin", "Aged", "Hypoglycemia"],
                "keywords": ["insulin therapy", "elderly", "type 2 diabetes", "hypoglycemia"],
            },
            {
                "_id": "pmid_38123460",
                "_score": 0.82,
                "pmid": "38123460",
                "title": "Continuous Glucose Monitoring in Type 1 Diabetes: Real-World Outcomes",
                "abstract": "Introduction: Continuous glucose monitoring (CGM) has transformed diabetes management. This real-world study assessed CGM impact on glycemic control and quality of life. Methods: 2,000 type 1 diabetes patients using CGM for 12 months. Results: HbA1c decreased from 8.2% to 7.1% (p<0.001). Time in range increased from 55% to 72%. Patient satisfaction scores improved significantly. Conclusion: CGM provides substantial clinical and quality-of-life benefits.",
                "authors": ["Taylor QR", "Rodriguez ST", "Kim UV"],
                "journal": "JAMA",
                "publication_date": "2023-05-18",
                "doi": "10.1001/jama.2023.5678",
                "mesh_terms": ["Diabetes Mellitus, Type 1", "Blood Glucose Self-Monitoring", "Continuous Glucose Monitoring"],
                "keywords": ["CGM", "continuous glucose monitoring", "type 1 diabetes", "glycemic control"],
            },
        ]

        # Filter based on query keywords (simple matching)
        query_lower = query.lower()
        filtered = []
        for article in sample_articles:
            # Check if any query terms appear in title, abstract, or keywords
            searchable_text = (
                article["title"].lower()
                + " "
                + article["abstract"].lower()
                + " "
                + " ".join(article["keywords"]).lower()
            )
            
            # Simple relevance: count matching words
            query_words = query_lower.split()
            matches = sum(1 for word in query_words if len(word) > 3 and word in searchable_text)
            
            if matches > 0 or len(filtered) < 2:  # Always return at least 2 results
                article["_score"] = 0.9 - (len(filtered) * 0.05)  # Decreasing scores
                filtered.append(article)

        return filtered[:max_results]

    @staticmethod
    def get_clinical_trial_results(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Get mock clinical trial results."""
        sample_trials = [
            {
                "_id": "nct_05123456",
                "_score": 0.93,
                "nct_id": "NCT05123456",
                "title": "Efficacy of Semaglutide in Type 2 Diabetes with Cardiovascular Disease",
                "brief_summary": "This phase 3 trial evaluates semaglutide 1.0mg weekly vs placebo in patients with type 2 diabetes and established cardiovascular disease.",
                "detailed_description": "Primary endpoint: Time to first occurrence of major adverse cardiovascular event (MACE). Secondary endpoints include HbA1c reduction, weight loss, and safety. Estimated enrollment: 3,000 patients across 150 sites.",
                "conditions": ["Type 2 Diabetes Mellitus", "Cardiovascular Diseases"],
                "interventions": ["Semaglutide 1.0mg", "Placebo"],
                "phase": "Phase 3",
                "status": "Recruiting",
                "start_date": "2023-06-01",
                "completion_date": "2026-12-31",
                "locations": ["United States", "Canada", "Europe"],
                "sponsors": ["Novo Nordisk"],
            },
            {
                "_id": "nct_05123457",
                "_score": 0.90,
                "nct_id": "NCT05123457",
                "title": "Dapagliflozin in Heart Failure with Preserved Ejection Fraction (DELIVER)",
                "brief_summary": "Randomized trial of dapagliflozin 10mg daily vs placebo in heart failure with preserved ejection fraction (HFpEF).",
                "detailed_description": "Primary outcome: Composite of cardiovascular death or worsening heart failure. The trial aims to determine if SGLT2 inhibition benefits HFpEF patients, a population with limited treatment options.",
                "conditions": ["Heart Failure", "Heart Failure with Preserved Ejection Fraction"],
                "interventions": ["Dapagliflozin 10mg", "Placebo"],
                "phase": "Phase 3",
                "status": "Completed",
                "start_date": "2021-08-15",
                "completion_date": "2023-03-30",
                "locations": ["United States", "Europe", "Asia"],
                "sponsors": ["AstraZeneca"],
            },
            {
                "_id": "nct_05123458",
                "_score": 0.87,
                "nct_id": "NCT05123458",
                "title": "Tirzepatide for Weight Management in Obesity (SURMOUNT-1)",
                "brief_summary": "Phase 3 study of tirzepatide (5mg, 10mg, 15mg) vs placebo for chronic weight management in adults with obesity.",
                "detailed_description": "Primary endpoint: Percent change in body weight from baseline to week 72. Secondary endpoints include achievement of ≥5%, ≥10%, ≥15% weight loss, and cardiometabolic risk factors.",
                "conditions": ["Obesity", "Overweight"],
                "interventions": ["Tirzepatide 5mg", "Tirzepatide 10mg", "Tirzepatide 15mg", "Placebo"],
                "phase": "Phase 3",
                "status": "Completed",
                "start_date": "2020-12-01",
                "completion_date": "2022-10-15",
                "locations": ["United States", "Canada", "Mexico"],
                "sponsors": ["Eli Lilly and Company"],
            },
            {
                "_id": "nct_05123459",
                "_score": 0.84,
                "nct_id": "NCT05123459",
                "title": "Continuous Glucose Monitoring in Type 1 Diabetes (DIAMOND)",
                "brief_summary": "Randomized controlled trial comparing continuous glucose monitoring (CGM) to standard blood glucose monitoring in adults with type 1 diabetes.",
                "detailed_description": "Primary outcome: Change in HbA1c at 24 weeks. Secondary outcomes include time in range (70-180 mg/dL), hypoglycemia frequency, and quality of life measures.",
                "conditions": ["Diabetes Mellitus, Type 1"],
                "interventions": ["Continuous Glucose Monitoring", "Standard Blood Glucose Monitoring"],
                "phase": "Phase 4",
                "status": "Completed",
                "start_date": "2019-03-01",
                "completion_date": "2020-09-30",
                "locations": ["United States"],
                "sponsors": ["Dexcom, Inc."],
            },
            {
                "_id": "nct_05123460",
                "_score": 0.81,
                "nct_id": "NCT05123460",
                "title": "Insulin Degludec vs Insulin Glargine in Elderly Patients (SENIOR)",
                "brief_summary": "Comparison of insulin degludec vs insulin glargine U100 in patients aged ≥65 years with type 2 diabetes.",
                "detailed_description": "Primary endpoint: Rate of severe or blood glucose-confirmed symptomatic hypoglycemia. Secondary endpoints include HbA1c change, nocturnal hypoglycemia, and treatment satisfaction.",
                "conditions": ["Diabetes Mellitus, Type 2", "Hypoglycemia"],
                "interventions": ["Insulin Degludec", "Insulin Glargine U100"],
                "phase": "Phase 3",
                "status": "Completed",
                "start_date": "2018-06-15",
                "completion_date": "2020-12-20",
                "locations": ["United States", "Europe"],
                "sponsors": ["Novo Nordisk"],
            },
        ]

        # Simple filtering
        query_lower = query.lower()
        filtered = []
        for trial in sample_trials:
            searchable_text = (
                trial["title"].lower()
                + " "
                + trial["brief_summary"].lower()
                + " "
                + " ".join(trial["conditions"]).lower()
            )
            
            query_words = query_lower.split()
            matches = sum(1 for word in query_words if len(word) > 3 and word in searchable_text)
            
            if matches > 0 or len(filtered) < 2:
                trial["_score"] = 0.9 - (len(filtered) * 0.05)
                filtered.append(trial)

        return filtered[:max_results]

    @staticmethod
    def get_drug_results(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Get mock FDA drug results."""
        sample_drugs = [
            {
                "_id": "drug_metformin",
                "_score": 0.94,
                "drug_name": "Metformin",
                "generic_name": "metformin hydrochloride",
                "brand_names": ["Glucophage", "Fortamet", "Glumetza"],
                "application_number": "NDA020357",
                "manufacturer": "Multiple manufacturers",
                "approval_date": "1994-12-29",
                "indications": "Treatment of type 2 diabetes mellitus as an adjunct to diet and exercise to improve glycemic control in adults and pediatric patients 10 years of age and older.",
                "warnings": "Lactic acidosis: Rare but serious metabolic complication. Risk factors include renal impairment, concomitant use of certain drugs, age ≥65 years, radiological studies with contrast, surgery, and other procedures. Vitamin B12 deficiency: Long-term treatment may lead to vitamin B12 deficiency.",
                "adverse_reactions": "Most common adverse reactions (>5%): diarrhea, nausea/vomiting, flatulence, asthenia, indigestion, abdominal discomfort, and headache.",
                "drug_class": "Biguanide",
                "route": "Oral",
            },
            {
                "_id": "drug_semaglutide",
                "_score": 0.91,
                "drug_name": "Semaglutide",
                "generic_name": "semaglutide",
                "brand_names": ["Ozempic", "Wegovy", "Rybelsus"],
                "application_number": "NDA209637",
                "manufacturer": "Novo Nordisk",
                "approval_date": "2017-12-05",
                "indications": "Ozempic: Type 2 diabetes mellitus to improve glycemic control and reduce cardiovascular events. Wegovy: Chronic weight management in adults with obesity or overweight with weight-related comorbidities. Rybelsus: Type 2 diabetes mellitus (oral formulation).",
                "warnings": "Risk of thyroid C-cell tumors (boxed warning). Contraindicated in patients with personal or family history of medullary thyroid carcinoma or Multiple Endocrine Neoplasia syndrome type 2. Acute pancreatitis, diabetic retinopathy complications, hypoglycemia with concomitant insulin or sulfonylureas.",
                "adverse_reactions": "Most common (≥5%): nausea, vomiting, diarrhea, abdominal pain, constipation. Injection site reactions with subcutaneous formulations.",
                "drug_class": "GLP-1 Receptor Agonist",
                "route": "Subcutaneous injection, Oral",
            },
            {
                "_id": "drug_dapagliflozin",
                "_score": 0.88,
                "drug_name": "Dapagliflozin",
                "generic_name": "dapagliflozin propanediol",
                "brand_names": ["Farxiga"],
                "application_number": "NDA202293",
                "manufacturer": "AstraZeneca",
                "approval_date": "2014-01-08",
                "indications": "Type 2 diabetes mellitus to improve glycemic control. Heart failure with reduced ejection fraction. Chronic kidney disease. Reduce risk of cardiovascular death and hospitalization for heart failure in adults with heart failure.",
                "warnings": "Ketoacidosis: Reports in patients with type 1 and type 2 diabetes. Acute kidney injury and impairment in renal function. Hypotension. Genital mycotic infections. Hypersensitivity reactions. Necrotizing fasciitis of the perineum (Fournier's gangrene).",
                "adverse_reactions": "Most common (≥5%): female genital mycotic infections, nasopharyngitis, urinary tract infections, back pain, increased urination, male genital mycotic infections, nausea, influenza.",
                "drug_class": "SGLT2 Inhibitor",
                "route": "Oral",
            },
        ]

        # Simple filtering
        query_lower = query.lower()
        filtered = []
        for drug in sample_drugs:
            searchable_text = (
                drug["drug_name"].lower()
                + " "
                + drug["generic_name"].lower()
                + " "
                + " ".join(drug["brand_names"]).lower()
                + " "
                + drug["indications"].lower()
            )
            
            query_words = query_lower.split()
            matches = sum(1 for word in query_words if len(word) > 3 and word in searchable_text)
            
            if matches > 0 or len(filtered) < 1:
                drug["_score"] = 0.9 - (len(filtered) * 0.05)
                filtered.append(drug)

        return filtered[:max_results]


# Global instance
_mock_data_service: MockDataService | None = None


def get_mock_data_service() -> MockDataService:
    """Get global mock data service instance."""
    global _mock_data_service
    if _mock_data_service is None:
        _mock_data_service = MockDataService()
    return _mock_data_service

