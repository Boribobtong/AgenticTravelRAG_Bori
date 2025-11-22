#!/bin/bash

# Create directory structure for ART project
echo "Creating ART project directory structure..."

# Main directories
mkdir -p src/{agents,tools,rag,core,api,ui}
mkdir -p data/{raw,processed,embeddings}
mkdir -p data/scripts
mkdir -p config
mkdir -p tests/{unit,integration,e2e}
mkdir -p docs/{api,guides,architecture}
mkdir -p docker/{elasticsearch,app}
mkdir -p notebooks
mkdir -p logs
mkdir -p .github/workflows

echo "Directory structure created successfully!"
echo "
ART-project/
├── src/
│   ├── agents/         # LangGraph agents (QueryParser, HotelRAG, Weather, GoogleSearch, ResponseGenerator)
│   ├── tools/          # External API tools (SerpApi, Open-Meteo)
│   ├── rag/            # ElasticSearch RAG pipeline
│   ├── core/           # Core logic (State management, Workflow definition)
│   ├── api/            # FastAPI endpoints
│   └── ui/             # Streamlit UI dashboard
├── data/
│   ├── raw/            # Raw datasets (TripAdvisor reviews)
│   ├── processed/      # Processed data
│   ├── embeddings/     # Vector embeddings
│   └── scripts/        # ETL scripts (Download, Indexing with synthetic metadata)
├── config/             # Configuration files (.env, config.yaml)
├── tests/              # Test suites (Unit, Integration, E2E)
├── docs/               # Documentation (API, Guides, Architecture)
├── docker/             # Docker configs (ElasticSearch, App)
├── notebooks/          # Jupyter notebooks for experiments
└── logs/               # Application logs
"