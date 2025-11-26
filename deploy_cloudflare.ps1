# Cloudflare Pages 배포 자동화 스크립트
# PowerShell 스크립트

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Cloudflare Pages 배포 준비" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. CSV to JSON 변환
Write-Host "`n[1/3] CSV 데이터를 JSON으로 변환 중..." -ForegroundColor Yellow
python convert_csv_to_json.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "오류: CSV 변환 실패" -ForegroundColor Red
    exit 1
}

# 2. Git 상태 확인
Write-Host "`n[2/3] Git 상태 확인 중..." -ForegroundColor Yellow
git status

# 3. 변경사항 커밋 및 푸시
Write-Host "`n[3/3] 변경사항 커밋 및 푸시 중..." -ForegroundColor Yellow
$commitMessage = Read-Host "커밋 메시지 입력 (엔터 시 기본 메시지 사용)"
if ([string]::IsNullOrWhiteSpace($commitMessage)) {
    $commitMessage = "Update JSON data for Cloudflare Pages"
}

git add .
git commit -m $commitMessage
git push origin main

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "준비 완료!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`n다음 단계:" -ForegroundColor Cyan
Write-Host "1. https://dash.cloudflare.com 접속" -ForegroundColor White
Write-Host "2. Pages → Create a project" -ForegroundColor White
Write-Host "3. Connect to Git → jayz-blip/jayz 선택" -ForegroundColor White
Write-Host "4. 빌드 설정:" -ForegroundColor White
Write-Host "   - Framework preset: None" -ForegroundColor Gray
Write-Host "   - Build output directory: templates" -ForegroundColor Gray
Write-Host "5. 환경 변수 추가: OPENAI_API_KEY" -ForegroundColor White
Write-Host "6. Save and Deploy 클릭" -ForegroundColor White
Write-Host "`n배포가 완료되면 자동으로 URL이 생성됩니다!" -ForegroundColor Green

