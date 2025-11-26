@echo off
echo ========================================
echo AI 챗봇 로컬 테스트 시작
echo ========================================
echo.

REM .env 파일 확인
if not exist .env (
    echo [경고] .env 파일이 없습니다.
    echo .env 파일을 생성하고 OPENAI_API_KEY를 추가하세요.
    echo.
    echo 예시:
    echo OPENAI_API_KEY=your_api_key_here
    echo.
    pause
    exit /b 1
)

REM CSV 파일 확인
if not exist "20251125_PPM학습용데이터_원글.csv" (
    echo [오류] CSV 파일을 찾을 수 없습니다.
    echo 20251125_PPM학습용데이터_원글.csv 파일이 필요합니다.
    pause
    exit /b 1
)

if not exist "20251125_PPM학습용데이터_댓글.csv" (
    echo [오류] CSV 파일을 찾을 수 없습니다.
    echo 20251125_PPM학습용데이터_댓글.csv 파일이 필요합니다.
    pause
    exit /b 1
)

echo [1/3] 의존성 확인 중...
python -c "import flask" 2>nul
if errorlevel 1 (
    echo Flask가 설치되지 않았습니다. 설치 중...
    pip install -r requirements.txt
)

echo [2/3] 서버 시작 중...
echo.
echo ========================================
echo 서버가 시작되었습니다!
echo 브라우저에서 다음 URL로 접속하세요:
echo http://localhost:5000
echo ========================================
echo.
echo 종료하려면 Ctrl+C를 누르세요.
echo.

python app.py

pause

