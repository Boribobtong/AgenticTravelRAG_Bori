# PR: verification/phase2-workflow-fixes

브랜치: verification/phase2-workflow-fixes

작성자: 자동 생성 (Assistant)
날짜: 2025-11-27

## 요약

이 PR은 Phase2 초기 PoC와 워크플로우 안정화(통합 테스트 그린)를 목표로 합니다. 핵심은 다음과 같습니다:

- 경량 Re-ranker PoC 추가 (토큰 오버랩 기반)
- 선택적 Cross-Encoder 재정렬기 추가(옵션, 환경변수로 활성화; heavy ML deps는 `requirements-ml.txt`로 분리)
- `ElasticSearchRAG.rerank_results`에 재정렬기 와이어링 및 안전한 폴백 구현
- `HotelRAGAgent.search`가 `ConversationMemory`를 읽어 사용자 선호를 병합하고 검색 요약을 메모리에 기록하도록 통합적 수정
- 워크플로우(`src/core/workflow.py`)의 피드백 라우팅 로직 수정: 피드백 → `feedback_handler` → `retry_search` 경로가 정상 동작하도록 조정
- 관련 단위 테스트 및 verification tests 추가/수정 (로컬에서 verification + 해당 통합 테스트 녹색)

## 변경된 파일 (핵심)

- src/rag/re_ranker.py — 경량 token-overlap re-ranker PoC
- src/rag/cross_reranker.py — 선택적 cross-encoder 로더(지연 로드, 실패 시 None 반환)
- src/rag/elasticsearch_rag.py — rerank hook에 cross/lexical re-ranker 와이어링
- src/agents/hotel_rag.py — ConversationMemory 병합(선호) 및 검색 기록 저장
- src/core/workflow.py — parse/feedback 라우팅 호환성 및 routing fixes
- src/core/state.py — `ConversationMemory` 모델 추가
- requirements-ml.txt — 선택적 ML 의존성
- tests/verification/test_re_ranker.py — re-ranker 단위 테스트
- tests/verification/test_adaptive_alpha.py — adaptive_alpha 단위 테스트

> 전체 커밋 로그는 브랜치에 여러 개의 세분화된 커밋으로 포함되어 있습니다(파일별 커밋 원칙 준수).

## 주요 커밋 (대표)

```
feat(reranker): add lightweight token-overlap re-ranker PoC (simple_rerank)
feat(reranker): add optional cross-encoder reranker (lazy load, opt-in via USE_CROSS_ENCODER)
fix(rag): wire optional cross-encoder and fallback to simple_rerank in rerank_results
feat(hotel): integrate ConversationMemory into HotelRAG.search (merge prefs + record search)
chore(deps): add requirements-ml.txt for optional ML deps (cross-encoder)
test(reranker): add unit test for simple_rerank lexical preference
test(rag): add unit tests for adaptive_alpha logic (semantic vs keyword)
feat(state): add ConversationMemory model and include in initial AppState
fix(workflow): ensure feedback routing and parse compatibility; log execution path consistently
```

## 테스트

- 로컬 단위(verification) 테스트: `PYTHONPATH=. pytest -q tests/verification` → 통과
- 관련 통합 테스트: `PYTHONPATH=. pytest -q tests/integration/test_workflow.py` → 통과

CI에서는 heavy ML 의존성을 기본으로 설치하지 않도록 유지하고 있습니다. Cross-Encoder를 실험하려면 `requirements-ml.txt`를 별도 환경에 설치하고 환경변수로 활성화하세요:

```bash
python -m venv .venv-ml
source .venv-ml/bin/activate
pip install -r requirements-ml.txt
export USE_CROSS_ENCODER=1
export CROSS_ENCODER_MODEL="cross-encoder/ms-marco-MiniLM-L-6-v2"
```

## 보안/운영 관련

- 민감키(.pem/.key) 관련: `.gitignore` 정책 및 CI 초반 검사(트랙된 키 감지 시 실패) 적용 권장(이미 일부 보호 조치 추가됨).

## 리뷰 포인트 (우선순위)

1. 피드백 라우팅 로직: `tests/integration/test_workflow.py`에 묘사된 시나리오가 기대대로 동작하는지 확인해 주세요.
2. ConversationMemory의 병합/기록 정책(간단 병합 → 점진 개선 권장).
3. Re-ranker PoC의 동작(기본은 경량 re-ranker; Cross-Encoder는 opt-in).

## 다음 단계

1. CI에서 PR 실행: GitHub Actions가 green인지 확인하고 실패 로그가 있으면 공유해 주세요.
2. Re-ranker 성능 정량화 및 re-ranker 개선(간단 교차 인코더 PoC 추가, A/B 테스트 설계).
3. 추가 통합 테스트(피드백 경로 다양화) 및 문서 보강.

---

### 체크리스트

- [x] 파일별로 개별 커밋으로 변경 반영
- [x] verification unit tests (로컬) 통과
- [x] 핵심 워크플로우 통합 테스트 (test_workflow) 통과
- [ ] GitHub Actions에서 PR 빌드/테스트 통과

### 요청 리뷰어

@b8goal

---
파일이 생성되었으며 현재 브랜치 `verification/phase2-workflow-fixes`에 커밋되어 있습니다. 원하시면 제가 PR 타이틀/본문을 이용해 GitHub에 PR을 생성하는 절차(명령어 또는 자동화된 스크립트)를 안내해 드리겠습니다.
