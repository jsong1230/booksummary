"""
NotebookLM용 URL 수집 스크립트
책 제목을 받아서 YouTube 영상 포함 20개 이상의 URL을 수집합니다.
"""

import os
import sys
import json
import time
from typing import List, Dict
from pathlib import Path

# src 디렉토리를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from googlesearch import search
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv

load_dotenv()

class NotebookLMURLCollector:
    """NotebookLM용 URL 수집 클래스"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.urls = []
    
    def search_urls(self, book_title: str, author: str = None, num_results: int = 25) -> List[str]:
        """
        책 관련 URL 수집 (YouTube 영상 포함)
        
        Args:
            book_title: 책 제목
            author: 저자 이름
            num_results: 수집할 URL 개수
        """
        query = book_title
        if author:
            query = f"{book_title} {author}"
        
        print(f"🔍 '{book_title}' 관련 URL 수집 중...")
        print(f"   목표: {num_results}개 이상\n")
        
        # 검색 쿼리 생성 (YouTube 포함)
        search_queries = [
            f"{query} site:youtube.com",  # YouTube 영상
            f"{query} site:youtu.be",     # YouTube 단축 URL
            f"{query} site:ko.wikipedia.org",  # 위키백과
            f"{query} site:kyobobook.co.kr",   # 교보문고
            f"{query} site:yes24.com",         # 예스24
            f"{query} site:aladin.co.kr",      # 알라딘
            f"{query} site:hani.co.kr 리뷰",   # 한겨레
            f"{query} site:khan.co.kr 리뷰",   # 경향신문
            f"{query} site:joongang.co.kr 리뷰", # 중앙일보
            f"{query} 서평 리뷰",              # 일반 서평/리뷰
            f"{query} 책 소개",                # 책 소개
            f"{query} 작가 인터뷰",            # 작가 인터뷰
            f"{query} 강의",                   # 강의/강연
            f"{query} 팟캐스트",               # 팟캐스트
        ]
        
        all_urls = []
        seen_urls = set()
        
        for search_query in search_queries:
            try:
                print(f"  검색 중: {search_query[:50]}...")
                results = search(search_query, num_results=5, lang='ko')
                
                for url in results:
                    if url not in seen_urls:
                        seen_urls.add(url)
                        all_urls.append(url)
                        print(f"    ✓ {url}")
                
                time.sleep(2)  # 요청 간 대기
                
            except Exception as e:
                print(f"  ⚠️ 검색 오류: {e}")
                continue
        
        print(f"\n✅ 총 {len(all_urls)}개의 URL을 수집했습니다.\n")
        return all_urls[:num_results]
    
    def validate_url(self, url: str) -> Dict[str, any]:
        """URL 유효성 검증"""
        try:
            response = self.session.get(url, timeout=10, allow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title = None
            if soup.title:
                title = soup.title.string.strip()
            elif soup.find('meta', property='og:title'):
                title = soup.find('meta', property='og:title')['content']
            
            description = None
            if soup.find('meta', property='og:description'):
                description = soup.find('meta', property='og:description')['content']
            elif soup.find('meta', attrs={'name': 'description'}):
                description = soup.find('meta', attrs={'name': 'description'})['content']
            
            return {
                'url': url,
                'valid': True,
                'title': title,
                'description': description,
                'status_code': response.status_code
            }
        except Exception as e:
            return {
                'url': url,
                'valid': False,
                'error': str(e)
            }
    
    def save_urls(self, book_title: str, urls: List[str], validate: bool = False) -> Dict[str, str]:
        """
        URL을 파일로 저장 (마크다운 형식 포함)
        
        Args:
            book_title: 책 제목
            urls: URL 리스트
            validate: URL 유효성 검증 여부
        """
        safe_title = "".join(c for c in book_title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')
        
        output_dir = Path("assets/urls")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        txt_path = output_dir / f"{safe_title}_notebooklm.txt"
        md_path = output_dir / f"{safe_title}_notebooklm.md"
        json_path = output_dir / f"{safe_title}_notebooklm.json"
        
        # 텍스트 파일 저장 (NotebookLM용 - 한 줄에 하나씩)
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"# {book_title} - NotebookLM용 URL 리스트\n")
            f.write(f"# 총 {len(urls)}개의 URL\n\n")
            for url in urls:
                f.write(f"{url}\n")
        
        # 마크다운 파일 저장 (NotebookLM 복사용)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# {book_title} - NotebookLM 소스 URL\n\n")
            f.write(f"**총 {len(urls)}개의 URL**\n\n")
            f.write("## 📋 URL 리스트\n\n")
            f.write("아래 URL들을 복사하여 NotebookLM에 소스로 추가하세요.\n\n")
            f.write("```\n")
            for i, url in enumerate(urls, 1):
                f.write(f"{url}\n")
            f.write("```\n\n")
            f.write("## 📝 사용 방법\n\n")
            f.write("1. 위 URL 블록을 전체 선택 (Cmd+A / Ctrl+A)\n")
            f.write("2. 복사 (Cmd+C / Ctrl+C)\n")
            f.write("3. NotebookLM에서 '소스 추가' > 'URL' 선택\n")
            f.write("4. 붙여넣기 (각 URL이 자동으로 인식됩니다)\n\n")
        
        # JSON 파일 저장 (상세 정보)
        url_data = {
            'book_title': book_title,
            'collected_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_urls': len(urls),
            'urls': []
        }
        
        if validate:
            print("🔍 URL 유효성 검증 중...")
            for i, url in enumerate(urls, 1):
                print(f"  [{i}/{len(urls)}] {url}")
                url_info = self.validate_url(url)
                url_data['urls'].append(url_info)
                time.sleep(0.5)
        else:
            url_data['urls'] = [{'url': url, 'valid': None} for url in urls]
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(url_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 URL 데이터를 저장했습니다:")
        print(f"   - TXT: {txt_path}")
        print(f"   - MD (NotebookLM 복사용): {md_path}")
        print(f"   - JSON (상세 정보): {json_path}")
        
        return {'txt_path': str(txt_path), 'md_path': str(md_path), 'json_path': str(json_path)}


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NotebookLM용 URL 수집')
    parser.add_argument('--title', type=str, help='책 제목')
    parser.add_argument('--author', type=str, help='저자 이름')
    parser.add_argument('--num', type=int, default=25, help='수집할 URL 개수 (기본값: 25)')
    parser.add_argument('--validate', action='store_true', help='URL 유효성 검증 수행')
    
    args = parser.parse_args()
    
    collector = NotebookLMURLCollector()
    
    if args.title:
        book_title = args.title
        author = args.author
    else:
        # 인터랙티브 모드
        print("=" * 60)
        print("📚 NotebookLM용 URL 수집기")
        print("=" * 60)
        print()
        
        book_title = input("책 제목을 입력하세요: ").strip()
        if not book_title:
            print("❌ 책 제목을 입력해주세요.")
            return
        
        author = input("저자 이름을 입력하세요 (선택사항): ").strip() or None
        num_results = input("수집할 URL 개수 (기본값: 25): ").strip()
        args.num = int(num_results) if num_results.isdigit() else 25
        args.validate = input("URL 유효성 검증을 수행하시겠습니까? (y/n, 기본값: n): ").strip().lower() == 'y'
    
    print()
    
    # URL 수집
    urls = collector.search_urls(book_title, author, args.num)
    
    if urls:
        # URL 저장
        result = collector.save_urls(book_title, urls, validate=args.validate)
        
        print()
        print("=" * 60)
        print("✅ URL 수집 완료!")
        print("=" * 60)
        print(f"\n📄 NotebookLM용 파일: {result['txt_path']}")
        print(f"\n💡 다음 단계:")
        print(f"   1. {result['txt_path']} 파일을 엽니다")
        print(f"   2. URL들을 복사합니다")
        print(f"   3. NotebookLM (https://notebooklm.google.com)에 접속합니다")
        print(f"   4. 새 소스 추가 > URL에서 붙여넣기합니다")
        print()
    else:
        print("❌ 수집된 URL이 없습니다.")


if __name__ == "__main__":
    main()

