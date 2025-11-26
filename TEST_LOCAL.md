# 로컬 테스트 가이드

## 1. 환경 변수 설정

`.env` 파일을 생성하고 OpenAI API 키를 추가하세요:

```bash
# .env 파일 생성
OPENAI_API_KEY=your_openai_api_key_here
```

`.env.example` 파일을 참고하세요.

## 2. 의존성 설치

```bash
pip install -r requirements.txt
```

## 3. CSV 데이터 확인

다음 CSV 파일이 프로젝트 루트에 있는지 확인:
- `20251125_PPM학습용데이터_원글.csv`
- `20251125_PPM학습용데이터_댓글.csv`

## 4. 앱 실행

```bash
python app.py
```

## 5. 브라우저에서 접속

서버가 시작되면 다음 URL로 접속:
- http://localhost:5000
- 또는 http://127.0.0.1:5000

## 테스트 예시 질문

1. "대한손해사정법인협회 관련 질문이 있어요"
2. "오늘 등록된 게시글 알려줘"
3. "블루타이거 담당자 누구야?"
4. "최근 문제 케이스 알려줘"

## 문제 해결

### 포트가 이미 사용 중인 경우
```bash
# 포트 5000을 사용하는 프로세스 종료
netstat -ano | findstr :5000
taskkill /PID [프로세스ID] /F
```

### CSV 파일을 찾을 수 없다는 오류
- CSV 파일이 프로젝트 루트에 있는지 확인
- 파일 이름이 정확한지 확인

### OpenAI API 오류
- `.env` 파일에 올바른 API 키가 있는지 확인
- API 키에 충분한 크레딧이 있는지 확인

