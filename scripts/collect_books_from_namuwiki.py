"""
나무위키에서 일당백 책 목록 수집 스크립트
"""

import requests
from bs4 import BeautifulSoup
import csv
import re
from pathlib import Path
from typing import List, Dict, Optional
import time

def parse_namuwiki_books(url: str) -> List[Dict]:
    """나무위키 페이지에서 책 목록 파싱"""
    print(f"📚 나무위키 페이지에서 책 목록 수집 중...")
    print(f"URL: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        books = []
        seen_books = set()  # 중복 체크용
        
        # 나무위키 테이블에서 책 정보 추출
        tables = soup.find_all('table')
        print(f"테이블 {len(tables)}개 발견")
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:  # 회차, 작품, 작가 컬럼이 있는 경우
                    try:
                        # 회차 (첫 번째 셀)
                        episode = cells[0].get_text(strip=True)
                        # 작품 (두 번째 셀)
                        title = cells[1].get_text(strip=True)
                        # 작가 (세 번째 셀)
                        author = cells[2].get_text(strip=True)
                        
                        # 유효한 책 정보인지 확인
                        if title and author and title != '작품' and author != '작가':
                            # 회차 번호 추출 (예: "1화", "1회" 등)
                            episode_num = re.search(r'(\d+)', episode)
                            episode_num = int(episode_num.group(1)) if episode_num else 0
                            
                            # 중복 체크
                            book_key = (title.lower(), author.lower())
                            if book_key not in seen_books:
                                seen_books.add(book_key)
                                books.append({
                                    'title': title,
                                    'author': author,
                                    'episode': episode_num,
                                    'episode_text': episode
                                })
                    except Exception as e:
                        continue
        
        # 테이블에서 찾지 못한 경우 텍스트에서 패턴 찾기
        if not books:
            print("테이블에서 찾지 못해 텍스트에서 패턴 검색 중...")
            all_text = soup.get_text()
            lines = all_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 다양한 패턴 시도
                patterns = [
                    r'(\d+)화\s*(.+?)\s*[-–]\s*(.+)',  # "1화 책제목 - 저자"
                    r'(\d+)회\s*(.+?)\s*[-–]\s*(.+)',  # "1회 책제목 - 저자"
                    r'(\d+)\.\s*(.+?)\s*[-–]\s*(.+)',  # "1. 책제목 - 저자"
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, line)
                    if match:
                        num, title, author = match.groups()
                        episode_num = int(num)
                        
                        # 유효성 체크
                        if episode_num <= 200 and len(title) > 1 and len(author) > 1:
                            book_key = (title.strip().lower(), author.strip().lower())
                            if book_key not in seen_books:
                                seen_books.add(book_key)
                                books.append({
                                    'title': title.strip(),
                                    'author': author.strip(),
                                    'episode': episode_num,
                                    'episode_text': f"{episode_num}화"
                                })
                                break
        
        # 에피소드 번호순으로 정렬
        books.sort(key=lambda x: x['episode'])
        
        print(f"✅ {len(books)}개의 책을 찾았습니다.")
        return books
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return []


def update_csv_with_books(books: List[Dict], csv_path: str = "data/ildangbaek_books.csv"):
    """CSV 파일에 책 목록 추가"""
    csv_file = Path(csv_path)
    
    # 기존 책 목록 로드
    existing_books = []
    existing_titles = set()
    
    if csv_file.exists():
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_books.append(row)
                existing_titles.add(row.get('title', '').strip().lower())
    
    # 새 책 추가
    added_count = 0
    fieldnames = ['title', 'author', 'category', 'season', 'episode', 
                 'source', 'status', 'video_created', 'youtube_uploaded', 
                 'notes', 'added_at']
    
    for book in books:
        title = book['title']
        author = book['author']
        
        # 중복 체크 (대소문자 무시)
        if title.lower() not in existing_titles:
            # 에피소드 정보 추가
            episode_str = str(book.get('episode', '')) if book.get('episode') else ''
            
            existing_books.append({
                'title': title,
                'author': author,
                'category': 'ildangbaek',
                'season': '',
                'episode': episode_str,
                'source': '나무위키',
                'status': 'not_processed',
                'video_created': '',
                'youtube_uploaded': '',
                'notes': '',
                'added_at': ''
            })
            existing_titles.add(title.lower())
            added_count += 1
            print(f"  ✓ 추가: {title} - {author}")
        else:
            print(f"  ⊘ 건너뜀 (이미 존재): {title}")
    
    # CSV 저장
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for book in existing_books:
            row = {field: book.get(field, '') for field in fieldnames}
            writer.writerow(row)
    
    print(f"\n✅ CSV 업데이트 완료: {added_count}개 추가, 총 {len(existing_books)}개")
    return added_count


def main():
    url = 'https://namu.wiki/w/일당백%20:%20일생동안%20읽어야%20할%20백권의%20책'
    
    print("=" * 60)
    print("📚 나무위키에서 일당백 책 목록 수집")
    print("=" * 60)
    print()
    
    # 책 목록 파싱
    books = parse_namuwiki_books(url)
    
    if not books:
        print("\n⚠️ 책 목록을 찾을 수 없습니다.")
        print("페이지 구조가 변경되었을 수 있습니다.")
        return
    
    print(f"\n📖 찾은 책 목록 (처음 10개):")
    for book in books[:10]:
        print(f"  {book['episode']}화. {book['title']} - {book['author']}")
    
    if len(books) > 10:
        print(f"  ... 외 {len(books) - 10}개")
    
    print()
    
    # CSV 업데이트
    added_count = update_csv_with_books(books)
    
    print()
    print("=" * 60)
    print("✅ 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
