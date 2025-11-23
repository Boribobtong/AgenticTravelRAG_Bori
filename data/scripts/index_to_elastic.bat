@echo off
REM ElasticSearch 인덱싱 스크립트 (Windows)
REM 다운로드한 데이터를 ElasticSearch에 인덱싱합니다.

echo 📊 ElasticSearch 인덱싱 시작...
echo ================================
echo ⚠️  주의: ElasticSearch가 실행 중이어야 합니다.
echo.

REM ElasticSearch 연결 확인
curl -s http://localhost:9200 >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ ElasticSearch가 실행되지 않았습니다.
    echo    다음 명령어로 실행하세요:
    echo    docker-compose -f docker/docker-compose.yml up -d elasticsearch
    exit /b 1
)

echo ✅ ElasticSearch 연결 확인 완료
echo.

REM Python 모듈로 실행
python -m data.scripts.index_to_elastic

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 인덱싱 완료!
    echo ================================
) else (
    echo.
    echo ❌ 인덱싱 실패. 오류를 확인하세요.
    exit /b 1
)
