#!/bin/bash
# Cloudflare Pages 배포 자동화 스크립트
# Bash 스크립트 (Linux/Mac)

echo "========================================"
echo "Cloudflare Pages 배포 준비"
echo "========================================"

# 1. CSV to JSON 변환
echo ""
echo "[1/3] CSV 데이터를 JSON으로 변환 중..."
python convert_csv_to_json.py
if [ $? -ne 0 ]; then
    echo "오류: CSV 변환 실패"
    exit 1
fi

# 2. Git 상태 확인
echo ""
echo "[2/3] Git 상태 확인 중..."
git status

# 3. 변경사항 커밋 및 푸시
echo ""
echo "[3/3] 변경사항 커밋 및 푸시 중..."
read -p "커밋 메시지 입력 (엔터 시 기본 메시지 사용): " commit_message
if [ -z "$commit_message" ]; then
    commit_message="Update JSON data for Cloudflare Pages"
fi

git add .
git commit -m "$commit_message"
git push origin main

echo ""
echo "========================================"
echo "준비 완료!"
echo "========================================"
echo ""
echo "다음 단계:"
echo "1. https://dash.cloudflare.com 접속"
echo "2. Pages → Create a project"
echo "3. Connect to Git → jayz-blip/jayz 선택"
echo "4. 빌드 설정:"
echo "   - Framework preset: None"
echo "   - Build output directory: templates"
echo "5. 환경 변수 추가: OPENAI_API_KEY"
echo "6. Save and Deploy 클릭"
echo ""
echo "배포가 완료되면 자동으로 URL이 생성됩니다!"

