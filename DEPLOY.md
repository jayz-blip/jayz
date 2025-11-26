# Cloudflare Pages 배포 가이드

## 1. Cloudflare Dashboard에서 프로젝트 생성

1. [Cloudflare Dashboard](https://dash.cloudflare.com)에 로그인
2. **Pages** 메뉴 클릭
3. **Create a project** 클릭
4. **Connect to Git** 선택
5. GitHub 저장소 `jayz-blip/jayz` 선택 및 연결

## 2. 빌드 설정

- **Framework preset**: None
- **Build command**: (비워두기)
- **Build output directory**: `templates`
- **Root directory**: `/` (기본값)

## 3. 환경 변수 설정

**Settings** → **Environment Variables**에서 다음 변수 추가:

- **Variable name**: `OPENAI_API_KEY`
- **Value**: OpenAI API 키
- **Environment**: Production (및 Preview)

## 4. 배포 확인

배포가 완료되면 자동으로 URL이 생성됩니다:
- 프로덕션: `https://jayz-cid.pages.dev` (또는 설정한 커스텀 도메인)

## 5. 기능 제한사항

⚠️ **중요**: Cloudflare Pages Functions는 파일 시스템에 직접 접근할 수 없으므로:
- CSV 파일 읽기 불가
- 현재는 기본 OpenAI 챗봇만 동작 (CSV 데이터 없이)
- CSV 데이터를 사용하려면 JSON으로 변환하여 Functions에 포함하거나, 다른 배포 플랫폼 사용 권장

## 6. CSV 데이터 포함 방법 (선택사항)

CSV 데이터를 사용하려면:
1. CSV를 JSON으로 변환
2. `functions/data.json`에 저장
3. Functions에서 JSON 파일 읽기

또는 Railway, Render 등 다른 플랫폼 사용을 권장합니다.

