# 배포 가이드

## Cloudflare Pages 배포

현재 애플리케이션은 Selenium을 사용하므로 Cloudflare Pages/Workers에서 직접 실행할 수 없습니다.

### 옵션 1: 정적 파일만 배포 (제한적)

1. Cloudflare Pages에 저장소 연결
2. 빌드 설정:
   - 프레임워크: None
   - 빌드 명령: (비워두기)
   - 출력 디렉토리: `templates`

### 옵션 2: 다른 플랫폼 사용 (권장)

#### Railway 배포
1. [Railway](https://railway.app)에 가입
2. GitHub 저장소 연결
3. 새 프로젝트 생성 → GitHub 저장소 선택
4. 환경 변수 설정:
   - `OPENAI_API_KEY`
   - `BOARD_EMAIL`
   - `BOARD_PASSWORD`
   - `BOARD_URL` (선택사항)
5. 배포 자동 시작

#### Render 배포
1. [Render](https://render.com)에 가입
2. 새 Web Service 생성
3. GitHub 저장소 연결
4. 설정:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`
5. 환경 변수 설정

#### Fly.io 배포
1. [Fly.io](https://fly.io) CLI 설치
2. `fly launch` 실행
3. 환경 변수 설정: `fly secrets set OPENAI_API_KEY=...`

### Cloudflare Pages Functions 설정

현재 `functions/` 디렉토리에 기본 Functions가 설정되어 있지만, Selenium 기능은 사용할 수 없습니다.

**중요**: Cloudflare Pages에서 환경 변수 설정:
1. Cloudflare Dashboard → Pages → 프로젝트 선택
2. Settings → Environment Variables
3. `OPENAI_API_KEY` 추가

