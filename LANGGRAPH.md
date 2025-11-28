
### 1\. 에이전트 실행 워크플로우 (LangGraph)

이 프로젝트의 핵심인 `src/core/workflow.py`에 정의된 에이전트 간의 실행 흐름입니다. 사용자의 요청이 처리되는 순서를 보여줍니다.

```mermaid
graph TD
    %% 노드 정의
    Start([User Input]) --> QueryParser
    
    subgraph "Core Agent Flow"
        QueryParser[Query Parser Agent<br/>(Gemini Flash)]
        HotelRAG[Hotel RAG Agent<br/>(ElasticSearch + A/B Test)]
        Weather[Weather Tool Agent<br/>(Open-Meteo)]
        GoogleSearch[Google Search Agent<br/>(SerpApi)]
        ResponseGen[Response Generator<br/>(Gemini Pro)]
        Feedback[Feedback Handler]
    end

    %% 흐름 연결
    QueryParser -- "목적지 있음" --> HotelRAG
    QueryParser -- "단순 대화/목적지 없음" --> Feedback
    
    HotelRAG --> Weather
    Weather --> GoogleSearch
    GoogleSearch --> ResponseGen
    
    ResponseGen -- "완료" --> End([Final Response])
    ResponseGen -- "피드백 필요" --> Feedback
    
    Feedback -- "재검색 요청" --> HotelRAG
    Feedback -- "쿼리 재수정" --> QueryParser
    Feedback -- "종료" --> End

    %% 스타일링
    style QueryParser fill:#e1f5fe,stroke:#01579b
    style HotelRAG fill:#fff9c4,stroke:#fbc02d
    style ResponseGen fill:#e8f5e9,stroke:#2e7d32
    style Feedback fill:#fce4ec,stroke:#880e4f
```

**흐름 설명:**

1.  **QueryParser**: 사용자의 자연어 입력을 JSON 형태(목적지, 날짜, 예산 등)로 변환합니다.
2.  **Routing**: 목적지가 파악되면 `HotelRAG`로, 그렇지 않으면 `FeedbackHandler`로 이동합니다.
3.  **HotelRAG**: ElasticSearch를 통해 호텔을 검색합니다. (Phase 4 기능인 A/B 테스팅이 여기서 적용되어 검색 알고리즘을 조정합니다.)
4.  **Enrichment (Weather -\> GoogleSearch)**: 검색된 호텔 정보를 바탕으로 날씨와 최신 가격 정보를 보강합니다.
5.  **ResponseGen**: 수집된 모든 정보를 종합하여 최종 여행 계획을 생성하고 사용자 만족도를 추적합니다.
6.  **Feedback**: 사용자가 "너무 비싸", "다른 곳 찾아줘" 등의 피드백을 주면 다시 검색 단계로 루프를 돕니다.

-----

### 2\. 전체 시스템 아키텍처 (System Architecture)

파일 구조(`FOLDER_STRUCTURE.md`)와 연동 방식(`docker-compose.yml`, `api/main.py`)을 기반으로 한 시스템 구성도입니다.

```mermaid
graph TB
    subgraph "Frontend Layer"
        CLI[CLI Client<br/>(scripts/run_agent.py)]
        Streamlit[Streamlit UI<br/>(src/ui/app.py)]
        Dashboard[Monitoring Dashboard<br/>(src/tools/monitoring_dashboard.py)]
    end

    subgraph "Backend API Layer"
        FastAPI[FastAPI Server<br/>(src/api/main.py)]
    end

    subgraph "Orchestration Layer (src/core)"
        LangGraph[LangGraph Workflow]
        StateManager[State Manager]
    end

    subgraph "Tools & Intelligence Layer"
        Gemini[Google Gemini API]
        Meteo[Open-Meteo API]
        Serp[SerpApi]
        
        subgraph "Production Tools (Phase 4)"
            ABTest[A/B Testing Manager]
            Tracker[Satisfaction Tracker]
            Metrics[Prometheus Collector]
            Retrain[Retraining Pipeline]
        end
    end

    subgraph "Data Layer"
        Elastic[(ElasticSearch<br/>Vector DB)]
        SQLite[(SQLite DBs<br/>Stats/Logs)]
        RawData[TripAdvisor Data]
    end

    %% 연결 관계
    CLI --> LangGraph
    Streamlit --> FastAPI
    Dashboard --> Metrics
    FastAPI --> LangGraph
    
    LangGraph --> Gemini
    LangGraph --> Meteo
    LangGraph --> Serp
    LangGraph --> Elastic
    
    LangGraph -.-> ABTest
    LangGraph -.-> Tracker
    LangGraph -.-> Metrics
    
    ABTest --> SQLite
    Tracker --> SQLite
    Retrain --> SQLite
```

**구성 요소 설명:**

  * **Frontend**: 사용자는 `Streamlit Web UI` 또는 터미널의 `CLI`를 통해 시스템에 접근합니다. 또한 별도의 모니터링 대시보드가 존재합니다.
  * **Backend**: `FastAPI`가 웹 요청을 받아 `LangGraph` 워크플로우를 실행합니다.
  * **Intelligence**: `Gemini`가 두뇌 역할을 하며, 외부 API(`Open-Meteo`, `SerpApi`)가 실시간 정보를 제공합니다.
  * **Production Tools (Phase 4)**: 최근 추가된 기능들로, A/B 테스트, 사용자 만족도 추적, 성능 메트릭 수집, 자동 재학습 파이프라인이 백그라운드에서 동작하며 `SQLite`에 데이터를 저장합니다.
  * **Data**: `ElasticSearch`가 핵심 호텔 데이터와 벡터 임베딩을 저장하고 검색합니다.
