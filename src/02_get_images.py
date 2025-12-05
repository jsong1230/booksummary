"""
책 표지 및 무드 이미지 다운로드 스크립트
- Google Books API로 책 표지 다운로드
- Unsplash/Pexels API로 무드 이미지 다운로드 (5~10장)
"""

import os
import json
import time
import requests
from pathlib import Path
from typing import List, Dict, Optional
import concurrent.futures
from dotenv import load_dotenv
from utils.retry_utils import retry_with_backoff

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
    GOOGLE_BOOKS_AVAILABLE = True
except ImportError:
    GOOGLE_BOOKS_AVAILABLE = False

try:
    from pexels_api import API as PexelsAPI
    PEXELS_AVAILABLE = True
except ImportError:
    PEXELS_AVAILABLE = False

load_dotenv()


class ImageDownloader:
    """이미지 다운로드 클래스"""
    
    def __init__(self):
        # API 키 로드
        self.google_books_api_key = os.getenv("GOOGLE_BOOKS_API_KEY")
        self.pexels_api_key = os.getenv("PEXELS_API_KEY")
        self.unsplash_access_key = os.getenv("UNSPLASH_ACCESS_KEY")
        self.pixabay_api_key = os.getenv("PIXABAY_API_KEY")
        
        # Google Books API 초기화
        self.books_service = None
        if GOOGLE_BOOKS_AVAILABLE and self.google_books_api_key:
            try:
                self.books_service = build('books', 'v1', developerKey=self.google_books_api_key)
            except Exception as e:
                print(f"⚠️ Google Books API 초기화 실패: {e}")
        
        # Pexels API 초기화
        self.pexels = None
        if PEXELS_AVAILABLE and self.pexels_api_key:
            try:
                self.pexels = PexelsAPI(self.pexels_api_key)
            except Exception as e:
                print(f"⚠️ Pexels API 초기화 실패: {e}")
        
        # AI API 키 로드
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.claude_api_key = os.getenv("CLAUDE_API_KEY")
    
    @retry_with_backoff(retries=3, backoff_in_seconds=1.0)
    def _download_single_image(self, url: str, output_path: Path) -> str:
        """단일 이미지 다운로드 (병렬 처리용)"""
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        return str(output_path)

    @retry_with_backoff(retries=3, backoff_in_seconds=2.0)
    def _make_request(self, url: str, headers: Dict = None, params: Dict = None) -> Dict:
        """API 요청 수행 (재시도 로직 포함)"""
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    @retry_with_backoff(retries=3, backoff_in_seconds=2.0)
    def _search_pexels(self, keyword: str, page: int, results_per_page: int) -> Dict:
        """Pexels 검색 수행 (재시도 로직 포함)"""
        if not self.pexels:
            raise ValueError("Pexels API not initialized")
        return self.pexels.search(keyword, page=page, results_per_page=results_per_page)
    
    def download_book_cover(self, book_title: str, author: str = None, output_dir: Path = None, skip_image: bool = False) -> Optional[str]:
        """
        Google Books API로 책 표지 다운로드 및 book_info.json 생성
        
        ⚠️ 주의: 책 표지 이미지는 저작권이 있어 YouTube 등에 사용 시 문제가 될 수 있습니다.
        표지 이미지는 참고용으로만 다운로드하며, 실제 영상 제작에는 사용하지 않습니다.
        
        Args:
            book_title: 책 제목
            author: 저자 이름
            output_dir: 저장 디렉토리
            skip_image: 이미지 다운로드는 건너뛰고 book_info.json만 생성
            
        Returns:
            다운로드된 파일 경로 (skip_image=True면 None)
        """
        if not self.books_service:
            print("⚠️ Google Books API가 설정되지 않았습니다.")
            return None
        
        print(f"📚 책 표지 검색 중: {book_title}")
        if author:
            print(f"   저자: {author}")
        
        try:
            # 검색 쿼리 구성 (저자 포함하여 정확도 향상)
            query = f'intitle:"{book_title}"'
            if author:
                query += f' inauthor:"{author}"'
            
            # 언어 감지: 제목에 한글이 있으면 한국어, 없으면 영어로 검색
            has_korean = any('\uAC00' <= c <= '\uD7A3' for c in book_title)
            lang_restrict = 'ko' if has_korean else 'en'
            
            print(f"   검색 언어: {lang_restrict}")
            
            # Google Books API 검색
            results = self.books_service.volumes().list(
                q=query,
                maxResults=10,  # 더 많은 결과 확인
                langRestrict=lang_restrict
            ).execute()
            
            if not results.get('items'):
                # 언어 제한 없이 재시도
                print("  ⚠️ 언어 제한 검색 결과가 없습니다. 언어 제한 없이 재시도...")
                results = self.books_service.volumes().list(
                    q=query,
                    maxResults=10
                ).execute()
            
            if not results.get('items'):
                print("  ⚠️ 검색 결과가 없습니다.")
                return None
            
            # 가장 관련성 높은 결과 선택 (저자명도 확인)
            best_book = None
            for book in results['items']:
                volume_info = book.get('volumeInfo', {})
                book_authors = volume_info.get('authors', [])
                book_title_found = volume_info.get('title', '').lower()
                
                # 저자명이 일치하는지 확인
                author_match = False
                if author:
                    author_lower = author.lower()
                    for book_author in book_authors:
                        if author_lower in book_author.lower() or book_author.lower() in author_lower:
                            author_match = True
                            break
                else:
                    author_match = True  # 저자 정보가 없으면 모든 결과 허용
                
                # 제목도 비슷한지 확인
                title_match = book_title.lower() in book_title_found or book_title_found in book_title.lower()
                
                if author_match and title_match:
                    best_book = book
                    print(f"  ✅ 매칭된 책 발견: {volume_info.get('title')} - {', '.join(book_authors)}")
                    break
            
            if not best_book:
                # 매칭되는 게 없으면 첫 번째 결과 사용
                print("  ⚠️ 정확한 매칭을 찾지 못했습니다. 첫 번째 결과를 사용합니다.")
                best_book = results['items'][0]
            
            book = best_book
            volume_info = book.get('volumeInfo', {})
            
            # 저장 경로
            if output_dir is None:
                from utils.file_utils import safe_title
                safe_title_str = safe_title(book_title)
                output_dir = Path("assets/images") / safe_title_str
            else:
                output_dir = Path(output_dir)
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 이미지 다운로드 (skip_image가 False인 경우만)
            image_url = None
            output_path = None
            if not skip_image:
                # 이미지 링크 찾기
                image_links = volume_info.get('imageLinks', {})
                if not image_links:
                    print("  ⚠️ 표지 이미지를 찾을 수 없습니다.")
                else:
                    # 가장 큰 이미지 선택
                    image_url = image_links.get('large') or image_links.get('medium') or image_links.get('small') or image_links.get('thumbnail')
                    
                    if image_url:
                        try:
                            # 이미지 다운로드
                            response = requests.get(image_url, timeout=10)
                            response.raise_for_status()
                            
                            output_path = output_dir / "cover.jpg"
                            
                            # 파일 저장
                            with open(output_path, 'wb') as f:
                                f.write(response.content)
                            
                            print(f"  ✅ 표지 다운로드 완료: {output_path}")
                        except Exception as e:
                            print(f"  ⚠️ 이미지 다운로드 실패: {e}")
                            image_url = None
                    else:
                        print("  ⚠️ 이미지 URL을 찾을 수 없습니다.")
            else:
                # skip_image=True인 경우에도 image_url은 book_info에 포함하기 위해 가져오기
                image_links = volume_info.get('imageLinks', {})
                if image_links:
                    image_url = image_links.get('large') or image_links.get('medium') or image_links.get('small') or image_links.get('thumbnail')
                print("  ℹ️ 이미지 다운로드는 건너뛰고 책 정보만 저장합니다.")
            
            # 책 정보 저장 (이미지 다운로드 여부와 관계없이 항상 저장)
            book_info = {
                'title': volume_info.get('title', book_title),
                'authors': volume_info.get('authors', [author] if author else []),
                'publisher': volume_info.get('publisher', ''),
                'publishedDate': volume_info.get('publishedDate', ''),
                'description': volume_info.get('description', ''),
                'pageCount': volume_info.get('pageCount', 0),
                'categories': volume_info.get('categories', []),
                'language': volume_info.get('language', 'ko'),
                'google_books_id': book.get('id', ''),
                'image_url': image_url if image_url else ''
            }
            
            book_info_path = output_dir / "book_info.json"
            with open(book_info_path, 'w', encoding='utf-8') as f:
                json.dump(book_info, f, ensure_ascii=False, indent=2)
            
            print(f"  ✅ 책 정보 저장 완료: {book_info_path}")
            
            return str(output_path) if output_path else None
            
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            return None
    
    @retry_with_backoff(retries=3, backoff_in_seconds=2.0)
    def download_mood_images_unsplash(self, keywords: List[str], num_images: int = 100, output_dir: Path = None) -> List[str]:
        """
        Unsplash API로 무드 이미지 다운로드
        
        Args:
            keywords: 검색 키워드 리스트
            num_images: 다운로드할 이미지 개수
            output_dir: 저장 디렉토리
            
        Returns:
            다운로드된 파일 경로 리스트
        """
        if not self.unsplash_access_key:
            print("⚠️ Unsplash API 키가 설정되지 않았습니다.")
            return []
        
        downloaded = []
        # 각 키워드에서 가져올 최대 이미지 수 (다양성을 위해 제한)
        max_per_keyword = max(2, num_images // len(keywords)) if keywords else 2
        
        # 다운로드 작업 리스트
        download_tasks = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            for keyword in keywords:
                if len(downloaded) + len(download_tasks) >= num_images:
                    break
                
                try:
                    print(f"  🔍 검색: {keyword}")
                    
                    # Unsplash API 검색
                    url = "https://api.unsplash.com/search/photos"
                    headers = {
                        "Authorization": f"Client-ID {self.unsplash_access_key}"
                    }
                    # 각 키워드에서 최대 max_per_keyword개만 가져오기
                    remaining = num_images - (len(downloaded) + len(download_tasks))
                    params = {
                        "query": keyword,
                        "per_page": min(max_per_keyword, remaining, 15),  # 더 많은 이미지 수집 (100개 목표)
                        "orientation": "landscape"
                    }
                    
                    data = self._make_request(url, headers=headers, params=params)
                    results = data.get('results', [])
                    
                    if not results:
                        print(f"    ⚠️ 검색 결과 없음")
                        continue
                    
                    for photo in results:
                        if len(downloaded) + len(download_tasks) >= num_images:
                            break
                        
                        # 고화질 이미지 URL
                        image_url = photo['urls'].get('regular') or photo['urls'].get('full')
                        
                        if not image_url:
                            continue
                        
                        # 저장 경로 설정
                        filename = f"mood_{len(downloaded) + len(download_tasks) + 1:02d}_{keyword.replace(' ', '_')}.jpg"
                        output_path = output_dir / filename
                        
                        # 병렬 다운로드 작업 추가
                        future = executor.submit(self._download_single_image, image_url, output_path)
                        download_tasks.append((future, filename))
                        
                        time.sleep(0.1)  # API rate limit 방지 (최소한의 지연)
                    
                except Exception as e:
                    print(f"    ❌ 오류: {e}")
                    continue
            
            # 결과 수집
            for future, filename in download_tasks:
                try:
                    result = future.result()
                    if result:
                        downloaded.append(result)
                        print(f"    ✅ {filename}")
                except Exception as e:
                    print(f"    ❌ 이미지 다운로드 실패 ({filename}): {e}")
        
        return downloaded
    
    @retry_with_backoff(retries=3, backoff_in_seconds=2.0)
    def download_mood_images_pexels(self, keywords: List[str], num_images: int = 100, output_dir: Path = None) -> List[str]:
        """
        Pexels API로 무드 이미지 다운로드
        
        Args:
            keywords: 검색 키워드 리스트
            num_images: 다운로드할 이미지 개수
            output_dir: 저장 디렉토리
            
        Returns:
            다운로드된 파일 경로 리스트
        """
        if not self.pexels:
            print("⚠️ Pexels API가 설정되지 않았습니다.")
            return []
        
        downloaded = []
        download_tasks = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            for keyword in keywords:
                if len(downloaded) + len(download_tasks) >= num_images:
                    break
                
                try:
                    print(f"  🔍 검색: {keyword}")
                    
                    # Pexels API 검색
                    try:
                        remaining = num_images - (len(downloaded) + len(download_tasks))
                        search_results = self._search_pexels(keyword, page=1, results_per_page=min(15, remaining))
                    except Exception as e:
                        print(f"    ❌ Pexels 검색 오류: {e}")
                        continue
                    
                    if not search_results.get('photos'):
                        print(f"    ⚠️ 검색 결과 없음")
                        continue
                    
                    for photo in search_results['photos']:
                        if len(downloaded) + len(download_tasks) >= num_images:
                            break
                        
                        # 고화질 이미지 URL
                        image_url = photo.get('src', {}).get('large') or photo.get('src', {}).get('original')
                        
                        if not image_url:
                            continue
                        
                        # 저장 경로 설정
                        filename = f"mood_{len(downloaded) + len(download_tasks) + 1:02d}_{keyword.replace(' ', '_')}.jpg"
                        output_path = output_dir / filename
                        
                        # 병렬 다운로드 작업 추가
                        future = executor.submit(self._download_single_image, image_url, output_path)
                        download_tasks.append((future, filename))
                        
                        time.sleep(0.1)  # API rate limit 방지
                    
                except Exception as e:
                    print(f"    ❌ 오류: {e}")
                    continue
            
            # 결과 수집
            for future, filename in download_tasks:
                try:
                    result = future.result()
                    if result:
                        downloaded.append(result)
                        print(f"    ✅ {filename}")
                except Exception as e:
                    print(f"    ❌ 이미지 다운로드 실패 ({filename}): {e}")
        
        return downloaded
    
    @retry_with_backoff(retries=3, backoff_in_seconds=2.0)
    def download_mood_images_pixabay(self, keywords: List[str], num_images: int = 100, output_dir: Path = None) -> List[str]:
        """
        Pixabay API로 무드 이미지 다운로드
        
        Args:
            keywords: 검색 키워드 리스트
            num_images: 다운로드할 이미지 개수
            output_dir: 저장 디렉토리
            
        Returns:
            다운로드된 파일 경로 리스트
        """
        if not self.pixabay_api_key:
            print("⚠️ Pixabay API 키가 설정되지 않았습니다.")
            return []
        
        downloaded = []
        base_url = "https://pixabay.com/api/"
        download_tasks = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            for keyword in keywords:
                if len(downloaded) + len(download_tasks) >= num_images:
                    break
                
                try:
                    print(f"  🔍 검색: {keyword}")
                    
                    # Pixabay API 검색
                    params = {
                        'key': self.pixabay_api_key,
                        'q': keyword,
                        'image_type': 'photo',
                        'orientation': 'horizontal',
                        'safesearch': 'true',
                        'per_page': min(20, num_images - (len(downloaded) + len(download_tasks)))
                    }
                    
                    data = self._make_request(base_url, params=params)
                    hits = data.get('hits', [])
                    
                    if not hits:
                        print(f"    ⚠️ 검색 결과 없음")
                        continue
                    
                    for hit in hits:
                        if len(downloaded) + len(download_tasks) >= num_images:
                            break
                        
                        # 고화질 이미지 URL (largeImageURL 우선, 없으면 webformatURL)
                        image_url = hit.get('largeImageURL') or hit.get('webformatURL')
                        
                        if not image_url:
                            continue
                        
                        # 저장 경로 설정
                        filename = f"mood_{len(downloaded) + len(download_tasks) + 1:02d}_{keyword.replace(' ', '_')}.jpg"
                        output_path = output_dir / filename
                        
                        # 병렬 다운로드 작업 추가
                        future = executor.submit(self._download_single_image, image_url, output_path)
                        download_tasks.append((future, filename))
                        
                        time.sleep(0.1)  # API rate limit 방지
                    
                except Exception as e:
                    print(f"    ❌ 오류: {e}")
                    continue
            
            # 결과 수집
            for future, filename in download_tasks:
                try:
                    result = future.result()
                    if result:
                        downloaded.append(result)
                        print(f"    ✅ {filename}")
                except Exception as e:
                    print(f"    ❌ 이미지 다운로드 실패 ({filename}): {e}")
        
        return downloaded
    
    def download_all(self, book_title: str, author: str = None, keywords: List[str] = None, num_mood_images: int = 100, skip_cover: bool = False) -> Dict:
        """
        책 표지와 무드 이미지 모두 다운로드
        
        Args:
            book_title: 책 제목
            author: 저자 이름
            keywords: 무드 이미지 검색 키워드 (None이면 자동 생성)
            num_mood_images: 무드 이미지 개수
            
        Returns:
            다운로드 결과 딕셔너리
        """
        print("=" * 60)
        print("🖼️ 이미지 다운로드 시작")
        print("=" * 60)
        print()
        
        # 출력 디렉토리 설정
        from utils.file_utils import safe_title
        safe_title_str = safe_title(book_title)
        output_dir = Path("assets/images") / safe_title_str
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. 책 표지 다운로드 및 book_info.json 생성 (선택사항)
        # ⚠️ 주의: 책 표지는 저작권이 있어 영상에 사용하지 않습니다.
        # 표지는 참고용으로만 다운로드하며, 실제 영상에는 저작권 없는 무드 이미지만 사용합니다.
        # skip_cover=True여도 book_info.json은 생성합니다.
        cover_path = None
        if skip_cover:
            print("ℹ️ 책 표지 이미지 다운로드는 건너뛰지만, 책 정보(book_info.json)는 생성합니다.")
            self.download_book_cover(book_title, author, output_dir, skip_image=True)
            print()
        else:
            print("⚠️ 책 표지 이미지는 저작권 문제로 영상에 사용하지 않습니다.")
            print("   표지는 참고용으로만 다운로드합니다.")
            cover_path = self.download_book_cover(book_title, author, output_dir, skip_image=False)
            print()
        
        # 2. 키워드 생성 (없으면) - AI를 사용하여 책 내용 기반 키워드 생성
        if keywords is None:
            print("📝 AI를 사용하여 책 내용 기반 이미지 검색 키워드 생성 중...")
            keywords = self.generate_keywords_with_ai(book_title, author, output_dir)
            print(f"   ✅ 생성된 키워드: {', '.join(keywords[:10])}")
            print()
        
        print(f"🎨 무드 이미지 다운로드 중... (키워드: {', '.join(keywords)})")
        print()
        
        # 3. 무드 이미지 다운로드 (Pexels → Pixabay → Unsplash 순서)
        # 기존 이미지 확인
        existing_images = list(output_dir.glob("mood_*.jpg"))
        existing_count = len(existing_images)
        
        if existing_count >= num_mood_images:
            print(f"✅ 기존 이미지 발견: {existing_count}개 (목표: {num_mood_images}개)")
            print(f"   이미지 다운로드를 건너뜁니다.")
            print()
            return {
                'cover_path': str(cover_path) if cover_path else None,
                'mood_images': [str(img) for img in existing_images[:num_mood_images]],
                'total_mood_images': existing_count
            }
        
        print(f"📊 기존 이미지: {existing_count}개, 추가로 {num_mood_images - existing_count}개 필요")
        print()
        
        # 100개 이미지를 확실히 다운로드하기 위해 여러 키워드에서 충분히 수집
        mood_images = existing_images.copy()  # 기존 이미지 포함
        target_count = num_mood_images
        
        # Pexels에서 다운로드 (1순위)
        if len(mood_images) < target_count and self.pexels:
            remaining = target_count - len(mood_images)
            print(f"  📸 Pexels에서 이미지 다운로드 중... (목표: {remaining}개)")
            additional = self.download_mood_images_pexels(keywords, remaining, output_dir)
            mood_images.extend(additional)
            print(f"  ✅ Pexels: {len(additional)}개 다운로드 완료")
        
        # Pixabay에서 추가 다운로드 (2순위)
        if len(mood_images) < target_count and self.pixabay_api_key:
            remaining = target_count - len(mood_images)
            print(f"  📸 Pixabay에서 추가 이미지 다운로드 중... (목표: {remaining}개)")
            additional = self.download_mood_images_pixabay(keywords, remaining, output_dir)
            mood_images.extend(additional)
            print(f"  ✅ Pixabay: {len(additional)}개 추가 다운로드 완료")
        
        # Unsplash에서 추가 다운로드 (3순위)
        if len(mood_images) < target_count and self.unsplash_access_key:
            remaining = target_count - len(mood_images)
            print(f"  📸 Unsplash에서 추가 이미지 다운로드 중... (목표: {remaining}개)")
            additional = self.download_mood_images_unsplash(keywords, remaining, output_dir)
            mood_images.extend(additional)
            print(f"  ✅ Unsplash: {len(additional)}개 추가 다운로드 완료")
        
        # 여전히 부족하면 키워드를 순환하며 추가 다운로드
        if len(mood_images) < target_count:
            remaining = target_count - len(mood_images)
            print(f"  🔄 추가 키워드로 이미지 다운로드 중... (목표: {remaining}개)")
            # 키워드를 순환하며 추가 다운로드
            keyword_cycle = 0
            while len(mood_images) < target_count and keyword_cycle < len(keywords) * 2:
                for keyword in keywords:
                    if len(mood_images) >= target_count:
                        break
                    remaining = target_count - len(mood_images)
                    if remaining <= 0:
                        break
                    
                    # Pexels에서 추가 시도 (1순위)
                    if len(mood_images) < target_count and self.pexels:
                        remaining = target_count - len(mood_images)
                        try:
                            additional = self.download_mood_images_pexels([keyword], min(remaining, 3), output_dir)
                            mood_images.extend(additional)
                        except:
                            pass
                    
                    # Pixabay에서 추가 시도 (2순위)
                    if len(mood_images) < target_count and self.pixabay_api_key:
                        remaining = target_count - len(mood_images)
                        try:
                            additional = self.download_mood_images_pixabay([keyword], min(remaining, 3), output_dir)
                            mood_images.extend(additional)
                        except:
                            pass
                    
                    # Unsplash에서 추가 시도 (3순위)
                    if len(mood_images) < target_count and self.unsplash_access_key:
                        remaining = target_count - len(mood_images)
                        try:
                            additional = self.download_mood_images_unsplash([keyword], min(remaining, 3), output_dir)
                            mood_images.extend(additional)
                        except:
                            pass
                
                keyword_cycle += 1
                if len(mood_images) >= target_count:
                    break
        
        print()
        print("=" * 60)
        print("✅ 다운로드 완료")
        print("=" * 60)
        print(f"📁 저장 위치: {output_dir}")
        print(f"📚 표지: {'✅' if cover_path else '❌'}")
        print(f"🎨 무드 이미지: {len(mood_images)}개")
        print()
        
        # mood_images가 Path 객체 리스트인 경우 문자열로 변환
        mood_images_str = [str(img) if isinstance(img, Path) else img for img in mood_images]
        
        return {
            'cover_path': str(cover_path) if cover_path else None,
            'mood_images': mood_images_str,
            'output_dir': str(output_dir),
            'total_mood_images': len(mood_images_str)
        }
    
    def _generate_keywords(self, book_title: str, author: str = None) -> List[str]:
        """
        책과 관련된 키워드 생성 (저작권 없는 이미지 검색용)
        - 관련 영화, 작가, 책 테마 등
        """
        keywords = []
        
        # 작가 관련 키워드
        if author:
            author_lower = author.lower()
            # 무라카미 하루키 관련
            if "무라카미" in author or "하루키" in author or "murakami" in author_lower or "haruki" in author_lower:
                keywords.extend([
                    "murakami haruki",
                    "haruki murakami",
                    "japanese literature",
                    "japanese author",
                    "tokyo cityscape",
                    "japanese culture",
                    "norwegian wood movie",  # 영화 관련
                    "norwegian wood film",
                    "japanese novel",
                    "murakami books"
                ])
            # 다른 작가들도 추가 가능
            keywords.append(author_lower.replace(" ", ""))
        
        # 책 제목 관련 키워드
        title_lower = book_title.lower()
        if "노르웨이" in book_title or "norwegian" in title_lower or "상실" in book_title or "loss" in title_lower:
            keywords.extend([
                "norway forest",
                "norwegian landscape",
                "forest nature",
                "scandinavian nature",
                "norwegian wood beatles",  # 비틀즈 노래 관련
                "1960s japan",  # 시대 배경
                "tokyo 1960s",
                "age of loss",  # 상실의 시대
                "loss and grief",
                "japanese youth 1960s",
                "tokyo university",
                "japanese student life"
            ])
        
        # 일반적인 문학 키워드 (책과 직접 관련된 것만)
        # "bookstore", "book reading" 등은 너무 일반적이어서 제외
        keywords.extend([
            "literature",
            "vintage book",
            "classic novel"
        ])
        
        # 중복 제거 및 최대 10개 반환
        unique_keywords = []
        seen = set()
        for kw in keywords:
            kw_clean = kw.lower().strip()
            if kw_clean and kw_clean not in seen:
                seen.add(kw_clean)
                unique_keywords.append(kw_clean)
        
        return unique_keywords[:10]
    
    def generate_keywords_with_ai(self, book_title: str, author: str = None, image_dir: Path = None) -> List[str]:
        """
        AI를 사용하여 책 내용 기반 이미지 검색 키워드 생성
        - 책의 내용, 주제, 배경, 감정, 주요 장면 등을 분석하여 구체적인 키워드 생성
        """
        from utils.file_utils import safe_title
        
        # 책 정보 로드 시도
        book_info = None
        if image_dir:
            book_info_path = image_dir / "book_info.json"
            if book_info_path.exists():
                try:
                    with open(book_info_path, 'r', encoding='utf-8') as f:
                        book_info = json.load(f)
                except:
                    pass
        
        # Summary 파일 로드 시도 (더 정확한 키워드 생성을 위해)
        summary_text = None
        summary_path_ko = Path("assets/summaries") / f"{safe_title(book_title)}_summary_ko.txt"
        summary_path_en = Path("assets/summaries") / f"{safe_title(book_title)}_summary_en.txt"
        
        if summary_path_ko.exists():
            try:
                with open(summary_path_ko, 'r', encoding='utf-8') as f:
                    summary_text = f.read()[:2000]  # 처음 2000자만 사용
            except:
                pass
        elif summary_path_en.exists():
            try:
                with open(summary_path_en, 'r', encoding='utf-8') as f:
                    summary_text = f.read()[:2000]
            except:
                pass
        
        # 프롬프트 구성 - 책 내용, 주제, 작가와 직접 연관된 키워드만 생성
        # 한강의 작품인 경우 한국 관련 키워드 포함
        is_korean_author = author and ("한강" in author or "Han Kang" in author)
        
        prompt = f"""다음 책에 대한 이미지 검색 키워드를 생성해주세요. 
책의 내용, 주제, 배경, 감정, 주요 장면, 작가의 스타일 등을 반영하여 Unsplash/Pexels에서 검색할 수 있는 구체적인 영어 키워드를 생성해주세요.

책 제목: {book_title}
저자: {author or "알 수 없음"}
"""
        
        # Summary 내용 추가 (가장 중요)
        if summary_text:
            prompt += f"\n책 요약 내용:\n{summary_text}\n"
        
        if book_info:
            if book_info.get('description'):
                prompt += f"\n책 설명: {book_info['description'][:800]}\n"
            if book_info.get('categories'):
                prompt += f"카테고리: {', '.join(book_info['categories'])}\n"
        
        if is_korean_author:
            prompt += """
중요: 이 책은 한국 작가의 작품입니다. 반드시 한국과 관련된 이미지 키워드를 포함하되, 책의 주제 및 작가의 작품 세계와 직접 연관된 키워드만 사용해주세요.
예를 들어, "소년이 온다"의 경우 광주 민주화 운동, 한국의 역사적 트라우마, 한국의 전환기 정의, 한국의 민주화, 한국의 현대사 등과 관련된 한국 이미지 키워드를 포함해주세요.
"""
        
        prompt += """
다음과 같은 유형의 키워드를 다양하게 포함해주세요 (각 카테고리에서 3-5개씩):
1. 책의 주요 주제/테마 (예: totalitarian government, surveillance state, dystopian society, thought control, historical trauma, transitional justice)
2. 책의 배경/장소 (예: 1960s tokyo, university dormitory, tokyo streets, japanese campus, london 1984, gwangju korea, south korean city, korean urban landscape)
3. 책의 감정/분위기 (예: melancholy youth, lost love, grief, sadness, loneliness, oppression, fear, collective memory, healing)
4. 책에서 언급되는 구체적인 장소나 물건 (예: norwegian forest, tokyo university, ministry of truth, room 101, telescreen, korean memorial, korean history)
5. 시대적 배경 (예: 1960s japan, post-war japan, vintage japan, world war ii aftermath, 1984 london, modern korea, contemporary korea, korean democracy)
6. 작가의 스타일/특징 (예: orwellian world, murakami style, kafkaesque atmosphere, korean literature, han kang style)
7. 주요 인물/관계 (예: young couple, student friendship, romantic relationship, young man alone, winston smith, korean people, korean youth)
8. 책의 핵심 개념/용어 (예: big brother, thought police, newspeak, doublethink, memory hole, korean history, korean society, korean memory)

중요: 
- 각 키워드는 2-4단어로 구성하고, 실제 이미지 검색에 유용한 구체적인 영어 표현을 사용해주세요.
- 반드시 책의 내용, 주제, 작가와 직접 연관된 키워드만 생성하세요.
- 다음 키워드는 절대 사용하지 마세요: "aesthetic", "beautiful", "nice", "pretty", "art", "design", "style" (단독으로 사용할 때)
- 너무 일반적인 키워드(예: "book", "reading", "literature", "novel")는 피하고, 책의 고유한 특성을 반영한 키워드를 우선하세요.
- 키워드만 한 줄에 하나씩 나열해주세요. 설명이나 번호, 불필요한 문자는 포함하지 마세요.
- 총 40-50개의 다양한 키워드를 생성해주세요 (100개 이미지를 다운로드하기 위해 충분한 키워드 필요).

예시 형식: "dystopian society", "totalitarian government", "surveillance state", "orwellian world", "thought police", "big brother watching" """

        try:
            # Claude API 우선 사용
            if ANTHROPIC_AVAILABLE and self.claude_api_key:
                client = anthropic.Anthropic(api_key=self.claude_api_key)
                response = client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1000,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                keywords_text = response.content[0].text
            # OpenAI API 사용
            elif OPENAI_AVAILABLE and self.openai_api_key:
                openai.api_key = self.openai_api_key
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that generates image search keywords based on book content."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000
                )
                keywords_text = response.choices[0].message.content
            else:
                print("   ⚠️ AI API 키가 없어 기본 키워드를 사용합니다.")
                return self._generate_keywords(book_title, author)
            
            # 키워드 파싱 및 필터링
            keywords = []
            # 금지된 일반적인 키워드 목록 (책과 직접 관련 없는 키워드)
            banned_keywords = {
                'aesthetic', 'beautiful', 'nice', 'pretty', 'art', 'design', 'style',
                'book', 'reading', 'literature', 'novel', 'story', 'fiction',
                'image', 'photo', 'picture', 'illustration', 'graphic', 'visual',
                'bookstore', 'bookshop', 'library',  # 책과 직접 관련 없는 일반적인 장소
                'japanese bookstore', 'japanese bookshop'  # 구체적인 금지 키워드
            }
            
            for line in keywords_text.strip().split('\n'):
                line = line.strip()
                # 번호나 불필요한 문자 제거
                if line and not line.startswith('#') and not line.startswith('-'):
                    # 번호 제거 (1. 2. 등)
                    line = line.lstrip('0123456789. -')
                    # 따옴표 제거
                    line = line.strip('"\'')
                    # 단일 문자나 너무 짧은 키워드 제외
                    words = line.split()
                    if words and len(words) >= 1 and len(words) <= 5:
                        # 각 단어가 최소 2글자 이상이어야 함
                        if all(len(w) >= 2 for w in words):
                            keyword = ' '.join(words).lower()
                            # "s tokyo" 같은 이상한 패턴 필터링 (단일 문자로 시작하는 경우)
                            if not (len(words) > 1 and len(words[0]) == 1):
                                # 금지된 키워드 필터링 (책과 직접 관련 없는 일반적인 키워드 제외)
                                keyword_words = set(keyword.split())
                                if not keyword_words.intersection(banned_keywords):
                                    keywords.append(keyword)
            
            if not keywords:
                print("   ⚠️ AI 키워드 생성 실패, 기본 키워드 사용")
                return self._generate_keywords(book_title, author)
            
            # 기본 키워드와 병합 (중복 제거)
            basic_keywords = self._generate_keywords(book_title, author)
            all_keywords = keywords + basic_keywords
            
            # 중복 제거 및 금지 키워드 재필터링
            seen = set()
            unique_keywords = []
            # 추가 금지 키워드 (전체 키워드 문자열에 포함되어 있으면 제외)
            additional_banned = ['bookstore', 'bookshop', 'japanese bookstore', 'japanese bookshop']
            
            for kw in all_keywords:
                kw_clean = kw.lower().strip()
                kw_words = set(kw_clean.split())
                
                # 금지된 키워드가 포함되어 있지 않은 경우만 추가
                if kw_clean and kw_clean not in seen and not kw_words.intersection(banned_keywords):
                    # 추가 금지 키워드 체크 (전체 문자열에 포함되어 있으면 제외)
                    if not any(banned in kw_clean for banned in additional_banned):
                        seen.add(kw_clean)
                        unique_keywords.append(kw_clean)
            
            print(f"   📝 필터링된 키워드: {len(unique_keywords)}개 (일반적인 키워드 제외)")
            # 100개 이미지를 다운로드하기 위해 충분한 키워드 반환
            return unique_keywords[:50]  # 최대 50개 키워드
            
        except Exception as e:
            print(f"   ⚠️ AI 키워드 생성 중 오류: {e}")
            print("   기본 키워드를 사용합니다.")
            return self._generate_keywords(book_title, author)


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='책 표지 및 무드 이미지 다운로드')
    parser.add_argument('--title', type=str, required=True, help='책 제목')
    parser.add_argument('--author', type=str, help='저자 이름')
    parser.add_argument('--keywords', type=str, nargs='+', help='무드 이미지 검색 키워드 (공백으로 구분)')
    parser.add_argument('--num-mood', type=int, default=100, help='무드 이미지 개수 (기본값: 100)')
    parser.add_argument('--skip-cover', action='store_true', help='표지 이미지 다운로드 건너뛰기')
    
    args = parser.parse_args()
    
    downloader = ImageDownloader()
    result = downloader.download_all(
        book_title=args.title,
        author=args.author,
        keywords=args.keywords,
        num_mood_images=args.num_mood,
        skip_cover=args.skip_cover
    )
    
    if result['cover_path']:
        print(f"✅ 표지: {result['cover_path']}")
    if result['mood_images']:
        print(f"✅ 무드 이미지: {len(result['mood_images'])}개")


if __name__ == "__main__":
    main()

