"""
Flask 웹 서버 - AI 챗봇 메인 애플리케이션
"""
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from board_crawler import BoardCrawler
from chatbot import ChatBot
import logging
import config

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 전역 변수
board_crawler = None
chatbot = None


def init_services():
    """서비스 초기화"""
    global board_crawler, chatbot
    
    # 설정에서 값 읽기
    board_url = config.BOARD_URL
    board_email = config.BOARD_EMAIL
    board_password = config.BOARD_PASSWORD
    api_key = config.OPENAI_API_KEY
    
    # 서비스 초기화
    board_crawler = BoardCrawler(board_url, board_email, board_password)
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
        
        # 고객사 이름 추출 및 게시판 URL 확인
        client_board_url = None
        client_name = None
        
        # 먼저 PID 매핑에서 고객사 확인 (우선순위)
        if hasattr(config, 'CLIENT_BOARD_PIDS') and config.CLIENT_BOARD_PIDS:
            for client, pid in config.CLIENT_BOARD_PIDS.items():
                if client in user_message:
                    client_name = client
                    client_board_url = config.get_board_url_by_pid(pid)
                    logger.info(f"고객사 감지 (PID 매핑): {client_name}, PID: {pid}, 게시판 URL: {client_board_url}")
                    break
        
        # PID 매핑에 없으면 기존 URL 매핑 확인 (하위 호환성)
        if not client_name and hasattr(config, 'CLIENT_BOARD_URLS') and config.CLIENT_BOARD_URLS:
            for client, url in config.CLIENT_BOARD_URLS.items():
                if client in user_message:
                    client_name = client
                    client_board_url = url
                    logger.info(f"고객사 감지 (URL 매핑): {client_name}, 게시판 URL: {client_board_url}")
                    break
        
        # config에 없으면 왼쪽 메뉴에서 동적으로 찾기
        if not client_name and board_crawler:
            try:
                # 모든 게시판 카테고리 가져오기
                logger.info("게시판 목록 동적 추출 시도 중...")
                all_boards = board_crawler.get_board_categories()
                
                if not all_boards or len(all_boards) == 0:
                    logger.warning("게시판 목록을 가져올 수 없습니다. config.CLIENT_BOARD_URLS에 수동으로 추가하거나, 왼쪽 메뉴 접근을 확인해주세요.")
                else:
                    logger.info(f"게시판 목록 {len(all_boards)}개 로드 완료")
                    
                    # 사용자 메시지에서 고객사 이름 찾기
                    for board_name, board_info in all_boards.items():
                        # 부분 매칭 (고객사 이름이 게시판 이름에 포함되거나 그 반대)
                        if board_name in user_message or any(word in board_name for word in user_message.split() if len(word) > 2):
                            client_name = board_name
                            client_board_url = board_info['url']
                            logger.info(f"고객사 감지 (동적 추출): {client_name}, 게시판 URL: {client_board_url}")
                            break
                    
                    # 정확한 매칭이 없으면 GPT로 추출 시도
                    if not client_name and all_boards:
                        try:
                            # 게시판 이름 목록 생성 (최대 50개만)
                            board_names = list(all_boards.keys())[:50]
                            client_list = ", ".join(board_names)
                            extraction_prompt = f"""다음 메시지에서 고객사 이름을 추출해주세요. 
가능한 고객사 목록: {client_list}
메시지: {user_message}
고객사 이름만 답변해주세요. 없으면 "없음"이라고 답변해주세요."""
                            
                            extracted_name = chatbot.get_response(extraction_prompt, "")
                            extracted_name = extracted_name.strip()
                            
                            # 추출된 이름이 게시판 목록에 있는지 확인
                            if extracted_name and extracted_name != "없음":
                                # 정확한 매칭
                                if extracted_name in all_boards:
                                    client_name = extracted_name
                                    client_board_url = all_boards[extracted_name]['url']
                                else:
                                    # 부분 매칭 시도
                                    for board_name in all_boards.keys():
                                        if extracted_name in board_name or board_name in extracted_name:
                                            client_name = board_name
                                            client_board_url = all_boards[board_name]['url']
                                            break
                            
                            if client_name:
                                logger.info(f"고객사 감지 (GPT 추출): {client_name}, 게시판 URL: {client_board_url}")
                        except Exception as e:
                            logger.warning(f"GPT로 고객사 이름 추출 실패: {str(e)}")
                        
            except Exception as e:
                logger.error(f"게시판 목록 동적 추출 실패: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
        
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
        if is_contact_query and board_crawler:
            try:
                # 고객사 이름이나 카테고리 이름 추출 시도
                categories = board_crawler.get_board_categories(board_url=client_board_url if client_board_url else None)
                
                # 사용자 메시지에서 카테고리 이름 찾기
                matched_category = None
                for cat_name in categories.keys():
                    if cat_name in user_message:
                        matched_category = cat_name
                        break
                
                # 카테고리 매칭되면 해당 카테고리의 담당자 정보 가져오기
                if matched_category:
                    category_url = categories[matched_category]['url']
                    responsible_person_info = board_crawler.get_recent_responsible_person(
                        category_name=matched_category,
                        category_url=category_url
                    )
                    logger.info(f"카테고리 '{matched_category}'의 담당자 정보: {responsible_person_info}")
            except Exception as e:
                logger.warning(f"담당자 정보 추출 실패: {str(e)}")
        
        # 게시판 정보 가져오기 (필요시)
        board_context = ""
        try:
            if board_crawler:
                # 특정 고객사 게시판이 감지된 경우 해당 게시판 사용
                if client_board_url:
                    board_context = board_crawler.get_all_posts_text(limit=30, board_url=client_board_url, date_filter=date_filter)
                else:
                    board_context = board_crawler.get_all_posts_text(limit=20, date_filter=date_filter)
                
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
    """게시판 정보 새로고침"""
    try:
        global board_crawler
        
        if board_crawler:
            board_crawler.close()
        
        # 재초기화
        board_url = config.BOARD_URL
        board_email = config.BOARD_EMAIL
        board_password = config.BOARD_PASSWORD
        
        board_crawler = BoardCrawler(board_url, board_email, board_password)
        success = board_crawler.login()
        
        if success:
            posts = board_crawler.get_posts(limit=20)
            return jsonify({
                'success': True,
                'message': f'{len(posts)}개의 게시글을 수집했습니다.',
                'posts_count': len(posts)
            })
        else:
            return jsonify({
                'success': False,
                'message': '게시판 로그인에 실패했습니다.'
            }), 500
            
    except Exception as e:
        logger.error(f"게시판 새로고침 오류: {str(e)}")
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

