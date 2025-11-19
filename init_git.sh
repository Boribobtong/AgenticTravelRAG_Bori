#!/bin/bash

# AgenticTravelRAG Git 초기 설정 스크립트
echo "🚀 AgenticTravelRAG 프로젝트 Git 초기화 중..."

# Git 초기화
git init

# 기본 브랜치를 main으로 설정
git branch -M main

# 모든 파일 추가
git add .

# 초기 커밋
git commit -m "feat: Initial project structure with core agents

- LangGraph workflow orchestration
- Multi-agent system (QueryParser, HotelRAG, Weather, GoogleSearch, ResponseGenerator)
- ElasticSearch RAG pipeline with TripAdvisor review data
- AppState management for multi-turn conversations
- External tool integration (Open-Meteo, SerpApi)
- Project documentation and contribution guide"

# Remote 추가 안내
echo ""
echo "✅ Git 초기화 완료!"
echo ""
echo "📌 다음 명령어로 GitHub 저장소를 연결하세요:"
echo ""
echo "git remote add origin https://github.com/YOUR_TEAM/AgenticTravelRAG.git"
echo "git push -u origin main"
echo ""
echo "📌 develop 브랜치 생성 (선택사항):"
echo "git checkout -b develop"
echo "git push -u origin develop"
