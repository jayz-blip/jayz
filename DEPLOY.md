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

## 5. CSV 데이터 변환

배포 전에 CSV 데이터를 JSON으로 변환해야 합니다:

```bash
python convert_csv_to_json.py
```

이 스크립트는:
- `20251125_PPM학습용데이터_원글.csv` → `public/data/posts.json`
- `20251125_PPM학습용데이터_댓글.csv` → `public/data/comments.json`
- 인덱스 데이터 → `public/data/indexed.json`

변환된 JSON 파일은 자동으로 배포에 포함됩니다.

## 6. 빌드 명령 (선택사항)

Cloudflare Pages 빌드 설정에서 빌드 명령을 추가할 수 있습니다:

- **Build command**: `python convert_csv_to_json.py` (Python이 설치된 경우)

또는 로컬에서 변환 후 커밋/푸시하세요.

