# 사내 업무 AI 챗봇

사내 게시판(ppm.malgn.co.kr)의 정보를 참조하여 업무 관련 질문에 답변하는 AI 챗봇입니다.

## 설치 방법

```bash
pip install -r requirements.txt
```

## 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 추가하세요:

```
OPENAI_API_KEY=your_api_key_here
BOARD_URL=https://ppm.malgn.co.kr/
BOARD_EMAIL=your_email@malgnsoft.com
BOARD_PASSWORD=your_password
```

## 실행 방법

```bash
python app.py
```

브라우저에서 `http://localhost:5000`으로 접속하세요.

## 기능

- 사내 게시판 로그인 및 게시글 수집
- OpenAI GPT를 활용한 자연어 질의응답
- 게시판 정보를 컨텍스트로 활용한 정확한 답변
