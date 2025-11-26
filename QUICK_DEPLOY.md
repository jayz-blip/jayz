# 빠른 배포 가이드

## 자동화 스크립트 사용 (권장)

### Windows (PowerShell)
```powershell
.\deploy_cloudflare.ps1
```

### Linux/Mac (Bash)
```bash
chmod +x deploy_cloudflare.sh
./deploy_cloudflare.sh
```

## 수동 배포 (5분 소요)

### 1단계: Cloudflare Dashboard 접속
👉 https://dash.cloudflare.com

### 2단계: 프로젝트 생성
1. 왼쪽 메뉴에서 **Pages** 클릭
2. **Create a project** 버튼 클릭
3. **Connect to Git** 선택

### 3단계: GitHub 저장소 연결
1. **GitHub** 선택
2. 저장소 `jayz-blip/jayz` 선택
3. **Begin setup** 클릭

### 4단계: 빌드 설정
다음과 같이 설정:
- **Project name**: `jayz-chatbot` (원하는 이름)
- **Production branch**: `main`
- **Framework preset**: `None` 또는 `Other`
- **Build command**: (비워두기)
- **Build output directory**: `templates`
- **Root directory**: `/` (기본값)

### 5단계: 환경 변수 설정
1. **Environment variables** 섹션 클릭
2. **Add variable** 클릭
3. 다음 추가:
   - **Name**: `OPENAI_API_KEY`
   - **Value**: (OpenAI API 키 입력)
   - **Environment**: Production 및 Preview 모두 선택

### 6단계: 배포
1. **Save and Deploy** 클릭
2. 배포 완료 대기 (약 2-3분)

### 7단계: 배포 확인
배포가 완료되면 자동으로 URL이 생성됩니다:
- 예: `https://jayz-chatbot.pages.dev`

## 문제 해결

### 배포 실패 시
1. **Build logs** 확인
2. JSON 파일이 `public/data/`에 있는지 확인
3. 환경 변수 `OPENAI_API_KEY`가 설정되었는지 확인

### JSON 데이터 업데이트
CSV 파일을 수정한 경우:
```bash
python convert_csv_to_json.py
git add public/data/*.json
git commit -m "Update JSON data"
git push origin main
```
Cloudflare Pages가 자동으로 재배포합니다.

