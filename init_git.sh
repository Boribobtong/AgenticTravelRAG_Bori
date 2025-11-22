#!/bin/bash

# AgenticTravelRAG Git 초기 설정 스크립트

# 1. 이미 Git이 초기화되어 있는지 확인
if [ -d ".git" ]; then
    echo "⚠️  이미 Git 저장소가 초기화되어 있습니다."
    read -p "재설정하시겠습니까? (y/n): " confirm
    if [ "$confirm" != "y" ]; then
        echo "취소되었습니다."
        exit 0
    fi
    rm -rf .git
    echo "기존 .git 디렉토리를 삭제했습니다."
fi

echo "🚀 AgenticTravelRAG 프로젝트 Git 초기화 중..."

# 2. 스크립트 파일 실행 권한 부여
echo "⚙️  스크립트 실행 권한 설정 중..."
find . -name "*.sh" -exec chmod +x {} \;

# 3. Git 초기화
git init
git branch -M main

# 4. 모든 파일 추가
git add .

# 5. 초기 커밋
git commit -m "feat: Initial project structure with core agents

- LangGraph workflow orchestration (v0.2.x)
- Multi-agent system powered by Google Gemini 2.5 (Flash/Pro)
- Hybrid RAG pipeline with ElasticSearch & Synthetic Metadata
- Multi-lingual Query Parser (Korean/English support)
- AppState management for multi-turn conversations
- External tool integration (Open-Meteo, SerpApi)
- Streamlit UI dashboard for interactive planning
- Project documentation and contribution guide"

echo "✅ Git 초기화 및 커밋 완료!"
echo ""

# 6. Remote 저장소 연결 안내
echo "📌 GitHub 저장소 연결 설정"
echo "연결할 GitHub 저장소 URL을 입력하세요 (엔터 입력 시 건너뜀):"
read -p "URL (예: https://github.com/b8goal/AgenticTravelRAG.git): " REPO_URL

if [ -n "$REPO_URL" ]; then
    git remote add origin "$REPO_URL"
    echo "✅ 원격 저장소가 연결되었습니다: origin -> $REPO_URL"
    
    echo ""
    echo "지금 푸시하시겠습니까? (y/n)"
    read -p "선택: " PUSH_CONFIRM
    if [ "$PUSH_CONFIRM" == "y" ]; then
        git push -u origin main
    else
        echo "나중에 다음 명령어로 푸시하세요:"
        echo "  git push -u origin main"
    fi
else
    echo "⚠️  원격 저장소 연결을 건너뛰었습니다."
    echo "나중에 다음 명령어로 연결하세요:"
    echo "  git remote add origin https://github.com/b8goal/AgenticTravelRAG.git"
    echo "  git push -u origin main"
fi

echo ""
echo "📌 develop 브랜치 생성 (선택사항):"
echo "  git checkout -b develop"
echo "  git push -u origin develop"