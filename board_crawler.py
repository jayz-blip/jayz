"""
사내 게시판 크롤러 모듈
로그인 후 게시글을 수집합니다.
"""
import time
import os
import re
from urllib.parse import urljoin
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BoardCrawler:
    def __init__(self, url, email, password):
        self.url = url
        self.email = email
        self.password = password
        self.driver = None
        self.session_data = None
        
    def _setup_driver(self):
        """Chrome 드라이버 설정"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 백그라운드 실행
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("Chrome 드라이버 설정 완료")
        
    def login(self):
        """사내 게시판에 로그인"""
        try:
            if not self.driver:
                self._setup_driver()
                
            logger.info(f"게시판 접속: {self.url}")
            self.driver.get(self.url)
            time.sleep(2)
            
            # 로그인 폼 찾기 및 입력
            try:
                logger.info(f"현재 URL: {self.driver.current_url}")
                logger.info(f"페이지 제목: {self.driver.title}")
                
                # 이메일 입력 필드 찾기 (name=id 우선)
                email_input = None
                selectors = [
                    (By.NAME, "id"),
                    (By.NAME, "email"),
                    (By.ID, "id"),
                    (By.ID, "email"),
                    (By.CSS_SELECTOR, "input[type='email']"),
                    (By.CSS_SELECTOR, "input[name*='email' i]"),
                    (By.CSS_SELECTOR, "input[id*='email' i]")
                ]
                
                for selector_type, selector_value in selectors:
                    try:
                        email_input = WebDriverWait(self.driver, 2).until(
                            EC.presence_of_element_located((selector_type, selector_value))
                        )
                        logger.info(f"이메일 필드 찾음: {selector_type}={selector_value}")
                        break
                    except:
                        continue
                
                if not email_input:
                    raise Exception("이메일 입력 필드를 찾을 수 없습니다.")
                
                email_input.clear()
                email_input.send_keys(self.email)
                logger.info("이메일 입력 완료")
                
                # 비밀번호 입력 필드 찾기 (name=passwd 우선)
                password_input = None
                password_selectors = [
                    (By.NAME, "passwd"),
                    (By.NAME, "password"),
                    (By.ID, "passwd"),
                    (By.ID, "password"),
                    (By.CSS_SELECTOR, "input[type='password']"),
                    (By.CSS_SELECTOR, "input[name*='password' i]")
                ]
                
                for selector_type, selector_value in password_selectors:
                    try:
                        password_input = self.driver.find_element(selector_type, selector_value)
                        logger.info(f"비밀번호 필드 찾음: {selector_type}={selector_value}")
                        break
                    except:
                        continue
                
                if not password_input:
                    raise Exception("비밀번호 입력 필드를 찾을 수 없습니다.")
                
                password_input.clear()
                password_input.send_keys(self.password)
                logger.info("비밀번호 입력 완료")
                
                # 로그인 버튼 클릭 (input[type='submit'].btn 우선)
                login_button = None
                button_selectors = [
                    (By.CSS_SELECTOR, "input[type='submit'].btn"),
                    (By.CSS_SELECTOR, "input[type='submit']"),
                    (By.CSS_SELECTOR, "button[type='submit']"),
                    (By.XPATH, "//button[contains(text(), '로그인')]"),
                    (By.XPATH, "//button[contains(text(), 'Login')]"),
                    (By.CSS_SELECTOR, "button.btn-primary"),
                    (By.CSS_SELECTOR, "button.login")
                ]
                
                for selector_type, selector_value in button_selectors:
                    try:
                        login_button = self.driver.find_element(selector_type, selector_value)
                        logger.info(f"로그인 버튼 찾음: {selector_type}={selector_value}")
                        break
                    except:
                        continue
                
                if not login_button:
                    raise Exception("로그인 버튼을 찾을 수 없습니다.")
                
                # StaleElementReferenceException 처리
                from selenium.webdriver.common.keys import Keys
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        login_button.click()
                        logger.info("로그인 버튼 클릭")
                        break
                    except Exception as e:
                        if "stale" in str(e).lower() and attempt < max_retries - 1:
                            logger.warning(f"StaleElementReferenceException 발생, 재시도 {attempt + 1}/{max_retries}")
                            try:
                                login_button = self.driver.find_element(selector_type, selector_value)
                                continue
                            except:
                                # Enter 키로 대체 시도
                                password_input.send_keys(Keys.RETURN)
                                logger.info("Enter 키로 로그인 시도")
                                break
                        else:
                            raise
                
                time.sleep(5)  # 로그인 처리 대기 시간 증가
                
                logger.info(f"로그인 후 URL: {self.driver.current_url}")
                
                # 로그인 성공 확인
                if "login" not in self.driver.current_url.lower() or "post_list" in self.driver.current_url.lower():
                    logger.info("로그인 성공으로 판단")
                    return True
                else:
                    logger.warning("로그인 실패 가능성")
                    return False
                    
            except Exception as e:
                logger.error(f"로그인 폼 처리 중 오류: {str(e)}")
                # 페이지 소스 확인을 위해 저장
                with open("debug_page.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                logger.info("디버그용 페이지 소스 저장: debug_page.html")
                return False
                
        except Exception as e:
            logger.error(f"로그인 중 오류 발생: {str(e)}")
            return False
    
    def navigate_to_board(self, board_url):
        """특정 게시판으로 이동"""
        try:
            if not self.driver:
                if not self.login():
                    return False
            
            logger.info(f"게시판으로 이동: {board_url}")
            self.driver.get(board_url)
            time.sleep(3)  # 페이지 로딩 대기
            return True
        except Exception as e:
            logger.error(f"게시판 이동 중 오류: {str(e)}")
            return False
    
    def get_board_categories(self, board_url=None, use_cache=True):
        """왼쪽 메뉴에서 게시판 카테고리 정보 추출 (모든 고객사 게시판 포함)"""
        # 캐시 사용 (성능 최적화)
        if use_cache and hasattr(self, '_board_categories_cache'):
            logger.info(f"캐시된 게시판 목록 사용: {len(self._board_categories_cache)}개")
            return self._board_categories_cache
        
        try:
            if not self.driver:
                if not self.login():
                    logger.error("로그인 실패로 게시판 목록을 가져올 수 없습니다.")
                    return {}
            
            # 메인 페이지로 이동 (왼쪽 메뉴는 메인 페이지에 있음)
            logger.info("게시판 목록 추출을 위해 메인 페이지로 이동 중...")
            self.driver.get(self.url)
            time.sleep(3)  # 페이지 로딩 대기 시간 증가
            
            # 현재 URL 확인
            current_url = self.driver.current_url
            logger.info(f"현재 URL: {current_url}")
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 왼쪽 메뉴 찾기: <div id="gs-left">
            left_menu = soup.find('div', id='gs-left')
            if not left_menu:
                logger.warning("왼쪽 메뉴(<div id='gs-left'>)를 찾을 수 없습니다.")
                # 디버그: 페이지 구조 확인
                all_divs = soup.find_all('div', id=True)
                logger.info(f"페이지에 있는 id 속성을 가진 div 개수: {len(all_divs)}")
                if len(all_divs) > 0:
                    sample_ids = [div.get('id') for div in all_divs[:10]]
                    logger.info(f"샘플 div id: {sample_ids}")
                
                # 대체 방법: 전체 페이지에서 post_list 링크 찾기
                logger.info("대체 방법: 전체 페이지에서 게시판 링크 찾기 시도...")
                all_post_links = soup.find_all('a', href=lambda x: x and 'post_list' in x)
                logger.info(f"전체 페이지에서 post_list 링크 {len(all_post_links)}개 발견")
                
                if len(all_post_links) == 0:
                    # 디버그용 HTML 저장
                    debug_file = "debug_main_page.html"
                    with open(debug_file, "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                    logger.error(f"게시판 링크를 찾을 수 없습니다. 디버그 파일 저장: {debug_file}")
                    return {}
                
                # 전체 페이지에서 링크 추출
                categories = {}
                for link in all_post_links:
                    category_name = link.get_text(strip=True)
                    href = link.get('href', '')
                    
                    if category_name and len(category_name.strip()) > 0 and href:
                        if href.startswith('http'):
                            category_url = href
                        elif href.startswith('/'):
                            category_url = urljoin(self.driver.current_url, href)
                        else:
                            category_url = urljoin(self.driver.current_url, href)
                        
                        if category_name not in categories:
                            categories[category_name] = {
                                'url': category_url,
                                'name': category_name
                            }
                
                if len(categories) > 0:
                    logger.info(f"대체 방법으로 게시판 {len(categories)}개 발견")
                    self._board_categories_cache = categories
                    return categories
                
                return {}
            
            categories = {}
            
            # 왼쪽 메뉴에서 모든 링크 찾기
            category_links = left_menu.find_all('a', href=lambda x: x and 'post_list' in x)
            logger.info(f"왼쪽 메뉴에서 post_list 링크 {len(category_links)}개 발견")
            
            for link in category_links:
                category_name = link.get_text(strip=True)
                href = link.get('href', '')
                
                # 빈 이름이나 의미 없는 텍스트 제외
                if not category_name or len(category_name.strip()) < 1:
                    continue
                
                if href:
                    # URL 완성
                    if href.startswith('http'):
                        category_url = href
                    elif href.startswith('/'):
                        category_url = urljoin(self.driver.current_url, href)
                    else:
                        category_url = urljoin(self.driver.current_url, href)
                    
                    # 중복 제거 (같은 이름이 여러 번 나올 수 있음)
                    if category_name not in categories:
                        categories[category_name] = {
                            'url': category_url,
                            'name': category_name
                        }
            
            # 캐시에 저장
            self._board_categories_cache = categories
            
            logger.info(f"게시판 {len(categories)}개 발견 (캐시 저장됨)")
            if len(categories) > 0:
                logger.info(f"샘플 게시판: {list(categories.keys())[:5]}")
            
            return categories
            
        except Exception as e:
            logger.error(f"게시판 목록 추출 중 오류: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {}
    
    def get_recent_responsible_person(self, category_name=None, category_url=None, limit=10):
        """특정 카테고리에서 최근 담당자(답변자) 추출"""
        try:
            if not category_url:
                # 카테고리 이름으로 URL 찾기
                categories = self.get_board_categories()
                if category_name in categories:
                    category_url = categories[category_name]['url']
                else:
                    logger.warning(f"카테고리 '{category_name}'를 찾을 수 없습니다.")
                    return None
            
            # 해당 카테고리 게시판으로 이동
            if not self.navigate_to_board(category_url):
                return None
            
            # 게시글 수집
            posts = self.get_posts(limit=limit, board_url=category_url)
            
            # 덧글 작성자 중 가장 최근에 답변한 사람 찾기
            responsible_persons = {}
            
            for post in posts:
                # 덧글에서 작성자 추출
                comments = post.get('comments', [])
                for comment in comments:
                    author = comment.get('author', '').strip()
                    date = comment.get('date', '')
                    
                    if author and author not in ['알 수 없음', '']:
                        # 날짜 파싱
                        try:
                            if date:
                                date_str = date.split()[0] if ' ' in date else date
                                comment_date = datetime.strptime(date_str, '%Y-%m-%d')
                                
                                # 기존 담당자보다 최근이면 업데이트
                                if author not in responsible_persons:
                                    responsible_persons[author] = comment_date
                                elif comment_date > responsible_persons[author]:
                                    responsible_persons[author] = comment_date
                        except:
                            pass
                
                # 게시글 작성자도 고려 (덧글이 없는 경우)
                post_author = post.get('author', '').strip()
                if post_author and post_author not in ['알 수 없음', '']:
                    try:
                        post_date_str = post.get('date', '').split()[0] if post.get('date') else ''
                        if post_date_str:
                            post_date = datetime.strptime(post_date_str, '%Y-%m-%d')
                            if post_author not in responsible_persons:
                                responsible_persons[post_author] = post_date
                            elif post_date > responsible_persons[post_author]:
                                responsible_persons[post_author] = post_date
                    except:
                        pass
            
            # 가장 최근에 활동한 담당자 반환
            if responsible_persons:
                most_recent = max(responsible_persons.items(), key=lambda x: x[1])
                logger.info(f"카테고리 '{category_name}'의 최근 담당자: {most_recent[0]} (최근 활동: {most_recent[1].strftime('%Y-%m-%d')})")
                return {
                    'name': most_recent[0],
                    'last_activity': most_recent[1].strftime('%Y-%m-%d'),
                    'all_persons': list(responsible_persons.keys())
                }
            
            return None
            
        except Exception as e:
            logger.error(f"담당자 정보 추출 중 오류: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _get_post_detail(self, post_url):
        """게시글 상세 페이지에서 본문과 덧글 가져오기"""
        try:
            if not self.driver:
                return None, []
            
            # 상세 페이지로 이동
            self.driver.get(post_url)
            time.sleep(2)  # 페이지 로딩 대기
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 본문 찾기: <div class="conts markdown-body" id="post{숫자}">
            content = ""
            # id가 "post"로 시작하는 div 찾기
            post_content = soup.find('div', id=re.compile(r'^post\d+'), class_=lambda x: x and 'conts' in x)
            if post_content:
                content = post_content.get_text(strip=True)
            else:
                # 대체: class="conts markdown-body" 찾기
                post_content = soup.find('div', class_=lambda x: x and 'conts' in x and 'markdown-body' in x)
                if post_content:
                    content = post_content.get_text(strip=True)
            
            # 덧글 찾기
            comments = []
            
            # 덧글은 <div class="conts" id="comment{숫자}"> 형태
            comment_divs = soup.find_all('div', id=re.compile(r'^comment\d+'), class_='conts')
            
            for comment_div in comment_divs:
                comment_id = comment_div.get('id', '')
                if not comment_id:
                    continue
                
                # 덧글 내용
                comment_text = comment_div.get_text(strip=True)
                if not comment_text or len(comment_text) < 5:
                    continue
                
                # 덧글 작성자와 날짜는 이전 형제 div의 테이블에서 찾기
                comment_author = ""
                comment_date = ""
                
                # 이전 형제 div 찾기 (덧글 헤더 테이블이 있는 div)
                prev_div = comment_div.find_previous_sibling('div')
                if prev_div:
                    # 테이블에서 작성자 찾기: <td><strong>&nbsp;이름</strong>
                    table = prev_div.find('table')
                    if table:
                        tds = table.find_all('td')
                        if len(tds) > 0:
                            # 첫 번째 td에 작성자
                            author_td = tds[0]
                            strong = author_td.find('strong')
                            if strong:
                                author_text = strong.get_text(strip=True)
                                # "&nbsp;" 제거
                                comment_author = author_text.replace('\xa0', '').replace('&nbsp;', '').strip()
                        
                        # 두 번째 td에 날짜
                        if len(tds) > 1:
                            date_td = tds[1]
                            date_div = date_td.find('div', class_='cont_date')
                            if date_div:
                                date_text = date_div.get_text(strip=True)
                                # "작성됨" 이전의 날짜 추출
                                date_match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', date_text)
                                if date_match:
                                    comment_date = date_match.group(1)
                
                if comment_text:
                    comments.append({
                        'author': comment_author,
                        'text': comment_text[:1000],  # 덧글 길이 증가
                        'date': comment_date
                    })
            
            logger.info(f"본문: {len(content)}자, 덧글: {len(comments)}개 수집")
            
            return content, comments
            
        except Exception as e:
            logger.error(f"게시글 상세 정보 가져오기 오류: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None, []
    
    def _check_date_filter(self, post_date, date_filter):
        """날짜 필터링 확인"""
        try:
            if not post_date:
                return True
            
            # 날짜 문자열 파싱 (YYYY-MM-DD 또는 YYYY-MM-DD HH:MM)
            date_str = post_date.split()[0] if ' ' in post_date else post_date
            post_dt = datetime.strptime(date_str, '%Y-%m-%d')
            
            today = datetime.now()
            
            if date_filter == 'today':
                return post_dt.date() == today.date()
            elif date_filter == 'yesterday':
                yesterday = today - timedelta(days=1)
                return post_dt.date() == yesterday.date()
            elif date_filter == 'this_week':
                # 이번 주 (월요일부터)
                days_since_monday = today.weekday()
                week_start = today - timedelta(days=days_since_monday)
                return post_dt >= week_start.replace(hour=0, minute=0, second=0, microsecond=0)
            elif date_filter == 'last_week':
                # 지난 주 (월요일부터 일요일까지)
                days_since_monday = today.weekday()
                week_start = today - timedelta(days=days_since_monday)
                last_week_start = week_start - timedelta(days=7)
                last_week_end = week_start - timedelta(days=1)
                return last_week_start.date() <= post_dt.date() <= last_week_end.date()
            elif date_filter == 'this_month':
                return post_dt.year == today.year and post_dt.month == today.month
            elif date_filter == 'last_month':
                last_month = today - timedelta(days=30)
                return post_dt.year == last_month.year and post_dt.month == last_month.month
            elif date_filter == 'recent':
                # 최근 7일
                week_ago = today - timedelta(days=7)
                return post_dt >= week_ago.replace(hour=0, minute=0, second=0, microsecond=0)
            
            return True
        except Exception as e:
            logger.warning(f"날짜 필터링 오류: {str(e)}")
            return True
    
    def get_posts(self, limit=50, board_url=None, date_filter=None):
        """게시판에서 게시글 수집"""
        try:
            if not self.driver:
                if not self.login():
                    return []
            
            # 특정 게시판 URL이 제공된 경우 해당 게시판으로 이동
            if board_url:
                if not self.navigate_to_board(board_url):
                    return []
            
            # 페이지 로딩 대기
            time.sleep(2)
            
            posts = []
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 디버그: 페이지 소스 저장
            logger.info(f"현재 URL: {self.driver.current_url}")
            debug_filename = "debug_board_page.html"
            with open(debug_filename, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            logger.info(f"게시판 페이지 HTML 저장: {debug_filename}")
            
            # 디버그: 페이지 구조 분석
            logger.info("=== 게시판 구조 분석 시작 ===")
            
            # 테이블 찾기
            tables = soup.find_all('table')
            logger.info(f"발견된 테이블 수: {len(tables)}")
            
            # 모든 tr 태그 찾기
            all_trs = soup.find_all('tr')
            logger.info(f"발견된 tr 태그 수: {len(all_trs)}")
            
            # 체크박스가 있는 tr 찾기
            trs_with_checkbox = [tr for tr in all_trs if tr.find('input', {'type': 'checkbox', 'name': 'idx'})]
            logger.info(f"체크박스가 있는 tr 수: {len(trs_with_checkbox)}")
            
            # a.nr10 태그 찾기
            nr10_links = soup.find_all('a', class_='nr10')
            logger.info(f"a.nr10 태그 수: {len(nr10_links)}")
            
            # post_view 링크 찾기
            post_view_links = soup.find_all('a', href=lambda x: x and 'post_view' in x)
            logger.info(f"post_view 링크 수: {len(post_view_links)}")
            
            # 첫 번째 게시글 행 샘플 출력 (있는 경우)
            if trs_with_checkbox:
                sample_row = trs_with_checkbox[0]
                logger.info("=== 첫 번째 게시글 행 샘플 ===")
                logger.info(f"HTML 구조:\n{str(sample_row)[:500]}...")
                
                # td 개수 확인
                tds = sample_row.find_all('td')
                logger.info(f"이 행의 td 개수: {len(tds)}")
                for i, td in enumerate(tds):
                    td_text = td.get_text(strip=True)
                    if td_text:
                        logger.info(f"  td[{i}]: {td_text[:50]}")
            
            logger.info("=== 게시판 구조 분석 완료 ===")
            
            # 게시판 테이블 구조 파싱
            # 테이블의 tr 태그에서 게시글 찾기
            # 일반적으로 게시글은 tr 태그 안에 있고, 제목은 a 태그 안에 있음
            table_rows = soup.find_all('tr')
            
            for row in table_rows:
                # 체크박스가 있는 행은 게시글 행일 가능성이 높음
                checkbox = row.find('input', {'type': 'checkbox', 'name': 'idx'})
                if not checkbox:
                    continue
                
                # 제목 찾기 - a 태그 중 class="nr10" 또는 href에 "post_view"가 있는 것
                title_link = row.find('a', class_='nr10')
                if not title_link:
                    # 대체: href에 post_view가 있는 a 태그
                    title_link = row.find('a', href=lambda x: x and 'post_view' in x)
                
                if title_link:
                    title = title_link.get_text(strip=True)
                    
                    # 댓글 수 추출
                    comment_count = 0
                    original_title = title
                    if '+' in title and '개의 추가 글' in title:
                        # "정산 관련 +11개의 추가 글" -> 댓글 수 추출
                        comment_match = re.search(r'\+(\d+)개의 추가 글', title)
                        if comment_match:
                            comment_count = int(comment_match.group(1))
                        title = title.split('+')[0].strip()
                    
                    # 게시글 상세 페이지 URL 추출
                    post_detail_url = None
                    if title_link.get('href'):
                        href = title_link.get('href')
                        if href.startswith('http'):
                            post_detail_url = href
                        elif href.startswith('/'):
                            post_detail_url = urljoin(self.driver.current_url, href)
                        else:
                            post_detail_url = urljoin(self.driver.current_url, href)
                    
                    # 추가 정보 추출 (작성자, 날짜 등)
                    tds = row.find_all('td')
                    author = ""
                    date = ""
                    
                    if len(tds) > 4:
                        # 날짜와 작성자 추출
                        for td in tds:
                            td_text = td.get_text(strip=True)
                            
                            # 날짜 형식 확인 (YYYY-MM-DD 또는 YYYY-MM-DD HH:MM)
                            # <td>2025-11-20 <span class="time01">10:02</span></td> 형태
                            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', td_text)
                            if date_match:
                                date_str = date_match.group(1)
                                # 시간 정보도 있는지 확인
                                time_span = td.find('span', class_='time01')
                                if time_span:
                                    time_str = time_span.get_text(strip=True)
                                    date = f"{date_str} {time_str}"
                                else:
                                    # 시간 정보가 없으면 날짜만
                                    date = date_str
                            
                            # 작성자 (한글 이름, 2-4자)
                            elif len(td_text) >= 2 and len(td_text) <= 4 and any('\uAC00' <= c <= '\uD7A3' for c in td_text):
                                if not author:
                                    author = td_text
                    
                    # 게시글 상세 페이지에서 본문과 덧글 가져오기 (선택적)
                    # 성능을 위해 처음 몇 개만 상세 정보 가져오기
                    content = title  # 기본값
                    comments = []
                    
                    # 처음 5개 게시글만 상세 정보 가져오기 (성능 최적화)
                    if post_detail_url and len(posts) < 5:
                        try:
                            logger.info(f"게시글 상세 정보 가져오기 시도: {title[:30]}...")
                            detail_content, detail_comments = self._get_post_detail(post_detail_url)
                            if detail_content and len(detail_content) > len(title):
                                content = detail_content
                                logger.info(f"본문 수집 성공: {len(content)}자")
                            if detail_comments:
                                comments = detail_comments
                                logger.info(f"덧글 {len(comments)}개 수집 성공")
                        except Exception as e:
                            logger.warning(f"게시글 상세 정보 가져오기 실패 ({title[:30]}...): {str(e)}")
                    else:
                        # 목록에서 추가 정보 추출 시도
                        # 제목이 있는 td의 전체 내용 확인
                        parent_td = title_link.find_parent('td')
                        if parent_td:
                            # 같은 td 안의 모든 텍스트 요소 찾기
                            all_text = parent_td.get_text(separator=' ', strip=True)
                            if len(all_text) > len(title) + 10:  # 제목 외에 추가 텍스트가 있는지
                                # 제목 외의 추가 텍스트가 있으면 내용으로 사용
                                # 제목 부분 제거
                                remaining_text = all_text.replace(title, '', 1).strip()
                                # 댓글 수 텍스트 제거
                                remaining_text = re.sub(r'\+\d+개의 추가 글', '', remaining_text).strip()
                                if remaining_text:
                                    content = f"{title} - {remaining_text[:500]}"
                        
                        # 같은 행의 다른 td에서 추가 정보 찾기
                        if content == title and len(tds) > 3:
                            # 제목이 있는 td의 인덱스 찾기
                            title_td_index = -1
                            for i, td in enumerate(tds):
                                if title_link in td.find_all():
                                    title_td_index = i
                                    break
                            
                            # 인접한 td에서 추가 정보 찾기
                            for i, td in enumerate(tds):
                                if i != title_td_index:
                                    td_text = td.get_text(strip=True)
                                    # 긴 텍스트가 있으면 내용으로 사용 (날짜, 작성자 제외)
                                    if len(td_text) > 20 and not re.match(r'^\d{4}-\d{2}-\d{2}', td_text):
                                        if not any('\uAC00' <= c <= '\uD7A3' for c in td_text[:3]):  # 한글 이름이 아닌 경우
                                            content = f"{title} - {td_text[:300]}"
                                            break
                    
                    # 날짜 필터링 적용
                    include_post = True
                    if date_filter and date:
                        include_post = self._check_date_filter(date, date_filter)
                    
                    if include_post:
                        posts.append({
                            'title': title,
                            'content': content[:1000],  # 본문 길이 증가
                            'author': author,
                            'date': date,
                            'comment_count': comment_count,
                            'comments': comments,  # 덧글 목록
                            'url': post_detail_url
                        })
                    
                    # limit 체크는 필터링 후 게시글 수로 확인
                    if len(posts) >= limit:
                        break
            
            # 위 방법으로 찾지 못한 경우, 대체 방법 시도
            if len(posts) == 0:
                logger.warning("기본 파싱 방법으로 게시글을 찾지 못함, 대체 방법 시도")
                
                # 모든 a 태그 중 href에 post_view가 있는 것 찾기
                post_links = soup.find_all('a', href=lambda x: x and 'post_view' in x)
                logger.info(f"대체 방법: post_view 링크 {len(post_links)}개 발견")
                
                for link in post_links[:limit]:
                    title = link.get_text(strip=True)
                    if title and len(title) > 0:
                        # 부모 tr 찾기
                        parent_tr = link.find_parent('tr')
                        author = ""
                        date = ""
                        
                        if parent_tr:
                            tds = parent_tr.find_all('td')
                            for td in tds:
                                td_text = td.get_text(strip=True)
                                # 날짜 형식 확인
                                if len(td_text) == 10 and '-' in td_text and td_text.count('-') == 2:
                                    date = td_text
                                # 작성자 (한글 이름, 2-4자)
                                elif len(td_text) >= 2 and len(td_text) <= 4 and any('\uAC00' <= c <= '\uD7A3' for c in td_text):
                                    if not author:
                                        author = td_text
                        
                        posts.append({
                            'title': title,
                            'content': title[:500],
                            'author': author,
                            'date': date
                        })
            
            if len(posts) == 0:
                logger.error("게시글을 전혀 찾지 못했습니다. HTML 구조를 확인해주세요.")
                logger.error(f"디버그 파일 확인: {debug_filename}")
            
            # 수집된 게시글 정보 요약 로그
            total_chars = sum(len(p.get('content', '')) for p in posts)
            total_comments = sum(len(p.get('comments', [])) for p in posts)
            posts_with_content = sum(1 for p in posts if p.get('content') and len(p.get('content', '')) > len(p.get('title', '')))
            
            filter_info = f" (날짜 필터: {date_filter})" if date_filter else ""
            logger.info(f"{len(posts)}개의 게시글 수집 완료{filter_info}")
            logger.info(f"  - 총 문자 수: {total_chars}자")
            logger.info(f"  - 본문이 있는 게시글: {posts_with_content}개")
            logger.info(f"  - 총 덧글 수: {total_comments}개")
            
            if date_filter:
                # 날짜 필터링된 게시글의 날짜 범위 표시
                dates = [p.get('date', '') for p in posts if p.get('date')]
                if dates:
                    logger.info(f"  - 날짜 범위: {min(dates)} ~ {max(dates)}")
            
            if total_chars < len(posts) * 20:
                logger.warning("게시글 내용이 거의 없습니다. 상세 페이지 접근이 실패했을 수 있습니다.")
            
            return posts
            
        except Exception as e:
            logger.error(f"게시글 수집 중 오류: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def get_all_posts_text(self, limit=50, board_url=None, date_filter=None):
        """모든 게시글을 텍스트로 반환 (컨텍스트용)"""
        posts = self.get_posts(limit, board_url, date_filter)
        if not posts:
            return ""
        
        text_parts = []
        for post in posts:
            post_text = f"제목: {post['title']}"
            if post.get('author'):
                post_text += f"\n작성자: {post['author']}"
            if post.get('date'):
                post_text += f"\n날짜: {post['date']}"
            if post.get('comment_count', 0) > 0:
                post_text += f"\n댓글 수: {post['comment_count']}개"
            
            # 내용 추가 (제목과 다를 때만)
            content = post.get('content', '')
            if content and content != post['title'] and len(content) > len(post['title']):
                post_text += f"\n내용: {content[:800]}"  # 본문 길이 증가
            
            # 덧글 정보 추가
            if post.get('comments') and len(post['comments']) > 0:
                post_text += f"\n\n덧글 ({len(post['comments'])}개):"
                for i, comment in enumerate(post['comments'][:5], 1):  # 최대 5개만 표시
                    comment_text = f"\n  [{i}] "
                    if comment.get('author'):
                        comment_text += f"작성자: {comment['author']} | "
                    if comment.get('date'):
                        comment_text += f"날짜: {comment['date']} | "
                    if comment.get('text'):
                        comment_text += f"내용: {comment['text']}"
                    post_text += comment_text
            
            text_parts.append(post_text)
        
        result = "\n\n".join(text_parts)
        logger.info(f"게시판 정보 수집 성공: {len(result)}자")
        return result
    
    def close(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("드라이버 종료")

