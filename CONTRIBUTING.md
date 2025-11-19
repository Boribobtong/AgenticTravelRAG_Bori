# 🤝 AgenticTravelRAG 기여 가이드

## 목차
- [행동 규칙](#행동-규칙)
- [기여 방법](#기여-방법)
- [개발 환경 설정](#개발-환경-설정)
- [코드 스타일](#코드-스타일)
- [커밋 규칙](#커밋-규칙)
- [PR 프로세스](#pr-프로세스)
- [이슈 작성](#이슈-작성)

## 📜 행동 규칙

- 모든 참여자를 존중하고 포용적인 환경 유지
- 건설적인 피드백 제공
- 팀 목표와 프로젝트 비전 우선시

## 🚀 기여 방법

### 1. Fork & Clone
```bash
# Fork 후 클론
git clone https://github.com/YOUR_USERNAME/AgenticTravelRAG.git
cd AgenticTravelRAG

# Upstream 설정
git remote add upstream https://github.com/TEAM/AgenticTravelRAG.git
```

### 2. 브랜치 생성
```bash
# 최신 develop 브랜치에서 시작
git checkout develop
git pull upstream develop

# 기능 브랜치 생성
git checkout -b feature/your-feature-name
```

### 3. 개발 및 테스트
```bash
# 환경 설정
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 개발
# ... 코드 작성 ...

# 테스트 실행
pytest tests/
```

### 4. 커밋 & 푸시
```bash
# 변경사항 커밋
git add .
git commit -m "feat: Add hotel recommendation feature"

# 푸시
git push origin feature/your-feature-name
```

### 5. Pull Request 생성
GitHub에서 PR 생성 → develop 브랜치로

## 💻 개발 환경 설정

### 필수 도구
- Python 3.9+
- Docker & Docker Compose
- Git
- ElasticSearch 8.x

### 환경 변수
```bash
cp config/.env.example .env
# .env 파일 편집하여 API 키 설정
```

### ElasticSearch 설정
```bash
docker-compose -f docker/docker-compose.yml up -d elasticsearch
```

## 📝 코드 스타일

### Python 코드 규칙
- **PEP 8** 준수
- **Black** 포매터 사용
- **Type hints** 적극 활용

```python
# Good ✅
def search_hotels(
    query: str, 
    location: Optional[str] = None,
    min_rating: float = 3.5
) -> List[HotelOption]:
    """
    호텔 검색 함수
    
    Args:
        query: 검색 쿼리
        location: 위치 필터
        min_rating: 최소 평점
        
    Returns:
        HotelOption 리스트
    """
    pass
```

### Docstring 규칙
- Google 스타일 사용
- 모든 public 함수/클래스에 필수

### Import 순서
```python
# 1. 표준 라이브러리
import os
import sys

# 2. 서드파티 라이브러리
import numpy as np
import pandas as pd

# 3. 로컬 모듈
from src.core.state import AppState
from src.agents.hotel_rag import HotelRAGAgent
```

## 📌 커밋 규칙

### 커밋 메시지 형식
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type
- **feat**: 새로운 기능
- **fix**: 버그 수정
- **docs**: 문서 변경
- **style**: 코드 스타일 변경
- **refactor**: 리팩토링
- **test**: 테스트 추가/수정
- **chore**: 빌드/설정 변경

### 예시
```bash
feat(agents): Add weather forecast integration

- Integrate Open-Meteo API for weather data
- Add activity recommendations based on weather
- Cache weather data for 1 hour

Closes #123
```

## 🔄 PR 프로세스

### PR 템플릿
```markdown
## 📋 Description
변경사항에 대한 간단한 설명

## 🔗 Related Issue
Closes #(issue number)

## ✅ Checklist
- [ ] 코드가 프로젝트 스타일 가이드를 따름
- [ ] 셀프 리뷰 완료
- [ ] 테스트 추가/수정
- [ ] 문서 업데이트 (필요시)
- [ ] 모든 테스트 통과
- [ ] 커밋 메시지 규칙 준수

## 📸 Screenshots (if applicable)
UI 변경사항이 있는 경우 스크린샷 첨부

## 💬 Additional Notes
리뷰어에게 전달할 추가 정보
```

### 리뷰 프로세스
1. 최소 1명의 리뷰어 승인 필요
2. 모든 CI 체크 통과
3. 충돌 해결 완료
4. develop 브랜치로 머지

## 🐛 이슈 작성

### 버그 리포트
```markdown
## 🐛 Bug Description
버그에 대한 명확한 설명

## 📝 Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

## 🎯 Expected Behavior
예상했던 동작

## 📸 Screenshots
가능하면 스크린샷 첨부

## 🖥️ Environment
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.9.0]
- Browser: [e.g., Chrome 120]
```

### 기능 요청
```markdown
## 💡 Feature Description
제안하는 기능에 대한 설명

## 🎯 Use Case
이 기능이 필요한 사용 사례

## 📝 Proposed Solution
제안하는 구현 방법 (선택사항)

## 🔄 Alternatives
고려해본 대안들
```

## 🧪 테스트 가이드

### 단위 테스트
```bash
pytest tests/unit/
```

### 통합 테스트
```bash
pytest tests/integration/
```

### 테스트 커버리지
```bash
pytest --cov=src tests/
```

## 📚 문서화

### 코드 문서
- 모든 public API는 docstring 필수
- 복잡한 로직은 인라인 주석 추가

### 프로젝트 문서
- `/docs` 폴더에 Markdown 형식으로 작성
- 중요 변경사항은 README 업데이트

## 🏷️ 버전 관리

[Semantic Versioning](https://semver.org/) 사용:
- MAJOR.MINOR.PATCH (예: 1.2.3)
- MAJOR: 호환성 깨지는 변경
- MINOR: 기능 추가
- PATCH: 버그 수정

## 💬 커뮤니케이션

- **GitHub Issues**: 버그, 기능 요청
- **GitHub Discussions**: 일반적인 토론
- **Slack/Discord**: 실시간 소통 (팀 내부)

## 🙏 감사의 말

AgenticTravelRAG 프로젝트에 기여해 주셔서 감사합니다! 
여러분의 기여가 프로젝트를 더 나은 방향으로 발전시킵니다. 🚀
