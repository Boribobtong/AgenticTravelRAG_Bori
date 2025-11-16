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
│   ├── agents/         # LangGraph agents
│   ├── tools/          # External API tools  
│   ├── rag/            # RAG pipeline
│   ├── core/           # Core logic
│   ├── api/            # FastAPI endpoints
│   └── ui/             # Streamlit UI
├── data/
│   ├── raw/            # Raw datasets
│   ├── processed/      # Processed data
│   ├── embeddings/     # Vector embeddings
│   └── scripts/        # ETL scripts
├── config/             # Configuration files
├── tests/              # Test suites
├── docs/               # Documentation
├── docker/             # Docker configs
├── notebooks/          # Jupyter notebooks
└── logs/               # Application logs
"
