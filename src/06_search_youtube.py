"""
GPT/Claude API를 사용하여 YouTube 영상 검색 및 URL 수집 스크립트
"""

import os
import json
from typing import List, Dict
from pathlib import Path
from dotenv import load_dotenv

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False

load_dotenv()


class YouTubeSearcher:
    """GPT/Claude API를 사용한 YouTube 영상 검색 클래스"""
    
    def __init__(self, use_claude: bool = True):
        """
        Args:
            use_claude: Claude API 사용 여부 (False면 OpenAI GPT 사용)
        """
        self.use_claude = use_claude
        
        # API 키 로드
        if use_claude and ANTHROPIC_AVAILABLE:
            self.claude_api_key = os.getenv("CLAUDE_API_KEY")
            if self.claude_api_key:
                self.claude_client = anthropic.Anthropic(api_key=self.claude_api_key)
            else:
                self.claude_client = None
        else:
            self.claude_client = None
        
        if not use_claude and OPENAI_AVAILABLE:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
            if self.openai_api_key:
                openai.api_key = self.openai_api_key
            else:
                self.openai_api_key = None
        else:
            self.openai_api_key = None
        
        # YouTube API 설정
        # YouTube Data API v3 키 필요 (Google Cloud Console에서 발급)
        # 참고: YOUTUBE_CLIENT_ID는 OAuth용이고, YOUTUBE_API_KEY는 Data API용입니다
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY") or os.getenv("GOOGLE_BOOKS_API_KEY")  # 임시로 Google Books API 키 사용 가능
        
        self.youtube = None
        if YOUTUBE_API_AVAILABLE and self.youtube_api_key:
            try:
                self.youtube = build('youtube', 'v3', developerKey=self.youtube_api_key)
            except Exception as e:
                print(f"⚠️ YouTube API 초기화 실패: {e}")
    
    def generate_search_queries(self, book_title: str, author: str = None) -> List[str]:
        """
        GPT/Claude API를 사용하여 YouTube 검색 쿼리 생성
        
        Args:
            book_title: 책 제목
            author: 저자 이름
            
        Returns:
            검색 쿼리 리스트
        """
        query_info = f"책 제목: {book_title}"
        if author:
            query_info += f", 저자: {author}"
        
        prompt = f"""다음 책에 대한 YouTube 영상 검색을 위한 검색 쿼리를 생성해주세요.

{query_info}

다음과 같은 유형의 검색 쿼리를 15-20개 생성해주세요:
1. 책 리뷰/서평
2. 작가 인터뷰
3. 책 해석/분석
4. 독서 후기/감상평
5. 줄거리 요약
6. 주요 장면/명대사
7. 팟캐스트/강의
8. 관련 영화/드라마 (있는 경우)

각 검색 쿼리는 한글로 작성하고, YouTube에서 실제로 검색 가능한 구체적인 키워드를 사용해주세요.
검색 쿼리만 한 줄에 하나씩 나열해주세요. 설명이나 번호는 필요 없습니다."""

        try:
            if self.use_claude and self.claude_client:
                response = self.claude_client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=1000,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                queries_text = response.content[0].text
            elif self.openai_api_key:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that generates YouTube search queries."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000
                )
                queries_text = response.choices[0].message.content
            else:
                print("⚠️ API 키가 설정되지 않았습니다. 기본 검색 쿼리를 사용합니다.")
                return self._default_search_queries(book_title, author)
            
            # 쿼리 파싱
            queries = []
            for line in queries_text.strip().split('\n'):
                line = line.strip()
                # 번호나 불필요한 문자 제거
                if line and not line.startswith('#') and not line.startswith('-'):
                    # 번호 제거 (1. 2. 등)
                    line = line.lstrip('0123456789. ')
                    if line:
                        queries.append(line)
            
            if not queries:
                return self._default_search_queries(book_title, author)
            
            print(f"✅ {len(queries)}개의 검색 쿼리를 생성했습니다.\n")
            return queries[:20]  # 최대 20개
            
        except Exception as e:
            print(f"⚠️ API 호출 실패: {e}")
            print("기본 검색 쿼리를 사용합니다.\n")
            return self._default_search_queries(book_title, author)
    
    def _default_search_queries(self, book_title: str, author: str = None) -> List[str]:
        """기본 검색 쿼리 생성"""
        queries = [
            f"{book_title} 리뷰",
            f"{book_title} 서평",
            f"{book_title} 해석",
            f"{book_title} 분석",
            f"{book_title} 독서 후기",
            f"{book_title} 줄거리",
            f"{book_title} 명대사",
            f"{book_title} 팟캐스트",
            f"{book_title} 강의",
        ]
        
        if author:
            queries.extend([
                f"{author} 인터뷰",
                f"{author} {book_title}",
                f"{book_title} {author} 리뷰",
            ])
        
        return queries
    
    def is_related_to_book(self, title: str, description: str, book_title: str, author: str = None) -> bool:
        """
        영상이 해당 책과 관련이 있는지 확인
        
        Args:
            title: 영상 제목
            description: 영상 설명
            book_title: 책 제목
            author: 저자 이름
            
        Returns:
            관련 여부
        """
        text = (title + " " + description).lower()
        book_title_lower = book_title.lower()
        
        # 책 제목이 포함되어 있는지 확인
        if book_title_lower in text:
            return True
        
        # 저자가 있으면 저자 이름도 확인
        if author:
            author_lower = author.lower()
            # 저자 이름의 주요 부분만 추출 (예: "무라카미 하루키" -> "무라카미", "하루키")
            author_parts = author_lower.split()
            if len(author_parts) > 0 and any(part in text for part in author_parts if len(part) > 2):
                return True
        
        return False
    
    def search_youtube_videos(self, queries: List[str], book_title: str, author: str = None, max_results_per_query: int = 3) -> List[Dict]:
        """
        YouTube Data API를 사용하여 영상 검색
        
        Args:
            queries: 검색 쿼리 리스트
            book_title: 책 제목 (관련성 검증용)
            author: 저자 이름 (관련성 검증용)
            max_results_per_query: 쿼리당 최대 결과 수
            
        Returns:
            영상 정보 리스트
        """
        if not self.youtube:
            print("⚠️ YouTube API가 설정되지 않았습니다.")
            print("   .env 파일에 YOUTUBE_API_KEY를 추가하세요.")
            return []
        
        all_videos = []
        seen_video_ids = set()
        
        print(f"🔍 YouTube 영상 검색 중... (총 {len(queries)}개 쿼리)\n")
        
        for i, query in enumerate(queries, 1):
            try:
                print(f"  [{i}/{len(queries)}] 검색: {query}")
                
                # YouTube API 검색
                search_response = self.youtube.search().list(
                    q=query,
                    part='id,snippet',
                    type='video',
                    maxResults=max_results_per_query,
                    order='relevance',
                    regionCode='KR'
                ).execute()
                
                for item in search_response.get('items', []):
                    video_id = item['id']['videoId']
                    
                    if video_id not in seen_video_ids:
                        seen_video_ids.add(video_id)
                        
                        video_title = item['snippet']['title']
                        video_description = item['snippet']['description']
                        
                        # 책과 관련이 있는지 확인
                        if not self.is_related_to_book(video_title, video_description, book_title, author):
                            print(f"    ⏭️ 관련 없음: {video_title[:50]}...")
                            continue
                        
                        video_info = {
                            'video_id': video_id,
                            'url': f"https://www.youtube.com/watch?v={video_id}",
                            'title': video_title,
                            'channel': item['snippet']['channelTitle'],
                            'published_at': item['snippet']['publishedAt'],
                            'description': video_description[:200] + '...' if len(video_description) > 200 else video_description,
                            'search_query': query
                        }
                        
                        all_videos.append(video_info)
                        print(f"    ✓ {video_info['title'][:50]}...")
                
            except Exception as e:
                print(f"    ⚠️ 검색 오류: {e}")
                continue
        
        print(f"\n✅ 총 {len(all_videos)}개의 관련 YouTube 영상을 찾았습니다.\n")
        return all_videos
    
    def validate_web_url(self, url: str, book_title: str) -> bool:
        """
        웹사이트 URL이 해당 책과 관련이 있는지 확인
        
        Args:
            url: URL
            book_title: 책 제목
            
        Returns:
            관련 여부
        """
        # 다른 책 제목이 포함된 URL 제외
        # 예: "82년생 김지영"이 "노르웨이의 숲" 파일에 들어오면 안 됨
        unrelated_books = [
            "82년생 김지영", "김지영", "조남주",
            # 다른 책 제목들도 추가 가능
        ]
        
        url_lower = url.lower()
        book_title_lower = book_title.lower()
        
        # 다른 책 제목이 포함되어 있으면 제외
        for unrelated in unrelated_books:
            if unrelated.lower() in url_lower and unrelated.lower() not in book_title_lower:
                return False
        
        return True
    
    def save_video_urls(self, book_title: str, videos: List[Dict], output_file: str = None) -> str:
        """
        YouTube 영상 URL을 마크다운 파일에 추가
        
        Args:
            book_title: 책 제목
            videos: 영상 정보 리스트
            output_file: 출력 파일 경로 (None이면 자동 생성)
            
        Returns:
            저장된 파일 경로
        """
        if output_file is None:
            safe_title = "".join(c for c in book_title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_')
            output_file = f"assets/urls/{safe_title}_notebooklm.md"
        
        output_path = Path(output_file)
        
        # 기존 파일 읽기
        existing_urls = []
        if output_path.exists():
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 기존 URL 추출 및 검증
                for line in content.split('\n'):
                    if line.startswith('https://'):
                        url = line.strip()
                        # 해당 책과 관련이 있는 URL만 유지
                        if self.validate_web_url(url, book_title):
                            existing_urls.append(url)
                        else:
                            print(f"  ⚠️ 관련 없는 URL 제거: {url[:60]}...")
        
        # 새 YouTube URL 추가
        new_urls = [video['url'] for video in videos]
        all_urls = existing_urls + new_urls
        
        # 중복 제거
        unique_urls = []
        seen = set()
        for url in all_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        # 파일 업데이트
        if output_path.exists():
            # 기존 파일의 URL 블록 찾아서 교체
            with open(output_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # URL 블록 시작/끝 찾기
            start_idx = None
            end_idx = None
            
            for i, line in enumerate(lines):
                if '```' in line and start_idx is None:
                    start_idx = i + 1
                elif start_idx is not None and '```' in line:
                    end_idx = i
                    break
            
            if start_idx is not None and end_idx is not None:
                # URL 블록 교체
                new_lines = lines[:start_idx] + [url + '\n' for url in unique_urls] + lines[end_idx:]
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
            else:
                # URL 블록이 없으면 추가
                with open(output_path, 'a', encoding='utf-8') as f:
                    f.write('\n')
                    for url in new_urls:
                        f.write(f"{url}\n")
        else:
            # 새 파일 생성
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"# {book_title} - NotebookLM 소스 URL\n\n")
                f.write("## 📋 URL 리스트\n\n```\n")
                for url in unique_urls:
                    f.write(f"{url}\n")
                f.write("```\n")
        
        print(f"💾 YouTube 영상 URL을 저장했습니다: {output_path}")
        print(f"   - 새로 추가된 영상: {len(new_urls)}개")
        print(f"   - 총 URL: {len(unique_urls)}개\n")
        
        return str(output_path)


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GPT/Claude API를 사용한 YouTube 영상 검색')
    parser.add_argument('--title', type=str, required=True, help='책 제목')
    parser.add_argument('--author', type=str, help='저자 이름')
    parser.add_argument('--use-openai', action='store_true', help='OpenAI GPT 사용 (기본값: Claude)')
    parser.add_argument('--max-results', type=int, default=3, help='쿼리당 최대 결과 수')
    parser.add_argument('--output', type=str, help='출력 파일 경로')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎬 GPT/Claude API를 사용한 YouTube 영상 검색")
    print("=" * 60)
    print()
    
    searcher = YouTubeSearcher(use_claude=not args.use_openai)
    
    # 검색 쿼리 생성
    print("🤖 AI를 사용하여 검색 쿼리 생성 중...")
    queries = searcher.generate_search_queries(args.title, args.author)
    
    if not queries:
        print("❌ 검색 쿼리를 생성할 수 없습니다.")
        return
    
    print(f"생성된 검색 쿼리 ({len(queries)}개):")
    for i, query in enumerate(queries, 1):
        print(f"  {i}. {query}")
    print()
    
    # YouTube 영상 검색
    videos = searcher.search_youtube_videos(queries, args.title, args.author, max_results_per_query=args.max_results)
    
    if not videos:
        print("❌ YouTube 영상을 찾을 수 없습니다.")
        print("   .env 파일에 YOUTUBE_API_KEY를 추가하세요.")
        return
    
    # URL 저장
    output_file = searcher.save_video_urls(args.title, videos, args.output)
    
    print("=" * 60)
    print("✅ 완료!")
    print("=" * 60)
    print(f"\n📄 저장된 파일: {output_file}")
    print(f"📺 찾은 영상: {len(videos)}개")
    print("\n💡 이제 마크다운 파일의 URL을 NotebookLM에 복사하세요!")


if __name__ == "__main__":
    main()

