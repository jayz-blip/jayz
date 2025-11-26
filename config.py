"""
설정 파일 - 환경 변수 관리
"""
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수에서 설정 읽기 (보안상 .env 파일 필수)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다. .env 파일을 확인하세요.")

BOARD_URL = os.getenv('BOARD_URL', 'https://ppm.malgn.co.kr/')
# CSV 기반으로 변경되어 더 이상 필요 없지만 하위 호환성을 위해 유지
BOARD_EMAIL = os.getenv('BOARD_EMAIL', '')
BOARD_PASSWORD = os.getenv('BOARD_PASSWORD', '')

# 고객사별 게시판 PID 매핑
CLIENT_BOARD_PIDS = {
    "블루타이거": 1459,
    "엔잡특공대": 1460,
    "스터디파이터": 1472,
    "에스티플리머스": 1966,
    # 추가 고객사는 여기에 추가 가능
}

# PID를 기반으로 게시판 URL 생성 함수
def get_board_url_by_pid(pid):
    """PID를 기반으로 게시판 URL 생성"""
    import base64
    # m 파라미터는 base64 인코딩된 "project{pid}-link" 형태
    m_param = base64.b64encode(f"project{pid}-link".encode()).decode()
    return f"https://ppm.malgn.co.kr/board/post_list.jsp?m={m_param}&pid={pid}"

# 고객사별 게시판 URL 매핑 (하위 호환성을 위해 유지)
CLIENT_BOARD_URLS = {
    client: get_board_url_by_pid(pid) 
    for client, pid in CLIENT_BOARD_PIDS.items()
}

