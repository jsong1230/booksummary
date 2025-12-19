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
import random
from dotenv import load_dotenv
try:
    from utils.retry_utils import retry_with_backoff
except ImportError:
    from src.utils.retry_utils import retry_with_backoff

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
        
        # 다양성을 위해 랜덤하게 페이지 선택 (1~3페이지)
        if page == 1:
            page = random.randint(1, 3)
            
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
                try:
                    from utils.file_utils import get_standard_safe_title
                except ImportError:
                    from src.utils.file_utils import get_standard_safe_title
                safe_title_str = get_standard_safe_title(book_title)
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
        # 각 키워드에서 가져올 이미지 수 (다양성을 위해 제한)
        # 키워드가 많으면 적게, 적으면 많이 가져옴 (최소 2개, 최대 5개)
        max_per_keyword = max(2, min(5, num_images // (len(keywords) or 1)))
        
        # 키워드 순서 섞기 (매번 같은 키워드만 사용되지 않도록)
        shuffled_keywords = keywords.copy()
        random.shuffle(shuffled_keywords)
        
        # 다운로드 작업 리스트
        download_tasks = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            for keyword in shuffled_keywords:
                if len(downloaded) + len(download_tasks) >= num_images:
                    break
                
                try:
                    print(f"  🔍 검색: {keyword}")
                    
                    # Unsplash API 검색
                    url = "https://api.unsplash.com/search/photos"
                    headers = {
                        "Authorization": f"Client-ID {self.unsplash_access_key}"
                    }
                    # 다양성을 위해 랜덤하게 페이지 선택 (1~3페이지)
                    page = random.randint(1, 3)
                    
                    # 각 키워드에서 최대 max_per_keyword개만 가져오기
                    remaining = num_images - (len(downloaded) + len(download_tasks))
                    params = {
                        "query": keyword,
                        "page": page,
                        "per_page": min(max_per_keyword, remaining, 15),
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
        # 키워드당 최대 이미지 수 제한 (다양성 확보)
        max_per_keyword = max(2, min(5, num_images // (len(keywords) or 1)))
        
        # 키워드 순서 섞기
        shuffled_keywords = keywords.copy()
        random.shuffle(shuffled_keywords)
        
        download_tasks = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            for keyword in shuffled_keywords:
                if len(downloaded) + len(download_tasks) >= num_images:
                    break
                
                try:
                    print(f"  🔍 검색: {keyword}")
                    
                    # Pexels API 검색
                    try:
                        remaining = num_images - (len(downloaded) + len(download_tasks))
                        # _search_pexels 내부에서 이미 페이지 랜덤화 처리됨
                        search_results = self._search_pexels(keyword, page=1, results_per_page=min(max_per_keyword, remaining))
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
        # 키워드당 최대 이미지 수 제한
        max_per_keyword = max(2, min(5, num_images // (len(keywords) or 1)))
        
        # 키워드 순서 섞기
        shuffled_keywords = keywords.copy()
        random.shuffle(shuffled_keywords)
        
        base_url = "https://pixabay.com/api/"
        download_tasks = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            for keyword in shuffled_keywords:
                if len(downloaded) + len(download_tasks) >= num_images:
                    break
                
                try:
                    print(f"  🔍 검색: {keyword}")
                    
                    # Pixabay API 검색
                    # 다양성을 위해 랜덤하게 페이지 선택
                    page = random.randint(1, 3)
                    
                    params = {
                        'key': self.pixabay_api_key,
                        'q': keyword,
                        'image_type': 'photo',
                        'orientation': 'horizontal',
                        'safesearch': 'true',
                        'page': page,
                        'per_page': min(max_per_keyword, num_images - (len(downloaded) + len(download_tasks)))
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
        try:
            from utils.file_utils import get_standard_safe_title
        except ImportError:
            from src.utils.file_utils import get_standard_safe_title
        safe_title_str = get_standard_safe_title(book_title)
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
            
            # 키워드 순서 섞기
            shuffled_keywords = keywords.copy()
            random.shuffle(shuffled_keywords)
            
            # 키워드를 순환하며 추가 다운로드
            keyword_cycle = 0
            while len(mood_images) < target_count and keyword_cycle < len(keywords) * 2:
                for keyword in shuffled_keywords:
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
        author_lower = author.lower() if author else ""
        title_lower = book_title.lower() if book_title else ""
        
        # 작가 관련 키워드
        if author:
            # 무라카미 하루키 관련
            if any(n in author_lower for n in ["무라카미", "하루키", "murakami", "haruki"]):
                keywords.extend([
                    "japanese literature", "tokyo cityscape", "japanese culture",
                    "norwegian wood movie", "japanese novel", "murakami books",
                    "surrealism art", "jazz bar atmosphere", "well in forest"
                ])
            # 오베라는 남자 / 프레드릭 배크만 관련
            elif any(n in author_lower or n in title_lower for n in ["오베", "배크만", "backman", "ove"]):
                keywords.extend([
                    "swedish small town", "old neighborhood houses", "saab car vintage",
                    "grumpy old man", "lonely figure park bench", "neighborhood community",
                    "winter in sweden", "melancholic atmosphere", "warm interior cottage",
                    "cat in neighborhood", "toolbox and tools", "blue overalls"
                ])
            # 일반적인 작가명 추가
            keywords.append(author_lower.replace(" ", ""))
        
        # 책 제목 테마 관련 키워드
        if any(n in title_lower for n in ["노르웨이", "norwegian", "상실", "loss"]):
            keywords.extend([
                "norway forest", "norwegian landscape", "forest nature",
                "scandinavian nature", "1960s japan", "tokyo 1960s",
                "loss and grief", "japanese youth 1960s", "tokyo university"
            ])
        
        # 시각적 다양성을 위한 범용 테마 키워드 (추가)
        keywords.extend([
            "dramatic lighting", "cinematic landscape", "moody atmosphere",
            "vintage photography", "storytelling visual", "emotional scene",
            "historical setting", "urban decay", "peaceful countryside",
            "abstract theme", "texture background", "soft bokeh",
            "golden hour nature", "minimalist composition", "symbolic object"
        ])
        
        # 일반적인 문학 키워드 (이미지 검색 효율이 좋은 것들)
        keywords.extend([
            "classic novel vibe",
            "vintage aesthetics",
            "literary atmosphere"
        ])
        
        # 중복 제거 및 최대 30개 반환 (기존 10개에서 상향)
        unique_keywords = []
        seen = set()
        for kw in keywords:
            kw_clean = kw.lower().strip()
            if kw_clean and kw_clean not in seen:
                seen.add(kw_clean)
                unique_keywords.append(kw_clean)
        
        return unique_keywords[:30]
    
    def generate_keywords_with_ai(self, book_title: str, author: str = None, image_dir: Path = None) -> List[str]:
        """
        AI를 사용하여 책 내용 기반 이미지 검색 키워드 생성
        - 책의 내용, 주제, 배경, 감정, 주요 장면 등을 분석하여 구체적인 키워드 생성
        """
        try:
            from utils.file_utils import get_standard_safe_title
        except ImportError:
            from src.utils.file_utils import get_standard_safe_title
        
        safe_title_str = get_standard_safe_title(book_title)
        
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
        # .txt와 .md 모두 지원
        summary_paths = [
            Path("assets/summaries") / f"{safe_title_str}_summary_kr.md",
            Path("assets/summaries") / f"{safe_title_str}_summary_en.md",
            # 호환성을 위한 기존 경로들
            Path("assets/summaries") / f"{safe_title_str}_summary_ko.md",
            Path("assets/summaries") / f"{safe_title_str}_summary_ko.txt",
            Path("assets/summaries") / f"{safe_title_str}_summary_en.txt"
        ]
        
        for sp in summary_paths:
            if sp.exists():
                try:
                    with open(sp, 'r', encoding='utf-8') as f:
                        summary_text = f.read()[:2000]  # 처음 2000자만 사용
                    break
                except:
                    continue
        
        prompt = f"""Role: You are an expert visual director and historian.
Task: Generate 60 specific English image search keywords for the book "{book_title}" by "{author}".

Instructions:
1. **Analyze Setting & Mood**: Determine the specific time period and geographical location.
2. **Visual Authenticity**: Generate keywords that strictly reflect the setting.
3. **CRITICAL - Geographical Accuracy**:
   - Strictly follow the story's setting. Do NOT use "Korea" unless the book is set there.
4. **Visual Diversity & Metaphor**: 
   - Beyond literal descriptions, include metaphorical and abstract visual concepts that represent the book's themes.
   - Use a mix of: Wide shots, Extreme-Close-ups (textures), and Medium shots.
   - Request varied lighting: (e.g., golden hour, moody shadows, harsh contrast, soft ethereal light).

Content to Analyze:
"""
        
        # Summary 내용 추가 (가장 중요)
        if summary_text:
            prompt += f"\n[Book Summary]\n{summary_text}\n"
        
        if book_info:
            if book_info.get('description'):
                prompt += f"\n[Book Description]\n{book_info['description'][:800]}\n"
            if book_info.get('categories'):
                prompt += f"[Categories]\n{', '.join(book_info['categories'])}\n"
        
        prompt += """
Keywords Categories (Provide 10-12 per category):
1. **Atmosphere & Mood**: (e.g., melancholy, ottoman miniature style, noir, dystopian fog, ethereal light)
2. **Setting & Architecture**: (e.g., hagia sophia, 16th century istanbul streets, 1960s tokyo alley, snowy forest)
3. **Objects & Symbols (Metaphoric)**: (e.g., broken hourglass, red caftan, vintage ink pot, wilting rose, heavy chains)
4. **Textures & Close-ups**: (e.g., old parchment texture, rain on window, dust motes in light, cracked soil, silk fabric)
5. **Characters/Scenes**: (e.g., silhouette in doorway, ottoman scribes, japanese students 1960s, lonely figure in coat)

Constraints:
- Keywords must be in **ENGLISH**.
- **NO** text overlays or typography keywords.
- **NO** generic terms like "book", "reading", "illustration".
- **Strictly exclude** modern elements if the book is historical.
- **Strictly exclude** Korean elements for non-Korean stories.

Format:
- Return ONLY a list of keywords separated by commas.
- No numbering or explanations.
"""



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
            # 금지된 일반적인 키워드 목록
            banned_keywords = {
                'aesthetic', 'beautiful', 'nice', 'pretty', 'art', 'design', 'style',
                'book', 'reading', 'literature', 'novel', 'story', 'fiction',
                'image', 'photo', 'picture', 'illustration', 'graphic', 'visual',
                'bookstore', 'bookshop', 'library'
            }
            
            # 쉼표(,)와 줄바꿈(\n)을 모두 처리하여 키워드 분리
            raw_keywords = []
            for part in keywords_text.split(','):
                for line in part.split('\n'):
                    raw_keywords.append(line.strip())
            
            for line in raw_keywords:
                # 번호나 불필요한 문자 제거
                if line and not line.startswith('#') and not line.startswith('-'):
                    # 번호 제거 (1. 2. 등)
                    line = line.lstrip('0123456789. -')
                    # 따옴표 제거
                    line = line.strip('"\'')
                    # 단일 문자나 너무 짧은 키워드 제외
                    words = line.split()
                    if words and len(words) >= 1 and len(words) <= 5:
                        # 각 단어가 최소 2글자 이상이어야 함 (단, 'saab' 같은 짧은 유효 단어 허용)
                        if all(len(w) >= 2 for w in words):
                            keyword = ' '.join(words).lower()
                            # 금지된 키워드 필터링
                            keyword_words = set(keyword.split())
                            if not keyword_words.intersection(banned_keywords):
                                keywords.append(keyword)
            
            if not keywords:
                print("   ⚠️ AI 키워드 파싱 결과가 없어 기본 키워드를 사용합니다.")
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

