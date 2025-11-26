"""
Flask 웹 서버 - AI 챗봇 메인 애플리케이션
CSV 데이터 기반으로 동작합니다.
"""
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from csv_loader import CSVDataLoader
from chatbot import ChatBot
import logging
import config
import os

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 전역 변수
csv_loader = None
chatbot = None


def init_services():
    """서비스 초기화"""
    global csv_loader, chatbot
    
    # 설정에서 값 읽기
    api_key = config.OPENAI_API_KEY
    
    # CSV 파일 경로 설정
    posts_csv = os.path.join(os.path.dirname(__file__), '20251125_PPM학습용데이터_원글.csv')
    comments_csv = os.path.join(os.path.dirname(__file__), '20251125_PPM학습용데이터_댓글.csv')
    
    # 서비스 초기화
    csv_loader = CSVDataLoader(posts_csv, comments_csv)
    chatbot = ChatBot(api_key)
    
    logger.info("서비스 초기화 완료")


@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """챗봇 API 엔드포인트"""
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': '메시지가 필요합니다.'}), 400
        
        # 고객사 이름 추출
        client_name = None
        
        # CSV에서 고객사 목록 가져오기
        if csv_loader:
            client_names = csv_loader.get_client_names()
            
            # 사용자 메시지에서 고객사 이름 찾기
            for name in client_names:
                if name in user_message or any(word in name for word in user_message.split() if len(word) > 2):
                    client_name = name
                    logger.info(f"고객사 감지: {client_name}")
                    break
            
            # 정확한 매칭이 없으면 GPT로 추출 시도
            if not client_name and client_names:
                try:
                    client_list = ", ".join(client_names[:50])  # 최대 50개만
                    extraction_prompt = f"""다음 메시지에서 고객사 이름을 추출해주세요. 
가능한 고객사 목록: {client_list}
메시지: {user_message}
고객사 이름만 답변해주세요. 없으면 "없음"이라고 답변해주세요."""
                    
                    extracted_name = chatbot.get_response(extraction_prompt, "")
                    extracted_name = extracted_name.strip()
                    
                    # 추출된 이름이 고객사 목록에 있는지 확인
                    if extracted_name and extracted_name != "없음":
                        for name in client_names:
                            if extracted_name in name or name in extracted_name:
                                client_name = name
                                break
                    
                    if client_name:
                        logger.info(f"고객사 감지 (GPT 추출): {client_name}")
                except Exception as e:
                    logger.warning(f"GPT로 고객사 이름 추출 실패: {str(e)}")
        
        # 날짜 필터 감지
        date_filter = None
        date_keywords = {
            '오늘': 'today',
            '어제': 'yesterday',
            '이번 주': 'this_week',
            '이번주': 'this_week',
            '지난 주': 'last_week',
            '지난주': 'last_week',
            '이번 달': 'this_month',
            '이번달': 'this_month',
            '지난 달': 'last_month',
            '지난달': 'last_month',
            '최근': 'recent',
            '최근 일주일': 'recent',
            '최근 7일': 'recent',
        }
        
        for keyword, filter_value in date_keywords.items():
            if keyword in user_message:
                date_filter = filter_value
                logger.info(f"날짜 필터 감지: {keyword} -> {filter_value}")
                break
        
        # 문제/어려운 케이스 관련 질문인지 감지
        is_problem_query = any(keyword in user_message for keyword in [
            '문제', '어려움', '이슈', '오류', '에러', '장애', '트러블', '난제', 
            '복잡', '어려웠', '문제가', '이슈가', '오류가', '에러가'
        ])
        
        # 담당자 문의인지 감지
        is_contact_query = any(keyword in user_message for keyword in [
            '담당자', '문의', '연락', '누구', '누가', '어디', '어느', '담당', '접촉'
        ])
        
        # 담당자 정보 추출 (담당자 문의인 경우)
        responsible_person_info = None
        if is_contact_query and csv_loader and client_name:
            try:
                responsible_person_info = csv_loader.get_responsible_person(client_name)
                if responsible_person_info:
                    logger.info(f"고객사 '{client_name}'의 담당자 정보: {responsible_person_info}")
            except Exception as e:
                logger.warning(f"담당자 정보 추출 실패: {str(e)}")
        
        # CSV 데이터에서 게시판 정보 가져오기
        board_context = ""
        try:
            if csv_loader:
                board_context = csv_loader.get_posts_text(
                    limit=30, 
                    client_name=client_name, 
                    date_filter=date_filter
                )
                
                if not board_context:
                    logger.warning("게시판 정보가 비어있습니다.")
                elif date_filter:
                    logger.info(f"날짜 필터 적용됨: {date_filter}")
        except Exception as e:
            logger.warning(f"게시판 정보 수집 실패: {str(e)}")
        
        # 챗봇 응답 생성
        response = chatbot.get_response(
            user_message, 
            board_context, 
            is_problem_query=is_problem_query,
            responsible_person_info=responsible_person_info
        )
        
        return jsonify({
            'response': response,
            'success': True
        })
        
    except Exception as e:
        logger.error(f"챗봇 API 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/refresh-board', methods=['POST'])
def refresh_board():
    """CSV 데이터 새로고침"""
    try:
        global csv_loader
        
        # CSV 파일 경로 설정
        posts_csv = os.path.join(os.path.dirname(__file__), '20251125_PPM학습용데이터_원글.csv')
        comments_csv = os.path.join(os.path.dirname(__file__), '20251125_PPM학습용데이터_댓글.csv')
        
        # 재초기화
        csv_loader = CSVDataLoader(posts_csv, comments_csv)
        
        posts_count = len(csv_loader.posts_data) if csv_loader.posts_data else 0
        comments_count = len(csv_loader.comments_data) if csv_loader.comments_data else 0
        
        return jsonify({
            'success': True,
            'message': f'CSV 데이터를 새로고침했습니다. (원글: {posts_count}개, 댓글: {comments_count}개)',
            'posts_count': posts_count,
            'comments_count': comments_count
        })
            
    except Exception as e:
        logger.error(f"CSV 데이터 새로고침 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    """대화 기록 초기화"""
    try:
        chatbot.clear_history()
        return jsonify({'success': True, 'message': '대화 기록이 초기화되었습니다.'})
    except Exception as e:
        logger.error(f"대화 기록 초기화 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    init_services()
    app.run(debug=True, host='0.0.0.0', port=5000)

