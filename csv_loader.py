"""
CSV 데이터 로더 모듈
게시판 데이터를 CSV 파일에서 로드합니다.
"""
import csv
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CSVDataLoader:
    def __init__(self, posts_csv_path: str, comments_csv_path: str):
        """
        CSV 데이터 로더 초기화
        
        Args:
            posts_csv_path: 원글 CSV 파일 경로
            comments_csv_path: 댓글 CSV 파일 경로
        """
        self.posts_csv_path = posts_csv_path
        self.comments_csv_path = comments_csv_path
        self.posts_data = []
        self.comments_data = []
        self._load_data()
    
    def _load_data(self):
        """CSV 파일에서 데이터 로드"""
        try:
            # 원글 데이터 로드
            if os.path.exists(self.posts_csv_path):
                with open(self.posts_csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    self.posts_data = list(reader)
                logger.info(f"원글 데이터 {len(self.posts_data)}개 로드 완료")
            else:
                logger.warning(f"원글 CSV 파일을 찾을 수 없습니다: {self.posts_csv_path}")
            
            # 댓글 데이터 로드
            if os.path.exists(self.comments_csv_path):
                with open(self.comments_csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    self.comments_data = list(reader)
                logger.info(f"댓글 데이터 {len(self.comments_data)}개 로드 완료")
            else:
                logger.warning(f"댓글 CSV 파일을 찾을 수 없습니다: {self.comments_csv_path}")
                
        except Exception as e:
            logger.error(f"CSV 데이터 로드 중 오류: {str(e)}")
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """날짜 문자열을 datetime 객체로 변환"""
        if not date_str:
            return None
        
        # 다양한 날짜 형식 시도
        date_formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y/%m/%d %H:%M:%S',
            '%Y/%m/%d'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except:
                continue
        
        return None
    
    def _filter_by_date(self, date_str: str, date_filter: str) -> bool:
        """날짜 필터에 맞는지 확인"""
        if not date_filter or not date_str:
            return True
        
        post_date = self._parse_date(date_str)
        if not post_date:
            return True
        
        now = datetime.now()
        
        if date_filter == 'today':
            return post_date.date() == now.date()
        elif date_filter == 'yesterday':
            return post_date.date() == (now - timedelta(days=1)).date()
        elif date_filter == 'this_week':
            week_start = now - timedelta(days=now.weekday())
            return post_date >= week_start
        elif date_filter == 'last_week':
            week_start = now - timedelta(days=now.weekday() + 7)
            week_end = now - timedelta(days=now.weekday())
            return week_start <= post_date < week_end
        elif date_filter == 'this_month':
            return post_date.year == now.year and post_date.month == now.month
        elif date_filter == 'last_month':
            last_month = now - timedelta(days=now.day)
            return post_date.year == last_month.year and post_date.month == last_month.month
        elif date_filter == 'recent':
            week_ago = now - timedelta(days=7)
            return post_date >= week_ago
        
        return True
    
    def get_posts_text(self, limit: int = 30, client_name: Optional[str] = None, 
                      date_filter: Optional[str] = None) -> str:
        """
        게시글 데이터를 텍스트로 변환
        
        Args:
            limit: 최대 게시글 수
            client_name: 고객사 이름 필터
            date_filter: 날짜 필터 (today, yesterday, this_week, last_week, this_month, last_month, recent)
        
        Returns:
            게시글 정보를 담은 텍스트
        """
        if not self.posts_data:
            return ""
        
        filtered_posts = []
        
        for post in self.posts_data:
            # 고객사 필터
            if client_name:
                post_client = post.get('name', '')
                if client_name not in post_client and post_client not in client_name:
                    continue
            
            # 날짜 필터
            reg_date = post.get('reg_date', '')
            if not self._filter_by_date(reg_date, date_filter):
                continue
            
            filtered_posts.append(post)
        
        # 댓글 수 기준으로 정렬 (문제 케이스 우선)
        filtered_posts.sort(key=lambda x: int(x.get('comm_cnt', 0) or 0), reverse=True)
        
        # 제한된 수만큼만 선택
        selected_posts = filtered_posts[:limit]
        
        # 텍스트로 변환
        result_lines = []
        for post in selected_posts:
            name = post.get('name', '')
            writer = post.get('writer', '')
            subject = post.get('subject', '[제목 없음]')
            content = post.get('content', '')
            reg_date = post.get('reg_date', '')
            comm_cnt = post.get('comm_cnt', '0')
            
            # HTML 태그 제거 (간단한 처리)
            import re
            content = re.sub(r'<[^>]+>', '', content)
            content = content.replace('&nbsp;', ' ').strip()
            
            result_lines.append(
                f"[고객사: {name}] 작성자: {writer} | 제목: {subject}\n"
                f"내용: {content[:200]}...\n"
                f"등록일: {reg_date} | 댓글 수: {comm_cnt}\n"
            )
        
        return "\n---\n".join(result_lines)
    
    def get_comments_for_post(self, post_id: str) -> List[Dict]:
        """특정 게시글의 댓글 가져오기"""
        return [comment for comment in self.comments_data 
                if comment.get('post_id') == post_id]
    
    def get_client_names(self) -> List[str]:
        """고객사 이름 목록 가져오기"""
        if not self.posts_data:
            return []
        
        client_names = set()
        for post in self.posts_data:
            name = post.get('name', '')
            if name:
                client_names.add(name)
        
        return sorted(list(client_names))
    
    def get_responsible_person(self, client_name: str) -> Optional[Dict]:
        """고객사별 최근 담당자 정보 가져오기"""
        if not self.posts_data:
            return None
        
        # 해당 고객사의 최근 게시글 찾기
        client_posts = [post for post in self.posts_data 
                       if client_name in post.get('name', '')]
        
        if not client_posts:
            return None
        
        # 최근 게시글의 작성자 정보
        latest_post = max(client_posts, 
                         key=lambda x: self._parse_date(x.get('reg_date', '')) or datetime.min)
        
        return {
            'name': latest_post.get('writer', ''),
            'last_activity': latest_post.get('reg_date', '')
        }

