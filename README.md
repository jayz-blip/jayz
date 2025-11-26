# 사내 업무 AI 챗봇

CSV 데이터를 기반으로 업무 관련 질문에 답변하는 AI 챗봇입니다.

## 설치 방법

```bash
pip install -r requirements.txt
```

## 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 추가하세요:

```
OPENAI_API_KEY=your_api_key_here
```

## CSV 데이터 파일

프로젝트 루트에 다음 CSV 파일이 필요합니다:
- `20251125_PPM학습용데이터_원글.csv` - 게시글 데이터
- `20251125_PPM학습용데이터_댓글.csv` - 댓글 데이터

## 실행 방법

```bash
python app.py
```

브라우저에서 `http://localhost:5000`으로 접속하세요.

## 기능

- CSV 파일에서 게시글 및 댓글 데이터 로드
- OpenAI GPT를 활용한 자연어 질의응답
- CSV 데이터를 컨텍스트로 활용한 정확한 답변
- 고객사별 필터링 및 날짜 필터링 지원
- 담당자 정보 조회 기능
