"""
CSV 데이터를 JSON으로 변환하는 스크립트
Cloudflare Pages Functions에서 사용할 수 있도록 변환합니다.
"""
import csv
import json
import os
import sys
from datetime import datetime
import re

# CSV 필드 크기 제한 증가 (Windows 호환)
try:
    csv.field_size_limit(131072 * 10)  # 기본값의 10배
except OverflowError:
    csv.field_size_limit(2147483647)  # Windows에서 사용 가능한 최대값

def clean_html(text):
    """HTML 태그 제거 및 텍스트 정리"""
    if not text:
        return ""
    # HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)
    # HTML 엔티티 제거
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    # 공백 정리
    text = ' '.join(text.split())
    return text.strip()

def parse_date(date_str):
    """날짜 문자열 파싱"""
    if not date_str:
        return None
    
    date_formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%Y/%m/%d %H:%M:%S',
        '%Y/%m/%d'
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).isoformat()
        except:
            continue
    
    return date_str

def convert_posts_csv(input_file, output_file):
    """원글 CSV를 JSON으로 변환"""
    posts = []
    
    print(f"원글 CSV 파일 읽는 중: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 필요한 필드만 추출하고 정리
            post = {
                'id': row.get('id', ''),
                'name': row.get('name', ''),
                'writer': row.get('writer', ''),
                'subject': clean_html(row.get('subject', '[제목 없음]')),
                'content': clean_html(row.get('content', ''))[:500],  # 내용은 500자로 제한
                'reg_date': parse_date(row.get('reg_date', '')),
                'comm_cnt': int(row.get('comm_cnt', 0) or 0),
                'hit_cnt': int(row.get('hit_cnt', 0) or 0),
            }
            posts.append(post)
    
    print(f"총 {len(posts)}개의 게시글 변환 완료")
    
    # JSON 파일로 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    
    print(f"JSON 파일 저장 완료: {output_file}")
    return posts

def convert_comments_csv(input_file, output_file):
    """댓글 CSV를 JSON으로 변환"""
    comments = []
    
    print(f"댓글 CSV 파일 읽는 중: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            comment = {
                'id': row.get('id', ''),
                'post_id': row.get('post_id', ''),
                'writer': row.get('writer', ''),
                'content': clean_html(row.get('content', ''))[:300],  # 댓글은 300자로 제한
                'reg_date': parse_date(row.get('reg_date', '')),
            }
            comments.append(comment)
    
    print(f"총 {len(comments)}개의 댓글 변환 완료")
    
    # JSON 파일로 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)
    
    print(f"JSON 파일 저장 완료: {output_file}")
    return comments

def create_indexed_data(posts, comments):
    """검색을 위한 인덱스 데이터 생성"""
    # 고객사별로 그룹화
    clients = {}
    for post in posts:
        client_name = post.get('name', '')
        if client_name not in clients:
            clients[client_name] = []
        clients[client_name].append(post)
    
    # 게시글 ID별 댓글 매핑
    comments_by_post = {}
    for comment in comments:
        post_id = comment.get('post_id', '')
        if post_id not in comments_by_post:
            comments_by_post[post_id] = []
        comments_by_post[post_id].append(comment)
    
    return {
        'clients': clients,
        'comments_by_post': comments_by_post,
        'client_names': sorted(list(clients.keys()))
    }

def main():
    """메인 함수"""
    base_dir = os.path.dirname(__file__)
    functions_dir = os.path.join(base_dir, 'functions', 'data')
    
    # functions/data 디렉토리 생성
    os.makedirs(functions_dir, exist_ok=True)
    
    # CSV 파일 경로
    posts_csv = os.path.join(base_dir, '20251125_PPM학습용데이터_원글.csv')
    comments_csv = os.path.join(base_dir, '20251125_PPM학습용데이터_댓글.csv')
    
    # JSON 파일 경로
    posts_json = os.path.join(functions_dir, 'posts.json')
    comments_json = os.path.join(functions_dir, 'comments.json')
    indexed_json = os.path.join(functions_dir, 'indexed.json')
    
    # CSV 파일 존재 확인
    if not os.path.exists(posts_csv):
        print(f"오류: 원글 CSV 파일을 찾을 수 없습니다: {posts_csv}")
        return
    
    if not os.path.exists(comments_csv):
        print(f"오류: 댓글 CSV 파일을 찾을 수 없습니다: {comments_csv}")
        return
    
    # 변환 실행
    print("=" * 50)
    print("CSV to JSON 변환 시작")
    print("=" * 50)
    
    posts = convert_posts_csv(posts_csv, posts_json)
    comments = convert_comments_csv(comments_csv, comments_json)
    
    # 인덱스 데이터 생성
    print("\n인덱스 데이터 생성 중...")
    indexed_data = create_indexed_data(posts, comments)
    
    with open(indexed_json, 'w', encoding='utf-8') as f:
        json.dump(indexed_data, f, ensure_ascii=False, indent=2)
    
    print(f"인덱스 JSON 파일 저장 완료: {indexed_json}")
    
    print("\n" + "=" * 50)
    print("변환 완료!")
    print(f"- 게시글: {len(posts)}개")
    print(f"- 댓글: {len(comments)}개")
    print(f"- 고객사: {len(indexed_data['client_names'])}개")
    print("=" * 50)

if __name__ == '__main__':
    main()

