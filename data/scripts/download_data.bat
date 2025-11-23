@echo off
REM 데이터 다운로드 스크립트 (Windows)
REM TripAdvisor 리뷰 데이터를 HuggingFace에서 다운로드합니다.

echo 🔽 데이터 다운로드 시작...
echo ================================

REM Python 모듈로 실행
python -m data.scripts.download_data

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 데이터 다운로드 완료!
    echo ================================
) else (
    echo.
    echo ❌ 데이터 다운로드 실패. 오류를 확인하세요.
    exit /b 1
)
