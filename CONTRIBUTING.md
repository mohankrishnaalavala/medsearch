# Contributing to MedSearch AI

Thank you for your interest in contributing! This project was built for the AI Accelerate Hackathon and welcomes improvements and extensions.

## Ways to contribute
- Report bugs and suggest features via GitHub Issues
- Tackle an existing issue (look for good first issue / help wanted labels)
- Improve documentation and examples
- Optimize performance or developer experience

## Development setup
- Backend: Python 3.11+, FastAPI
- Frontend: Next.js 15, TypeScript
- Services: Elasticsearch 8.x, Redis
- Containerization: Docker Compose

Recommended steps:
1) Fork this repository and create a feature branch
2) Make changes locally and add tests when appropriate
3) Ensure quality checks pass (see below)
4) Open a Pull Request with a clear description of changes and rationale

## Quality checks
Run these before opening a PR:

Backend
```
cd backend
pytest
pytest --cov=app --cov-report=term-missing
ruff check app
mypy app
```

Frontend
```
cd frontend
npm ci
npm run lint
npm run type-check
npm run test
```

## Commit message convention
Use Conventional Commits:
- feat: add a new feature
- fix: bug fix
- docs: documentation only changes
- refactor: code change that neither fixes a bug nor adds a feature
- test: adding or correcting tests
- chore: tooling, CI, maintenance

Example: `feat(frontend): add streaming status indicator`

Note: Avoid proprietary or sensitive terms in commit messages.

## Pull request checklist
- [ ] Clear title using Conventional Commits
- [ ] Description explains what and why
- [ ] Includes tests for core logic (when applicable)
- [ ] All checks pass (lint, type-check, tests)
- [ ] No secrets committed

## Security and privacy
- Do not include real PHI or sensitive medical data in issues or PRs
- Redact API keys and credentials
- Prefer synthetic or public datasets for examples

## Code of Conduct
Be respectful and inclusive. Disagreements are fine; disrespect is not. Maintain a professional tone and help others succeed.

## License
By contributing, you agree that your contributions will be licensed under the MIT License of this repository.

