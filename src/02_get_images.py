"""
책 표지 및 무드 이미지 다운로드 스크립트
- Google Books API로 책 표지 다운로드
- Unsplash/Pexels API로 무드 이미지 다운로드 (5~10장)
"""

import os
import json
import time
import base64
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
    from utils.logger import get_logger
except ImportError:
    from src.utils.logger import get_logger

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
        self.logger = get_logger(__name__)
        
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
                self.logger.warning(f"Google Books API 초기화 실패: {e}")
        
        # Pexels API 초기화
        self.pexels = None
        if PEXELS_AVAILABLE and self.pexels_api_key:
            try:
                self.pexels = PexelsAPI(self.pexels_api_key)
            except Exception as e:
                self.logger.warning(f"Pexels API 초기화 실패: {e}")
        
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
            self.logger.warning("Google Books API가 설정되지 않았습니다.")
            return None
        
        self.logger.info(f"📚 책 표지 검색 중: {book_title}")
        if author:
            self.logger.info(f"   저자: {author}")
        
        try:
            # 검색 쿼리 구성 (저자 포함하여 정확도 향상)
            query = f'intitle:"{book_title}"'
            if author:
                query += f' inauthor:"{author}"'
            
            # 언어 감지: 제목에 한글이 있으면 한국어, 없으면 영어로 검색
            has_korean = any('\uAC00' <= c <= '\uD7A3' for c in book_title)
            lang_restrict = 'ko' if has_korean else 'en'
            
            self.logger.info(f"   검색 언어: {lang_restrict}")
            
            # Google Books API 검색
            results = self.books_service.volumes().list(
                q=query,
                maxResults=10,  # 더 많은 결과 확인
                langRestrict=lang_restrict
            ).execute()
            
            if not results.get('items'):
                # 언어 제한 없이 재시도
                self.logger.warning("언어 제한 검색 결과가 없습니다. 언어 제한 없이 재시도...")
                results = self.books_service.volumes().list(
                    q=query,
                    maxResults=10
                ).execute()
            
            if not results.get('items'):
                self.logger.warning("검색 결과가 없습니다.")
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
                    self.logger.info(f"✅ 매칭된 책 발견: {volume_info.get('title')} - {', '.join(book_authors)}")
                    break
            
            if not best_book:
                # 매칭되는 게 없으면 첫 번째 결과 사용
                self.logger.warning("정확한 매칭을 찾지 못했습니다. 첫 번째 결과를 사용합니다.")
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
                    self.logger.warning("표지 이미지를 찾을 수 없습니다.")
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
                            
                            self.logger.info(f"✅ 표지 다운로드 완료: {output_path}")
                        except Exception as e:
                            self.logger.warning(f"이미지 다운로드 실패: {e}")
                            image_url = None
                    else:
                        self.logger.warning("이미지 URL을 찾을 수 없습니다.")
            else:
                # skip_image=True인 경우에도 image_url은 book_info에 포함하기 위해 가져오기
                image_links = volume_info.get('imageLinks', {})
                if image_links:
                    image_url = image_links.get('large') or image_links.get('medium') or image_links.get('small') or image_links.get('thumbnail')
                self.logger.info("이미지 다운로드는 건너뛰고 책 정보만 저장합니다.")
            
            # ISBN 추출 (industryIdentifiers 필드)
            isbn_13 = ''
            isbn_10 = ''
            for identifier in volume_info.get('industryIdentifiers', []):
                id_type = identifier.get('type', '')
                id_value = identifier.get('identifier', '')
                if id_type == 'ISBN_13':
                    isbn_13 = id_value
                elif id_type == 'ISBN_10':
                    isbn_10 = id_value

            # 검색된 판본의 언어에 따라 ISBN을 한국어/영어로 분류
            book_lang = volume_info.get('language', 'ko')
            isbn_13_ko = isbn_13 if book_lang == 'ko' else ''
            isbn_10_ko = isbn_10 if book_lang == 'ko' else ''
            isbn_13_en = isbn_13 if book_lang != 'ko' else ''
            isbn_10_en = isbn_10 if book_lang != 'ko' else ''

            # 기존 book_info.json이 있으면 다른 언어 ISBN을 보존
            book_info_path = output_dir / "book_info.json"
            if book_info_path.exists():
                try:
                    with open(book_info_path, 'r', encoding='utf-8') as f:
                        existing = json.load(f)
                    if not isbn_13_ko:
                        isbn_13_ko = existing.get('isbn_13_ko', '')
                    if not isbn_10_ko:
                        isbn_10_ko = existing.get('isbn_10_ko', '')
                    if not isbn_13_en:
                        isbn_13_en = existing.get('isbn_13_en', '')
                    if not isbn_10_en:
                        isbn_10_en = existing.get('isbn_10_en', '')
                except Exception:
                    pass

            # 책 정보 저장 (이미지 다운로드 여부와 관계없이 항상 저장)
            book_info = {
                'title': volume_info.get('title', book_title),
                'authors': volume_info.get('authors', [author] if author else []),
                'publisher': volume_info.get('publisher', ''),
                'publishedDate': volume_info.get('publishedDate', ''),
                'description': volume_info.get('description', ''),
                'pageCount': volume_info.get('pageCount', 0),
                'categories': volume_info.get('categories', []),
                'language': book_lang,
                'google_books_id': book.get('id', ''),
                'image_url': image_url if image_url else '',
                'isbn_13_ko': isbn_13_ko,
                'isbn_10_ko': isbn_10_ko,
                'isbn_13_en': isbn_13_en,
                'isbn_10_en': isbn_10_en
            }
            
            book_info_path = output_dir / "book_info.json"
            with open(book_info_path, 'w', encoding='utf-8') as f:
                json.dump(book_info, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"✅ 책 정보 저장 완료: {book_info_path}")
            
            return str(output_path) if output_path else None
            
        except Exception as e:
            self.logger.error(f"오류: {e}")
            return None
    
    @retry_with_backoff(retries=3, backoff_in_seconds=2.0)
    def download_mood_images_unsplash(self, keywords: List[str], num_images: int = 100, output_dir: Path = None, max_per_keyword_override: Optional[int] = None) -> List[str]:
        """
        Unsplash API로 무드 이미지 다운로드
        
        Args:
            keywords: 검색 키워드 리스트
            num_images: 다운로드할 이미지 개수
            output_dir: 저장 디렉토리
            max_per_keyword_override: 키워드당 최대 이미지 수 오버라이드 (None이면 자동 계산)
            
        Returns:
            다운로드된 파일 경로 리스트
        """
        if not self.unsplash_access_key:
            self.logger.warning("Unsplash API 키가 설정되지 않았습니다.")
            return []
        
        downloaded = []
        # 각 키워드에서 가져올 이미지 수 (다양성을 위해 제한)
        # 키워드가 많으면 적게, 적으면 많이 가져옴 (최소 2개, 최대 5개)
        # 추가 다운로드 시에는 제한을 완화하여 빠르게 다운로드
        if max_per_keyword_override is not None:
            max_per_keyword = max_per_keyword_override
        else:
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
                    self.logger.info(f"🔍 검색: {keyword}")
                    
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
                        self.logger.warning(f"검색 결과 없음: {keyword}")
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
                    self.logger.error(f"오류: {e}")
                    continue
            
            # 결과 수집
            for future, filename in download_tasks:
                try:
                    result = future.result()
                    if result:
                        downloaded.append(result)
                        self.logger.info(f"✅ {filename}")
                except Exception as e:
                    self.logger.error(f"이미지 다운로드 실패 ({filename}): {e}")
        
        return downloaded
    
    @retry_with_backoff(retries=3, backoff_in_seconds=2.0)
    def download_mood_images_pexels(self, keywords: List[str], num_images: int = 100, output_dir: Path = None, max_per_keyword_override: Optional[int] = None) -> List[str]:
        """
        Pexels API로 무드 이미지 다운로드
        
        Args:
            keywords: 검색 키워드 리스트
            num_images: 다운로드할 이미지 개수
            output_dir: 저장 디렉토리
            max_per_keyword_override: 키워드당 최대 이미지 수 오버라이드 (None이면 자동 계산)
            
        Returns:
            다운로드된 파일 경로 리스트
        """
        if not self.pexels:
            self.logger.warning("Pexels API가 설정되지 않았습니다.")
            return []
        
        downloaded = []
        # 키워드당 최대 이미지 수 제한 (다양성 확보)
        # 추가 다운로드 시에는 제한을 완화하여 빠르게 다운로드
        if max_per_keyword_override is not None:
            max_per_keyword = max_per_keyword_override
        else:
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
                    self.logger.info(f"🔍 검색: {keyword}")
                    
                    # Pexels API 검색
                    try:
                        remaining = num_images - (len(downloaded) + len(download_tasks))
                        # _search_pexels 내부에서 이미 페이지 랜덤화 처리됨
                        search_results = self._search_pexels(keyword, page=1, results_per_page=min(max_per_keyword, remaining))
                    except Exception as e:
                        self.logger.error(f"Pexels 검색 오류: {e}")
                        continue
                    
                    if not search_results.get('photos'):
                        self.logger.warning(f"검색 결과 없음: {keyword}")
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
                    self.logger.error(f"오류: {e}")
                    continue
            
            # 결과 수집
            for future, filename in download_tasks:
                try:
                    result = future.result()
                    if result:
                        downloaded.append(result)
                        self.logger.info(f"✅ {filename}")
                except Exception as e:
                    self.logger.error(f"이미지 다운로드 실패 ({filename}): {e}")
        
        return downloaded
    
    @retry_with_backoff(retries=3, backoff_in_seconds=2.0)
    def download_mood_images_pixabay(self, keywords: List[str], num_images: int = 100, output_dir: Path = None, max_per_keyword_override: Optional[int] = None) -> List[str]:
        """
        Pixabay API로 무드 이미지 다운로드
        
        Args:
            keywords: 검색 키워드 리스트
            num_images: 다운로드할 이미지 개수
            output_dir: 저장 디렉토리
            max_per_keyword_override: 키워드당 최대 이미지 수 오버라이드 (None이면 자동 계산)
            
        Returns:
            다운로드된 파일 경로 리스트
        """
        if not self.pixabay_api_key:
            self.logger.warning("Pixabay API 키가 설정되지 않았습니다.")
            return []
        
        downloaded = []
        # 키워드당 최대 이미지 수 제한
        # 추가 다운로드 시에는 제한을 완화하여 빠르게 다운로드
        if max_per_keyword_override is not None:
            max_per_keyword = max_per_keyword_override
        else:
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
                    self.logger.info(f"🔍 검색: {keyword}")
                    
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
                        self.logger.warning(f"검색 결과 없음: {keyword}")
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
                    self.logger.error(f"오류: {e}")
                    continue
            
            # 결과 수집
            for future, filename in download_tasks:
                try:
                    result = future.result()
                    if result:
                        downloaded.append(result)
                        self.logger.info(f"✅ {filename}")
                except Exception as e:
                    self.logger.error(f"이미지 다운로드 실패 ({filename}): {e}")
        
        return downloaded
    
    def validate_images_with_ai(self, image_dir: Path, book_title: str, author: str = None, target_count: int = 100) -> List[Path]:
        """
        GPT-4o Vision으로 다운로드된 이미지의 책 관련성을 검증하고 상위 이미지만 유지.

        Args:
            image_dir: 이미지 디렉토리 경로
            book_title: 책 제목
            author: 저자 이름
            target_count: 최종 유지할 이미지 수 (기본: 100)

        Returns:
            검증 후 유지된 이미지 경로 목록
        """
        if not OPENAI_AVAILABLE or not self.openai_api_key:
            self.logger.warning("OpenAI API 키가 없어 이미지 검증을 건너뜁니다.")
            return list(image_dir.glob("mood_*.jpg"))[:target_count]

        all_images = sorted(image_dir.glob("mood_*.jpg"))
        if not all_images:
            return []

        self.logger.info(f"🔍 AI 이미지 검증 시작: {len(all_images)}개 이미지 → 상위 {target_count}개 선별")

        author_str = f" by {author}" if author else ""
        scored_images = []
        batch_size = 10

        client_oa = openai.OpenAI(api_key=self.openai_api_key)

        for i in range(0, len(all_images), batch_size):
            batch = all_images[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(all_images) + batch_size - 1) // batch_size
            self.logger.info(f"  배치 {batch_num}/{total_batches} 검증 중... ({len(batch)}개)")

            # 이미지를 base64로 인코딩
            image_contents = []
            valid_batch = []
            for img_path in batch:
                try:
                    with open(img_path, 'rb') as f:
                        img_data = base64.b64encode(f.read()).decode('utf-8')
                    image_contents.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_data}", "detail": "low"}
                    })
                    valid_batch.append(img_path)
                except Exception as e:
                    self.logger.warning(f"이미지 읽기 실패 ({img_path.name}): {e}")

            if not valid_batch:
                continue

            prompt_text = (
                f"You are evaluating {len(valid_batch)} images for use in a video about the book "
                f'"{book_title}"{author_str}.\n\n'
                f"For EACH image (numbered 1 to {len(valid_batch)}), rate how relevant it is to this specific book's "
                f"content, setting, themes, or atmosphere on a scale of 1-10.\n\n"
                f"Scoring guide:\n"
                f"- 8-10: Directly matches the book's setting, characters, or key themes\n"
                f"- 5-7: Loosely related to the book's mood or general era/location\n"
                f"- 1-4: Generic stock photo with no clear connection to this book\n\n"
                f"Respond with ONLY {len(valid_batch)} numbers separated by commas (e.g., '7,3,9,5,...').\n"
                f"No explanations."
            )

            messages = [{"type": "text", "text": prompt_text}] + image_contents

            try:
                response = client_oa.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": messages}],
                    max_tokens=100
                )
                scores_text = response.choices[0].message.content or ""
                scores_raw = [s.strip() for s in scores_text.split(',')]
                scores = []
                for s in scores_raw:
                    try:
                        scores.append(int(float(s)))
                    except ValueError:
                        scores.append(5)  # 파싱 실패 시 중간 점수

                # 점수 길이 맞추기
                while len(scores) < len(valid_batch):
                    scores.append(5)
                scores = scores[:len(valid_batch)]

                for img_path, score in zip(valid_batch, scores):
                    scored_images.append((score, img_path))

            except Exception as e:
                self.logger.warning(f"배치 {batch_num} 검증 실패: {e}")
                # 실패한 배치는 중간 점수로 처리
                for img_path in valid_batch:
                    scored_images.append((5, img_path))

            time.sleep(0.5)  # API rate limit 방지

        if not scored_images:
            self.logger.warning("검증 결과 없음 - 원본 이미지 목록 반환")
            return list(all_images)[:target_count]

        # 점수순 내림차순 정렬
        scored_images.sort(key=lambda x: x[0], reverse=True)

        # 점수 분포 로깅
        score_counts = {i: sum(1 for s, _ in scored_images if s == i) for i in range(1, 11)}
        self.logger.info(f"📊 점수 분포: {score_counts}")

        kept = [p for _, p in scored_images[:target_count]]
        removed = [p for _, p in scored_images[target_count:]]

        # 점수 낮은 이미지 삭제
        deleted_count = 0
        for img_path in removed:
            try:
                img_path.unlink()
                deleted_count += 1
            except Exception as e:
                self.logger.warning(f"이미지 삭제 실패 ({img_path.name}): {e}")

        # 유지된 이미지 중 점수 낮은 것(1-4점) 개수 로깅
        low_score_kept = sum(1 for s, _ in scored_images[:target_count] if s <= 4)
        self.logger.info(
            f"✅ 검증 완료: {len(kept)}개 유지 (저점수 포함 {low_score_kept}개), {deleted_count}개 삭제"
        )

        return kept

    def download_all(self, book_title: str, author: str = None, keywords: List[str] = None, num_mood_images: int = 100, skip_cover: bool = False, skip_validation: bool = False) -> Dict:
        """
        책 표지와 무드 이미지 모두 다운로드

        Args:
            book_title: 책 제목
            author: 저자 이름
            keywords: 무드 이미지 검색 키워드 (None이면 자동 생성)
            num_mood_images: 최종 유지할 무드 이미지 개수 (기본: 100)
            skip_cover: 표지 이미지 다운로드 건너뛰기
            skip_validation: AI 검증 건너뛰기 (기본: False, 검증 수행)

        Returns:
            다운로드 결과 딕셔너리
        """
        self.logger.info("=" * 60)
        self.logger.info("🖼️ 이미지 다운로드 시작")
        self.logger.info("=" * 60)
        
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
            self.logger.info("책 표지 이미지 다운로드는 건너뛰지만, 책 정보(book_info.json)는 생성합니다.")
            self.download_book_cover(book_title, author, output_dir, skip_image=True)
        else:
            self.logger.warning("책 표지 이미지는 저작권 문제로 영상에 사용하지 않습니다.")
            self.logger.info("표지는 참고용으로만 다운로드합니다.")
            cover_path = self.download_book_cover(book_title, author, output_dir, skip_image=False)
        
        # 2. 키워드 생성 (없으면) - AI를 사용하여 책 내용 기반 키워드 생성
        if keywords is None:
            self.logger.info("📝 AI를 사용하여 책 내용 기반 이미지 검색 키워드 생성 중...")
            keywords = self.generate_keywords_with_ai(book_title, author, output_dir)
            self.logger.info(f"✅ 생성된 키워드: {', '.join(keywords[:10])}")
        
        self.logger.info(f"🎨 무드 이미지 다운로드 중... (키워드: {', '.join(keywords)})")
        
        # 3. 무드 이미지 다운로드 (Pexels → Pixabay → Unsplash 순서)
        # 기존 이미지 확인
        existing_images = list(output_dir.glob("mood_*.jpg"))
        existing_count = len(existing_images)
        
        if existing_count >= num_mood_images:
            self.logger.info(f"✅ 기존 이미지 발견: {existing_count}개 (목표: {num_mood_images}개)")
            self.logger.info("이미지 다운로드를 건너뜁니다.")
            return {
                'cover_path': str(cover_path) if cover_path else None,
                'mood_images': [str(img) for img in existing_images[:num_mood_images]],
                'total_mood_images': existing_count
            }

        # AI 검증을 위해 여유분(30개)을 포함하여 더 많이 다운로드
        # skip_validation이면 목표 수만큼만 다운로드
        download_target = num_mood_images if skip_validation else max(num_mood_images + 30, 130)
        self.logger.info(f"📊 기존 이미지: {existing_count}개, 다운로드 목표: {download_target}개 (검증 후 {num_mood_images}개 유지)")

        # 이미지를 확실히 다운로드하기 위해 여러 키워드에서 충분히 수집
        mood_images = existing_images.copy()  # 기존 이미지 포함
        target_count = download_target
        
        # Pexels에서 다운로드 (1순위)
        if len(mood_images) < target_count and self.pexels:
            remaining = target_count - len(mood_images)
            self.logger.info(f"📸 Pexels에서 이미지 다운로드 중... (목표: {remaining}개)")
            additional = self.download_mood_images_pexels(keywords, remaining, output_dir)
            mood_images.extend(additional)
            self.logger.info(f"✅ Pexels: {len(additional)}개 다운로드 완료")
        
        # Pixabay에서 추가 다운로드 (2순위)
        if len(mood_images) < target_count and self.pixabay_api_key:
            remaining = target_count - len(mood_images)
            self.logger.info(f"📸 Pixabay에서 추가 이미지 다운로드 중... (목표: {remaining}개)")
            additional = self.download_mood_images_pixabay(keywords, remaining, output_dir)
            mood_images.extend(additional)
            self.logger.info(f"✅ Pixabay: {len(additional)}개 추가 다운로드 완료")
        
        # Unsplash에서 추가 다운로드 (3순위)
        if len(mood_images) < target_count and self.unsplash_access_key:
            remaining = target_count - len(mood_images)
            self.logger.info(f"📸 Unsplash에서 추가 이미지 다운로드 중... (목표: {remaining}개)")
            additional = self.download_mood_images_unsplash(keywords, remaining, output_dir)
            mood_images.extend(additional)
            self.logger.info(f"✅ Unsplash: {len(additional)}개 추가 다운로드 완료")
        
        # 여전히 부족하면 키워드를 순환하며 추가 다운로드
        # 개선: 한 번에 더 많은 이미지를 가져오고, 병렬 처리를 최적화하여 지연 최소화
        if len(mood_images) < target_count:
            remaining = target_count - len(mood_images)
            self.logger.info(f"🔄 추가 키워드로 이미지 다운로드 중... (목표: {remaining}개)")
            
            # 키워드 순서 섞기
            shuffled_keywords = keywords.copy()
            random.shuffle(shuffled_keywords)
            
            # 추가 다운로드: 한 번에 더 많은 이미지를 가져오도록 개선
            # 키워드당 최대 개수를 늘리고, 병렬 처리를 최적화
            keyword_cycle = 0
            max_cycles = 3  # 최대 3번 순환 (기존 len(keywords) * 2에서 축소)
            
            while len(mood_images) < target_count and keyword_cycle < max_cycles:
                remaining = target_count - len(mood_images)
                if remaining <= 0:
                    break
                
                # 한 번에 더 많은 이미지를 가져오기 위해 키워드당 최대 개수 증가
                # 남은 개수가 적으면 한 번에 처리
                batch_size = min(remaining, 10)  # 한 번에 최대 10개씩 처리
                
                # Pexels에서 추가 시도 (1순위) - 우선적으로 더 많이 가져오기
                if len(mood_images) < target_count and self.pexels:
                    remaining = target_count - len(mood_images)
                    try:
                        # 추가 다운로드 시 키워드당 제한을 완화 (최대 10개까지 허용)
                        # 남은 개수가 적으면 한 번에 빠르게 처리
                        additional = self.download_mood_images_pexels(
                            shuffled_keywords[:5], 
                            remaining, 
                            output_dir,
                            max_per_keyword_override=min(10, remaining)  # 키워드당 최대 10개까지 허용
                        )
                        mood_images.extend(additional)
                        if len(mood_images) >= target_count:
                            break
                    except Exception as e:
                        self.logger.warning(f"Pexels 추가 다운로드 실패: {e}")
                
                # Pixabay에서 추가 시도 (2순위)
                if len(mood_images) < target_count and self.pixabay_api_key:
                    remaining = target_count - len(mood_images)
                    try:
                        # 추가 다운로드 시 키워드당 제한을 완화
                        additional = self.download_mood_images_pixabay(
                            shuffled_keywords[:5], 
                            remaining, 
                            output_dir,
                            max_per_keyword_override=min(10, remaining)  # 키워드당 최대 10개까지 허용
                        )
                        mood_images.extend(additional)
                        if len(mood_images) >= target_count:
                            break
                    except Exception as e:
                        self.logger.warning(f"Pixabay 추가 다운로드 실패: {e}")
                
                # Unsplash에서 추가 시도 (3순위)
                if len(mood_images) < target_count and self.unsplash_access_key:
                    remaining = target_count - len(mood_images)
                    try:
                        # 추가 다운로드 시 키워드당 제한을 완화
                        additional = self.download_mood_images_unsplash(
                            shuffled_keywords[:5], 
                            remaining, 
                            output_dir,
                            max_per_keyword_override=min(10, remaining)  # 키워드당 최대 10개까지 허용
                        )
                        mood_images.extend(additional)
                        if len(mood_images) >= target_count:
                            break
                    except Exception as e:
                        self.logger.warning(f"Unsplash 추가 다운로드 실패: {e}")
                
                keyword_cycle += 1
                if len(mood_images) >= target_count:
                    break
        
        self.logger.info("=" * 60)
        self.logger.info("✅ 다운로드 완료")
        self.logger.info("=" * 60)
        self.logger.info(f"📁 저장 위치: {output_dir}")
        self.logger.info(f"📚 표지: {'✅' if cover_path else '❌'}")
        self.logger.info(f"🎨 무드 이미지: {len(mood_images)}개")

        # 4. AI 검증 단계: 관련성 낮은 이미지 삭제, 상위 num_mood_images개 유지
        if not skip_validation and len(mood_images) > num_mood_images:
            self.logger.info(f"🔍 AI 검증 시작: {len(mood_images)}개 → {num_mood_images}개 선별")
            validated = self.validate_images_with_ai(output_dir, book_title, author, target_count=num_mood_images)
            mood_images = validated
        else:
            if skip_validation:
                self.logger.info("⏩ AI 검증 건너뜀 (--skip-validation)")
            mood_images = mood_images[:num_mood_images]

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
        
        # 범용 테마 키워드는 제거 - 책 내용과 무관한 이미지가 포함되는 원인
        
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
                        summary_text = f.read()[:4000]  # 처음 4000자 사용 (더 많은 장면 정보)
                    break
                except:
                    continue
        
        prompt = f"""Role: You are an expert visual director and historian specializing in book-to-visual adaptation.
Task: Generate 60 specific English image search keywords for the book "{book_title}" by "{author}".

CRITICAL RULES:
1. **Book-Specific ONLY**: Every keyword must directly reflect THIS book's actual content, scenes, settings, or themes.
2. **NO Generic Photography Terms**: FORBIDDEN - "dramatic lighting", "cinematic landscape", "moody atmosphere", "vintage photography", "golden hour", "soft bokeh", "minimalist composition", "symbolic object", "classic novel vibe", "literary atmosphere". These are banned.
3. **Geographical Accuracy**: Strictly follow the story's actual setting. Do NOT use "Korea" unless the book is set there.
4. **Scene-Based**: Extract specific scenes, locations, objects, and characters from the book's actual content.
5. **Visual Diversity**: Include wide establishing shots, close-up textures, and character moments - all book-specific.

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
1. **Book-Specific Atmosphere**: ONLY the unique emotional tone and atmosphere of THIS book (e.g., "nazi concentration camp despair", "1960s tokyo melancholy", "austrian mountains isolation")
2. **Setting & Architecture**: Actual locations from the book (e.g., "hagia sophia interior", "auschwitz barracks", "1960s tokyo university dormitory", "norwegian forest autumn")
3. **Objects & Symbols**: Actual objects that appear in the book or symbolize its themes (e.g., "prisoner uniform stripes", "vintage japanese record player", "worn leather journal")
4. **Textures & Close-ups**: Physical details that evoke the book's world (e.g., "barbed wire close-up", "old tatami mat texture", "yellowed wartime document")
5. **Characters/Scenes**: Specific scenes or character types from the book (e.g., "prisoner working in nazi camp", "japanese college student 1960s", "lonely man in snowy park")

Constraints:
- Keywords must be in **ENGLISH**.
- **NO** text overlays or typography keywords.
- **NO** generic stock photo terms: "dramatic lighting", "cinematic", "vintage photography", "golden hour", "bokeh", "minimalist", "storytelling visual", "emotional scene", "literary".
- **NO** generic terms like "book", "reading", "illustration", "nature landscape" unless specific to the book.
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
                    model="claude-sonnet-4-6",
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
                client_oa = openai.OpenAI(api_key=self.openai_api_key)
                response = client_oa.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that generates image search keywords based on book content."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000
                )
                keywords_text = response.choices[0].message.content
            else:
                self.logger.warning("AI API 키가 없어 기본 키워드를 사용합니다.")
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
                self.logger.warning("AI 키워드 파싱 결과가 없어 기본 키워드를 사용합니다.")
                return self._generate_keywords(book_title, author)
            
            # AI 키워드가 충분하면 basic 키워드 병합하지 않음 (책 관련성 유지)
            # AI 키워드가 30개 미만일 때만 작가/제목별 하드코딩 키워드로 보충
            if len(keywords) >= 30:
                self.logger.info(f"📝 AI 키워드 {len(keywords)}개 충분 - basic 키워드 병합 생략 (관련성 유지)")
                all_keywords = keywords
            else:
                self.logger.info(f"📝 AI 키워드 {len(keywords)}개 부족 - basic 키워드로 보충")
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
            
            self.logger.info(f"📝 필터링된 키워드: {len(unique_keywords)}개 (일반적인 키워드 제외)")
            # 100개 이미지를 다운로드하기 위해 충분한 키워드 반환
            return unique_keywords[:50]  # 최대 50개 키워드
            
        except Exception as e:
            self.logger.warning(f"AI 키워드 생성 중 오류: {e}")
            self.logger.info("기본 키워드를 사용합니다.")
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
    parser.add_argument('--skip-validation', action='store_true', help='AI 이미지 검증 건너뛰기 (기본: 검증 수행)')

    args = parser.parse_args()

    downloader = ImageDownloader()
    result = downloader.download_all(
        book_title=args.title,
        author=args.author,
        keywords=args.keywords,
        num_mood_images=args.num_mood,
        skip_cover=args.skip_cover,
        skip_validation=args.skip_validation
    )
    
    logger = get_logger(__name__)
    if result['cover_path']:
        logger.info(f"✅ 표지: {result['cover_path']}")
    if result['mood_images']:
        logger.info(f"✅ 무드 이미지: {len(result['mood_images'])}개")


if __name__ == "__main__":
    main()

