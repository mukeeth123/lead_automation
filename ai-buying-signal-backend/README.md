# AI Buying Signal Intelligence Platform - Backend

This is the MVP backend for the AI Buying Signal Intelligence Platform.

## Technology Stack
- **Framework**: FastAPI
- **Intelligence Orchestration**: LangGraph
- **Database**: PostgreSQL with pgvector (via SQLAlchemy & Alembic)
- **Cache/Queue**: Redis
- **Data Parsing**: BeautifulSoup, feedparser
- **LLM Integration**: OpenAI-compatible API

## Setup
1. Create a virtual environment: `python -m venv venv`
2. Activate it: `venv\Scripts\activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and fill in your keys.
5. Spin up services: `docker-compose up -d`
