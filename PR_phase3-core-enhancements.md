# PR: feature/phase3-core-enhancements

브랜치: feature/phase3-core-enhancements

작성자: 자동 생성 (Assistant)
날짜: 2025-11-27

## 요약

Phase3는 생산 준비를 위한 핵심 확장(Phase2 PoC의 연장)입니다. 이 PR은 다음 PoC/스텁을 추가합니다:

- `PriceAggregator` PoC: `src/tools/price_aggregator.py` — Mock provider와 간단한 집계 로직
- `ClimateDB` PoC: `src/tools/climate_db.py` — 월별 평년 기후 샘플 및 `get_climate_info` API
- `ResponseGeneratorAgent.stream_response` 스텁: 점진적(3단계) 응답 스트리밍 PoC
- 관련 단위 테스트 추가: price aggregator, climate db, response streaming
- CI 고려사항 문서: `docs/CI_NOTES_PHASE3.md` (옵션 ML job, 자격증명 취급)

## 변경된 파일

- src/tools/price_aggregator.py
- src/tools/climate_db.py
- src/agents/response_generator.py (stream_response 추가 및 LLM optional)
- tests/verification/test_price_aggregator.py
- tests/verification/test_climate_db.py
- tests/verification/test_response_stream.py
- docs/CI_NOTES_PHASE3.md

## 테스트

- `pytest -q tests/verification` → 로컬 통과 (LLM 관련 의존성은 optional)

## CI 영향

- 기본 워크플로우를 변경하지 않고, optional ML/Cloud jobs를 별도로 운영하는 것을 권장합니다.

## 다음 단계

1. Re-run CI on this branch and fix any environment-related failures.
2. Implement a light integration test that exercises `PriceAggregator` with a mocked provider.
3. Add a `ci-ml-tests.yml` workflow to run ML-heavy tests on-demand.

---

체크리스트
- [x] 파일별로 커밋 수행
- [x] verification tests (로컬) 통과
- [ ] PR을 통한 CI 확인

피드백이나 수정 사항 있으면 알려주세요.
