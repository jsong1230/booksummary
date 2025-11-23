"""
NotebookLM용 URL 수집 스크립트
책 제목을 받아서 한글/영어 자료를 반반씩 수집하여 마크다운 파일을 생성합니다.
"""

import os
import sys
import json
import time
from typing import List, Dict, Tuple
from pathlib import Path

# src 디렉토리를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv

# YouTube API import
try:
    from googleapiclient.discovery import build
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False

load_dotenv()

class NotebookLMURLCollector:
    """NotebookLM용 URL 수집 클래스 (한글/영어 분리 수집)"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.urls = []
        self.ddgs = DDGS()  # DuckDuckGo 검색 인스턴스
        
        # YouTube API 초기화
        self.youtube = None
        if YOUTUBE_API_AVAILABLE:
            youtube_api_key = os.getenv("YOUTUBE_API_KEY") or os.getenv("GOOGLE_BOOKS_API_KEY")
            if youtube_api_key:
                try:
                    self.youtube = build('youtube', 'v3', developerKey=youtube_api_key)
                    print("✅ YouTube API 초기화 완료")
                except Exception as e:
                    print(f"⚠️ YouTube API 초기화 실패: {e}")
    
    def search_urls_bilingual(
        self, 
        book_title: str, 
        author: str = None, 
        total_results: int = 30,
        en_title: str = None
    ) -> Tuple[List[str], List[str]]:
        """
        한글/영어 자료를 반반씩 수집
        
        Args:
            book_title: 책 제목 (한글)
            author: 저자 이름
            total_results: 총 수집할 URL 개수
            translate_title: 영어 제목 자동 번역 여부
            
        Returns:
            (한글_urls, 영어_urls) 튜플
        """
        ko_count = total_results // 2
        en_count = total_results - ko_count
        
        print(f"🔍 '{book_title}' 관련 URL 수집 중...")
        print(f"   목표: 한글 {ko_count}개 + 영어 {en_count}개 = 총 {total_results}개\n")
        
        # 영어 제목 설정
        if not en_title:
            en_title = self._translate_title(book_title)
        
        # 한글 URL 수집
        print("=" * 60)
        print("📚 한글 자료 수집 중...")
        print("=" * 60)
        ko_urls = self._search_korean_urls(book_title, author, ko_count)
        
        # 영어 URL 수집
        print("\n" + "=" * 60)
        print("📚 English Resources Collection...")
        print("=" * 60)
        en_urls = self._search_english_urls(book_title, author, en_count, en_title)
        
        print(f"\n✅ 수집 완료:")
        print(f"   한글: {len(ko_urls)}개")
        print(f"   영어: {len(en_urls)}개")
        print(f"   총계: {len(ko_urls) + len(en_urls)}개\n")
        
        return ko_urls, en_urls
    
    def _search_korean_urls(self, book_title: str, author: str = None, num_results: int = 15) -> List[str]:
        """한글 자료 수집"""
        query = book_title
        if author:
            query = f"{book_title} {author}"
        
        all_urls = []
        
        # YouTube 직접 검색 (우선)
        youtube_urls = self._search_youtube_direct(query, book_title, author, max_results=5)
        all_urls.extend(youtube_urls)
        
        # 나머지 소스는 DuckDuckGo로 검색
        search_queries = [
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
        
        remaining_count = max(0, num_results - len(all_urls))
        if remaining_count > 0:
            other_urls = self._execute_search(search_queries, remaining_count, lang='ko')
            all_urls.extend(other_urls)
        
        return all_urls[:num_results]
    
    def _search_youtube_direct(self, query: str, book_title: str, author: str = None, max_results: int = 5, region: str = 'KR') -> List[str]:
        """YouTube Data API를 사용하여 직접 검색"""
        if not self.youtube:
            # YouTube API가 없으면 빈 리스트 반환
            return []
        
        youtube_urls = []
        seen_video_ids = set()
        
        # YouTube 검색 쿼리 생성
        youtube_queries = [
            f"{query} 리뷰",
            f"{query} 서평",
            f"{query} 책",
            f"{query} 작가 인터뷰",
            f"{query} 강의",
        ]
        
        try:
            for search_query in youtube_queries:
                if len(youtube_urls) >= max_results:
                    break
                
                try:
                    search_response = self.youtube.search().list(
                        q=search_query,
                        part='id,snippet',
                        type='video',
                        maxResults=3,
                        order='relevance',
                        regionCode=region
                    ).execute()
                    
                    for item in search_response.get('items', []):
                        if len(youtube_urls) >= max_results:
                            break
                        
                        video_id = item['id']['videoId']
                        if video_id not in seen_video_ids:
                            seen_video_ids.add(video_id)
                            video_url = f"https://www.youtube.com/watch?v={video_id}"
                            youtube_urls.append(video_url)
                            print(f"    ✓ YouTube: {item['snippet']['title'][:50]}...")
                    
                    time.sleep(0.5)  # API 제한 방지
                    
                except Exception as e:
                    print(f"  ⚠️ YouTube 검색 오류: {e}")
                    continue
                    
        except Exception as e:
            print(f"  ⚠️ YouTube API 오류: {e}")
        
        return youtube_urls
    
    def _translate_title(self, book_title: str) -> str:
        """책 제목을 영어로 번역 (간단한 매핑)"""
        translations = {
            "노르웨이의 숲": "Norwegian Wood",
            "노르웨이의_숲": "Norwegian Wood",
            "1984": "1984",
            "사피엔스": "Sapiens",
            "21세기를 위한 21가지 제언": "21 Lessons for the 21st Century",
            "호모 데우스": "Homo Deus",
            "1Q84": "1Q84",
            "해변의 카프카": "Kafka on the Shore",
            "동물농장": "Animal Farm",
            "노인과 바다": "The Old Man and the Sea",
            "위대한 개츠비": "The Great Gatsby",
            "호밀밭의 파수꾼": "The Catcher in the Rye",
            "앵무새 죽이기": "To Kill a Mockingbird",
            "오만과 편견": "Pride and Prejudice",
            "전쟁과 평화": "War and Peace",
            "안나 카레니나": "Anna Karenina",
        }
        # 공백을 언더스코어로 변환한 버전도 확인
        book_title_underscore = book_title.replace(' ', '_')
        if book_title_underscore in translations:
            return translations[book_title_underscore]
        # 번역이 없으면 원본 반환 (주제의 경우 그대로 사용)
        return translations.get(book_title, book_title)
    
    def _search_english_urls(self, book_title: str, author: str = None, num_results: int = 15, en_title: str = None) -> List[str]:
        """영어 자료 수집"""
        # 영어 제목 변환
        if not en_title:
            en_title = self._translate_title(book_title)
        en_query = en_title
        if author:
            en_query = f"{en_title} {author}"
        
        all_urls = []
        
        # YouTube 직접 검색 (우선)
        youtube_urls = self._search_youtube_direct(en_query, en_title, author, max_results=5, region='US')
        all_urls.extend(youtube_urls)
        
        # 나머지 소스는 DuckDuckGo로 검색
        search_queries = [
            f"{en_query} site:en.wikipedia.org",  # Wikipedia
            f"{en_query} site:goodreads.com",     # Goodreads
            f"{en_query} site:amazon.com review", # Amazon reviews
            f"{en_query} site:nytimes.com review", # NY Times
            f"{en_query} site:theguardian.com review", # The Guardian
            f"{en_query} book review",              # General reviews
            f"{en_query} book summary",            # Book summary
            f"{en_query} author interview",        # Author interview
            f"{en_query} lecture",                  # Lecture
            f"{en_query} podcast",                  # Podcast
            f"{en_query} analysis",                 # Analysis
            f"{en_query} discussion",               # Discussion
        ]
        
        remaining_count = max(0, num_results - len(all_urls))
        if remaining_count > 0:
            other_urls = self._execute_search(search_queries, remaining_count, lang='en')
            all_urls.extend(other_urls)
        
        return all_urls[:num_results]
    
    def _execute_search(self, search_queries: List[str], num_results: int, lang: str = 'ko') -> List[str]:
        """검색 쿼리 실행 (DuckDuckGo 사용)"""
        all_urls = []
        seen_urls = set()
        
        for search_query in search_queries:
            if len(all_urls) >= num_results:
                break
                
            try:
                print(f"  검색 중: {search_query[:60]}...")
                # DuckDuckGo 검색 (각 쿼리당 최대 5개 결과)
                results = list(self.ddgs.text(search_query, max_results=5))
                
                for result in results:
                    if len(all_urls) >= num_results:
                        break
                    url = result.get('href', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_urls.append(url)
                        print(f"    ✓ {url}")
                
                time.sleep(1)  # 요청 간 대기 (DuckDuckGo는 덜 엄격함)
                
            except Exception as e:
                print(f"  ⚠️ 검색 오류: {e}")
                continue
        
        return all_urls[:num_results]
    
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
                # DuckDuckGo 검색
                results = list(self.ddgs.text(search_query, max_results=5))
                
                for result in results:
                    url = result.get('href', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_urls.append(url)
                        print(f"    ✓ {url}")
                
                time.sleep(1)  # 요청 간 대기
                
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
    
    def save_urls_bilingual(
        self, 
        book_title: str, 
        ko_urls: List[str], 
        en_urls: List[str],
        author: str = None,
        validate: bool = False
    ) -> Dict[str, str]:
        """
        한글/영어 URL을 파일로 저장 (마크다운 형식 포함)
        
        Args:
            book_title: 책 제목
            ko_urls: 한글 URL 리스트
            en_urls: 영어 URL 리스트
            author: 저자 이름
            validate: URL 유효성 검증 여부
        """
        safe_title = "".join(c for c in book_title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')
        
        output_dir = Path("assets/urls")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        md_path = output_dir / f"{safe_title}_notebooklm.md"
        
        total_urls = ko_urls + en_urls
        
        # 마크다운 파일 저장 (한글/영어 섹션 구분)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# {book_title} - NotebookLM 소스 URL\n\n")
            if author:
                f.write(f"**책**: {book_title}  \n")
                f.write(f"**저자**: {author}  \n")
            f.write(f"**총 {len(total_urls)}개의 URL (한글 {len(ko_urls)}개 + 영어 {len(en_urls)}개)**\n\n")
            f.write("> ✅ **한글/영어 자료 반반 수집**: 한글 자료와 영어 자료를 균형있게 수집했습니다.  \n")
            f.write("> ✅ **다양한 소스**: 위키백과, 온라인 서점, 뉴스 리뷰, YouTube 영상 등 다양한 출처를 포함했습니다.\n\n")
            
            f.write("## 📋 URL 리스트\n\n")
            f.write("아래 URL들을 복사하여 NotebookLM에 소스로 추가하세요.\n\n")
            
            # 한글 섹션
            f.write("### 📚 한글 자료\n\n")
            f.write("```\n")
            for url in ko_urls:
                f.write(f"{url}\n")
            f.write("```\n\n")
            
            # 영어 섹션
            f.write("### 📚 English Resources\n\n")
            f.write("```\n")
            for url in en_urls:
                f.write(f"{url}\n")
            f.write("```\n\n")
            
            # 전체 URL (복사용)
            f.write("### 📋 전체 URL (복사용)\n\n")
            f.write("```\n")
            for url in total_urls:
                f.write(f"{url}\n")
            f.write("```\n\n")
            
            f.write("## 📝 사용 방법\n\n")
            f.write("1. 위 URL 블록을 전체 선택 (Cmd+A / Ctrl+A)\n")
            f.write("2. 복사 (Cmd+C / Ctrl+C)\n")
            f.write("3. NotebookLM에서 '소스 추가' > 'URL' 선택\n")
            f.write("4. 붙여넣기 (각 URL이 자동으로 인식됩니다)\n\n")
            f.write("💡 **팁**: 한글 자료와 영어 자료를 모두 포함하면 더 풍부한 콘텐츠를 생성할 수 있습니다.\n\n")
        
        print(f"\n💾 URL 데이터를 저장했습니다:")
        print(f"   - MD (NotebookLM 복사용): {md_path}")
        
        return {'md_path': str(md_path)}
    
    def save_urls(self, book_title: str, urls: List[str], validate: bool = False) -> Dict[str, str]:
        """
        URL을 파일로 저장 (마크다운 형식 포함) - 기존 메서드 (하위 호환성)
        
        Args:
            book_title: 책 제목
            urls: URL 리스트
            validate: URL 유효성 검증 여부
        """
        safe_title = "".join(c for c in book_title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')
        
        output_dir = Path("assets/urls")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        md_path = output_dir / f"{safe_title}_notebooklm.md"
        
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
        
        print(f"\n💾 URL 데이터를 저장했습니다:")
        print(f"   - MD (NotebookLM 복사용): {md_path}")
        
        return {'md_path': str(md_path)}


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NotebookLM용 URL 수집 (한글/영어 반반)')
    parser.add_argument('--title', type=str, help='책 제목 (한글)')
    parser.add_argument('--author', type=str, help='저자 이름')
    parser.add_argument('--en-title', type=str, help='책 제목 (영어, 선택사항 - 자동 번역 시도)')
    parser.add_argument('--num', type=int, default=30, help='총 수집할 URL 개수 (기본값: 30, 한글/영어 반반)')
    parser.add_argument('--validate', action='store_true', help='URL 유효성 검증 수행')
    parser.add_argument('--bilingual', action='store_true', default=True, help='한글/영어 반반 수집 (기본값: True)')
    
    args = parser.parse_args()
    
    collector = NotebookLMURLCollector()
    
    if args.title:
        book_title = args.title
        author = args.author
        en_title = args.en_title
    else:
        # 인터랙티브 모드
        print("=" * 60)
        print("📚 NotebookLM용 URL 수집기 (한글/영어 반반)")
        print("=" * 60)
        print()
        
        book_title = input("책 제목을 입력하세요 (한글): ").strip()
        if not book_title:
            print("❌ 책 제목을 입력해주세요.")
            return
        
        author = input("저자 이름을 입력하세요 (선택사항): ").strip() or None
        en_title = input("책 제목 (영어, 선택사항 - 자동 번역 시도): ").strip() or None
        num_results = input("총 수집할 URL 개수 (기본값: 30, 한글/영어 반반): ").strip()
        args.num = int(num_results) if num_results.isdigit() else 30
        args.validate = input("URL 유효성 검증을 수행하시겠습니까? (y/n, 기본값: n): ").strip().lower() == 'y'
        args.bilingual = input("한글/영어 반반 수집하시겠습니까? (y/n, 기본값: y): ").strip().lower() != 'n'
    
    print()
    
    # URL 수집
    if args.bilingual:
        # 한글/영어 반반 수집
        en_title = args.en_title if hasattr(args, 'en_title') and args.en_title else None
        ko_urls, en_urls = collector.search_urls_bilingual(book_title, author, args.num, en_title=en_title)
        
        if ko_urls or en_urls:
            # URL 저장
            result = collector.save_urls_bilingual(
                book_title, 
                ko_urls, 
                en_urls, 
                author=author,
                validate=args.validate
            )
            
            print()
            print("=" * 60)
            print("✅ URL 수집 완료!")
            print("=" * 60)
            print(f"\n📄 NotebookLM용 파일: {result['md_path']}")
            print(f"\n💡 다음 단계:")
            print(f"   1. {result['md_path']} 파일을 엽니다")
            print(f"   2. '전체 URL (복사용)' 섹션의 URL들을 복사합니다")
            print(f"   3. NotebookLM (https://notebooklm.google.com)에 접속합니다")
            print(f"   4. 새 소스 추가 > URL에서 붙여넣기합니다")
            print(f"\n📊 수집 결과:")
            print(f"   - 한글 자료: {len(ko_urls)}개")
            print(f"   - 영어 자료: {len(en_urls)}개")
            print(f"   - 총계: {len(ko_urls) + len(en_urls)}개")
            print()
        else:
            print("❌ 수집된 URL이 없습니다.")
    else:
        # 기존 방식 (한글만)
        urls = collector.search_urls(book_title, author, args.num)
        
        if urls:
            # URL 저장
            result = collector.save_urls(book_title, urls, validate=args.validate)
            
            print()
            print("=" * 60)
            print("✅ URL 수집 완료!")
            print("=" * 60)
            print(f"\n📄 NotebookLM용 파일: {result['md_path']}")
            print(f"\n💡 다음 단계:")
            print(f"   1. {result['md_path']} 파일을 엽니다")
            print(f"   2. URL들을 복사합니다")
            print(f"   3. NotebookLM (https://notebooklm.google.com)에 접속합니다")
            print(f"   4. 새 소스 추가 > URL에서 붙여넣기합니다")
            print()
        else:
            print("❌ 수집된 URL이 없습니다.")


if __name__ == "__main__":
    main()

