# Backend Architecture MVP

## System Architecture
The backend is a Python-based intelligent pipeline designed to collect, parse, and analyze public conversations to identify B2B buying signals. It cleanly separates the background crawling/collection layer from the intelligence processing layer (LangGraph) and the API serving layer (FastAPI).

## Source Agent Architecture
To ensure maintainability, each data source is implemented as an independent "Source Agent":
- Each source (Indie Hackers, n8n Community, GitHub Discussions, Hacker News) has its own dedicated collection logic.
- Scraping logic (BeautifulSoup, feedparser, APIs) is strictly isolated to its respective agent.
- Every agent is responsible for translating its specific data format into a **common normalized signal schema** before passing it to the intelligence pipeline.

## LangGraph Architecture
LangGraph drives the intelligence pipeline by defining a state graph for processing normalized signals:
1. **Intake Node**: Receives the normalized signal.
2. **Relevance/Filter Node**: LLM determines if the conversation is a genuine buying signal.
3. **Extraction Node**: LLM extracts structured data (business pain, technology need, intent score, company info).
4. **Enrichment Node**: Integrates vector similarity search (pgvector) to match needs against specific service offerings.
5. **Output Node**: Saves the finalized intelligence object to PostgreSQL.

## Data Flow
1. **Collection**: Background workers trigger Source Agents.
2. **Normalization**: Source Agents scrape data and output normalized basic objects.
3. **Processing**: Normalized objects are pushed into the LangGraph pipeline.
4. **Storage**: Analyzed signals are committed to PostgreSQL.
5. **Delivery**: FastAPI application reads from PostgreSQL to serve the frontend API.

## API Layer
FastAPI provides the standard interface:
- Operates strictly as a consumer of the PostgreSQL database, isolated from the ingestion pipeline.
- Endpoints will serve paginated leads and aggregated analytics.

## Database Layer
- **PostgreSQL**: Primary data store for leads, sources, and analytics.
- **pgvector**: Used specifically for semantic matching of business pain to specific service offerings, avoiding over-engineering where exact match is sufficient.
- **SQLAlchemy + Alembic**: For ORM definitions and schema migrations.

## Redis Layer
- **Caching**: Storing API responses.
- **Job Coordination**: Storing queue states for future background scraping tasks, ensuring we do not overlap workers or hammer external sources.

## Future Extensibility
- Adding a new source simply requires creating a new Source Agent that outputs the normalized schema. The LangGraph pipeline and API remain completely untouched.
- Additional LangGraph nodes can be inserted seamlessly to enrich data without breaking the existing flow.
