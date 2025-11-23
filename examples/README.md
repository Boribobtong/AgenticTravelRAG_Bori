# 🌤️ Weather Agent Demo

Weather Agent의 기능을 테스트하고 검증하기 위한 데모 스크립트입니다.
실제 Open-Meteo API와 Google Gemini API를 연동하여 날씨 정보와 AI 조언을 생성합니다.

## 🚀 주요 기능

1.  **다양한 시나리오 테스트**:
    *   여러 도시(Paris, Tokyo, New York 등)와 날짜 범위에 대한 테스트를 지원합니다.
2.  **데이터 무결성 검증**:
    *   API 응답의 필수 필드, 값의 범위, 논리적 일관성(최저기온 < 최고기온 등)을 자동으로 검증합니다.
3.  **결과 저장**:
    *   테스트 결과를 JSON 파일로 저장하여 추후 분석이나 기록용으로 활용할 수 있습니다.
4.  **Mock vs Real 비교**:
    *   Mock 데이터와 실제 API 호출 결과를 비교하여 데이터의 풍부함과 구조적 차이를 확인할 수 있습니다.
5.  **진행 상황 표시**:
    *   `tqdm` 라이브러리를 사용하여 테스트 진행률을 시각적으로 보여줍니다.

## 💻 사용법

### 1. 기본 실행
기본 설정(Paris, 3일)으로 데모를 실행합니다.
```bash
python examples/weather_agent_demo.py
```

### 2. 특정 도시 및 기간 지정
원하는 도시와 예보 기간을 지정하여 실행합니다.
```bash
python examples/weather_agent_demo.py --location Seoul --days 7
```

### 3. 모든 시나리오 실행
사전에 정의된 모든 테스트 시나리오(Paris, Tokyo, New York)를 순차적으로 실행합니다.
```bash
python examples/weather_agent_demo.py --all-scenarios
```

### 4. 결과 저장 (`--save`)
실행 결과를 `examples/demo_results/` 디렉토리에 JSON 파일로 저장합니다.
```bash
python examples/weather_agent_demo.py --location London --days 5 --save
```

### 5. Mock vs Real 비교 (`--compare`)
Mock 데이터와 실제 API 호출 결과를 비교하여 차이점을 분석합니다.
```bash
python examples/weather_agent_demo.py --compare
```

## 📊 옵션 요약

| 옵션 | 설명 | 기본값 |
| :--- | :--- | :--- |
| `--location` | 조회할 도시 이름 | Paris |
| `--days` | 예보 기간 (일) | 3 |
| `--all-scenarios` | 정의된 모든 시나리오 실행 | False |
| `--save` | 결과를 JSON 파일로 저장 | False |
| `--compare` | Mock vs Real 데이터 비교 모드 실행 | False |

## 📁 결과 파일 예시

저장된 JSON 파일은 다음과 같은 구조를 가집니다:

```json
{
  "metadata": {
    "location": "Seoul",
    "query_time": "2025-11-23T21:23:13.123456",
    "forecast_count": 7
  },
  "forecasts": [
    {
      "date": "2025-11-24",
      "temperature": {
        "min": -2.5,
        "max": 5.8,
        "unit": "celsius"
      },
      "llm_advice": "1. 옷차림: 두꺼운 패딩..."
    }
  ]
}
```
