#!/usr/bin/env python3
"""
책 분위기에 맞는 라이선스 없는 배경음악 자동 다운로드 스크립트

책 정보를 분석하여 적절한 배경음악을 검색하고 다운로드합니다.
"""

import os
import sys
import json
import time
import requests
import argparse
import webbrowser
import urllib.parse
import re
from pathlib import Path
from typing import Optional, List, Dict
from dotenv import load_dotenv

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        WEBDRIVER_MANAGER_AVAILABLE = True
    except ImportError:
        WEBDRIVER_MANAGER_AVAILABLE = False
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.file_utils import get_standard_safe_title, load_book_info
from src.utils.logger import setup_logger
from utils.translations import translate_book_title, is_english_title

load_dotenv()

# 로거 설정
logger = setup_logger(__name__)


def analyze_book_mood(book_title: str, book_info: Optional[Dict] = None) -> List[str]:
    """
    책 정보를 분석하여 음악 분위기 키워드 생성
    
    Args:
        book_title: 책 제목
        book_info: 책 정보 딕셔너리 (선택사항)
        
    Returns:
        음악 검색 키워드 리스트
    """
    keywords = []
    
    # 책 제목에서 키워드 추출
    title_lower = book_title.lower()
    
    # 장르별 키워드 매핑
    genre_keywords = {
        # 고전/문학
        'classic': ['classical', 'piano', 'orchestral', 'ambient'],
        'literature': ['ambient', 'calm', 'peaceful', 'acoustic'],
        'novel': ['ambient', 'cinematic', 'emotional'],
        
        # 역사
        'history': ['epic', 'orchestral', 'cinematic', 'dramatic'],
        'historical': ['epic', 'orchestral', 'cinematic'],
        
        # 철학
        'philosophy': ['ambient', 'meditative', 'calm', 'peaceful'],
        'philosophical': ['ambient', 'meditative'],
        
        # 전쟁/액션
        'war': ['epic', 'dramatic', 'intense', 'cinematic'],
        'action': ['energetic', 'upbeat', 'cinematic'],
        
        # 로맨스
        'romance': ['romantic', 'soft', 'emotional', 'piano'],
        'love': ['romantic', 'soft', 'emotional'],
        
        # 공포/스릴러
        'horror': ['dark', 'mysterious', 'suspenseful', 'atmospheric'],
        'thriller': ['suspenseful', 'dramatic', 'intense'],
        
        # SF/판타지
        'science': ['futuristic', 'electronic', 'ambient'],
        'fantasy': ['epic', 'magical', 'cinematic', 'orchestral'],
        
        # 비즈니스/자기계발
        'business': ['corporate', 'upbeat', 'motivational'],
        'self': ['inspirational', 'uplifting', 'positive'],
        'development': ['inspirational', 'uplifting'],
    }
    
    # 제목에서 장르 키워드 찾기
    for genre, music_keywords in genre_keywords.items():
        if genre in title_lower:
            keywords.extend(music_keywords)
            break
    
    # 기본 키워드 (항상 포함)
    if not keywords:
        keywords = ['ambient', 'calm', 'peaceful', 'cinematic']
    
    # 책 정보에서 추가 키워드 추출
    if book_info:
        # 카테고리/장르 정보 활용
        categories = book_info.get('categories', [])
        for category in categories:
            category_lower = category.lower()
            if 'fiction' in category_lower or '소설' in category_lower:
                keywords.extend(['narrative', 'storytelling', 'emotional'])
            elif 'non-fiction' in category_lower or '비소설' in category_lower:
                keywords.extend(['documentary', 'informative', 'calm'])
            elif 'history' in category_lower or '역사' in category_lower:
                keywords.extend(['epic', 'orchestral'])
            elif 'philosophy' in category_lower or '철학' in category_lower:
                keywords.extend(['meditative', 'thoughtful'])
    
    # 중복 제거 및 정리
    keywords = list(set(keywords))[:5]  # 최대 5개
    
    return keywords


def search_freesound(keywords: List[str], api_key: Optional[str] = None) -> Optional[Dict]:
    """
    Freesound API로 음악 검색 (효과음 위주이지만 일부 음악도 있음)
    
    Args:
        keywords: 검색 키워드 리스트
        api_key: Freesound API 키 (선택사항)
        
    Returns:
        음악 정보 딕셔너리 또는 None
    """
    if not api_key:
        api_key = os.getenv("FREESOUND_API_KEY")
    
    if not api_key:
        logger.warning("Freesound API 키가 설정되지 않았습니다.")
        return None
    
    try:
        # Freesound API 검색
        query = ' '.join(keywords[:3])  # 처음 3개 키워드만 사용
        url = "https://freesound.org/apiv2/search/text/"
        params = {
            'query': query,
            'filter': 'duration:[10 TO 300]',  # 10초~5분
            'fields': 'id,name,previews,duration,license,username',
            'page_size': 5
        }
        headers = {
            'Authorization': f'Token {api_key}'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        results = data.get('results', [])
        
        if results:
            # 가장 적합한 음악 선택 (라이선스 확인)
            for result in results:
                license_url = result.get('license', '')
                # CC0 또는 CC BY 라이선스만 사용
                if 'cc0' in license_url.lower() or 'creativecommons.org/licenses/by' in license_url.lower():
                    return {
                        'id': result['id'],
                        'name': result['name'],
                        'preview_url': result['previews'].get('preview-hq-mp3') or result['previews'].get('preview-lq-mp3'),
                        'duration': result.get('duration', 0),
                        'license': license_url,
                        'source': 'freesound'
                    }
        
        return None
        
    except Exception as e:
        logger.warning(f"Freesound API 검색 실패: {e}")
        return None


def sanitize_filename(filename: str) -> str:
    """파일명에서 특수문자 제거"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    filename = ' '.join(filename.split())
    return filename[:200]


def setup_driver(headless: bool = False):
    """Chrome WebDriver 설정"""
    if not SELENIUM_AVAILABLE:
        logger.error("Selenium이 설치되지 않았습니다. pip install selenium webdriver-manager")
        return None
    
    options = webdriver.ChromeOptions()
    
    if headless:
        options.add_argument("--headless=new")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    logger.info("Chrome WebDriver 초기화 중...")
    try:
        if WEBDRIVER_MANAGER_AVAILABLE:
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options,
            )
        else:
            driver = webdriver.Chrome(options=options)
        
        driver.set_window_size(1920, 1080)
        driver.implicitly_wait(5)
        
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            '''
        })
        
        logger.info("WebDriver 준비 완료")
        return driver
    except Exception as e:
        logger.error(f"WebDriver 초기화 실패: {e}")
        return None


def find_mp3_url(driver, track_url: str) -> Optional[str]:
    """트랙 페이지에서 MP3 다운로드 URL 찾기"""
    strategies = [
        # 전략 1: 직접 다운로드 링크 찾기
        lambda: _find_direct_download_link(driver),
        # 전략 2: 페이지 소스에서 정규식으로 찾기
        lambda: _find_in_page_source(driver),
        # 전략 3: data 속성에서 찾기
        lambda: _find_in_data_attributes(driver),
        # 전략 4: 네트워크 로그에서 찾기
        lambda: _find_in_network_logs(driver),
    ]
    
    for i, strategy in enumerate(strategies, 1):
        try:
            url = strategy()
            if url:
                logger.info(f"MP3 URL 발견 (전략 {i}): {url[:80]}...")
                return url
        except Exception as e:
            logger.debug(f"전략 {i} 실패: {e}")
    
    return None


def _find_direct_download_link(driver) -> Optional[str]:
    """직접 다운로드 링크 찾기"""
    try:
        download_buttons = driver.find_elements(By.XPATH, "//a[contains(@href, '.mp3')]")
        for btn in download_buttons:
            href = btn.get_attribute('href')
            if href and '.mp3' in href:
                return href
    except:
        pass
    return None


def _find_in_page_source(driver) -> Optional[str]:
    """페이지 소스에서 MP3 URL 찾기"""
    page_source = driver.page_source
    patterns = [
        r'https?://[^"\s]+\.mp3',
        r'"(https?://[^"]+download[^"]+\.mp3[^"]*)"',
        r'url\(["\']?(https?://[^"\']+\.mp3[^"\']*?)["\']?\)',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, page_source)
        for match in matches:
            if 'pixabay' in match.lower() and '.mp3' in match.lower():
                return match
    return None


def _find_in_data_attributes(driver) -> Optional[str]:
    """data 속성에서 MP3 URL 찾기"""
    try:
        elements = driver.find_elements(By.XPATH, "//*[@data-url or @data-src or @data-mp3]")
        for elem in elements:
            for attr in ['data-url', 'data-src', 'data-mp3']:
                url = elem.get_attribute(attr)
                if url and '.mp3' in url:
                    return url
    except:
        pass
    return None


def _find_in_network_logs(driver) -> Optional[str]:
    """네트워크 로그에서 MP3 URL 찾기"""
    try:
        logs = driver.get_log('performance')
        for log in logs:
            message = log.get('message', '')
            if '.mp3' in message and 'download' in message.lower():
                try:
                    log_data = json.loads(message)
                    if 'message' in log_data:
                        params = log_data['message'].get('params', {})
                        request = params.get('request', {})
                        url = request.get('url', '')
                        if '.mp3' in url:
                            return url
                except:
                    pass
    except:
        pass
    return None


def download_mp3_from_pixabay(keywords: List[str], output_dir: Path, max_tracks: int = 1) -> Optional[str]:
    """
    Pixabay Music에서 Selenium을 사용하여 음악 자동 다운로드
    
    Args:
        keywords: 검색 키워드 리스트
        output_dir: 출력 디렉토리
        max_tracks: 최대 다운로드 개수 (기본값: 1)
        
    Returns:
        다운로드된 파일 경로 또는 None
    """
    if not SELENIUM_AVAILABLE:
        logger.warning("Selenium이 설치되지 않았습니다.")
        logger.info("pip install selenium webdriver-manager")
        return None
    
    # 검색 URL 생성
    search_query = ' '.join(keywords[:3])  # 처음 3개 키워드만 사용
    base_url = "https://pixabay.com/music/search/"
    search_url = base_url + urllib.parse.quote(search_query) + "/"
    
    logger.info(f"🔍 Pixabay Music 검색: {search_query}")
    logger.info(f"   URL: {search_url}")
    
    driver = setup_driver(headless=False)  # 브라우저 보이기
    if not driver:
        return None
    
    try:
        # 검색 페이지 열기
        driver.get(search_url)
        time.sleep(3)
        
        # 트랙 링크 찾기
        try:
            track_links = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/music/']"))
            )
        except TimeoutException:
            logger.warning("트랙을 찾을 수 없습니다.")
            return None
        
        # 고유한 트랙 URL만 추출
        unique_tracks = set()
        for link in track_links:
            href = link.get_attribute('href')
            if href and '/music/' in href and 'search' not in href:
                unique_tracks.add(href)
        
        logger.info(f"발견된 트랙: {len(unique_tracks)}개")
        
        if not unique_tracks:
            logger.warning("다운로드할 트랙이 없습니다.")
            return None
        
        # 첫 번째 트랙 다운로드 시도
        for i, track_url in enumerate(list(unique_tracks)[:max_tracks], 1):
            try:
                logger.info(f"\n트랙 {i}/{min(max_tracks, len(unique_tracks))} 처리 중...")
                driver.get(track_url)
                time.sleep(2)
                
                # 트랙 제목 가져오기
                try:
                    title_elem = driver.find_element(By.TAG_NAME, "h1")
                    title = title_elem.text.strip()
                except:
                    title = f"pixabay_music_{int(time.time())}"
                
                # 파일명 생성
                filename = sanitize_filename(f"{title}.mp3")
                output_path = output_dir / filename
                
                # 이미 존재하면 스킵
                if output_path.exists():
                    logger.info(f"이미 존재: {filename}")
                    return str(output_path)
                
                # 다운로드 버튼 클릭 시도
                try:
                    download_btn = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Download') or contains(@class, 'download') or contains(@href, 'download')]"))
                    )
                    driver.execute_script("arguments[0].click();", download_btn)
                    time.sleep(3)
                except:
                    pass
                
                # MP3 URL 찾기
                mp3_url = find_mp3_url(driver, track_url)
                
                if not mp3_url:
                    logger.warning(f"MP3 URL을 찾을 수 없습니다: {title}")
                    continue
                
                # 다운로드
                logger.info(f"다운로드 중: {title}")
                try:
                    response = requests.get(mp3_url, stream=True, timeout=30)
                    response.raise_for_status()
                    
                    with open(output_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    file_size = output_path.stat().st_size / (1024 * 1024)  # MB
                    logger.info(f"✅ 다운로드 완료: {filename} ({file_size:.2f}MB)")
                    return str(output_path)
                    
                except Exception as e:
                    logger.warning(f"다운로드 실패: {e}")
                    if output_path.exists():
                        output_path.unlink()
                    continue
                
            except Exception as e:
                logger.error(f"트랙 처리 실패: {e}")
                continue
        
        return None
        
    finally:
        driver.quit()


def download_background_music(
    book_title: str,
    book_info: Optional[Dict] = None,
    output_dir: Optional[Path] = None,
    preferred_mood: Optional[str] = None
) -> Optional[str]:
    """
    책 분위기에 맞는 배경음악 다운로드
    
    Args:
        book_title: 책 제목
        book_info: 책 정보 딕셔너리 (선택사항)
        output_dir: 출력 디렉토리 (기본값: assets/music)
        preferred_mood: 선호하는 분위기 (예: 'calm', 'epic', 'emotional')
        
    Returns:
        다운로드된 음악 파일 경로 또는 None
    """
    if output_dir is None:
        output_dir = Path("assets/music")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 책 분위기 분석
    logger.info("🎵 책 분위기 분석 중...")
    keywords = analyze_book_mood(book_title, book_info)
    
    if preferred_mood:
        keywords.insert(0, preferred_mood)
    
    logger.info(f"   추천 키워드: {', '.join(keywords)}")
    logger.info("")
    
    # Freesound API 시도
    logger.info("🔍 Freesound에서 음악 검색 중...")
    music_info = search_freesound(keywords)
    
    if music_info and music_info.get('preview_url'):
        try:
            logger.info(f"   ✅ 음악 발견: {music_info['name']}")
            logger.info(f"   📄 라이선스: {music_info.get('license', 'Unknown')}")
            
            # 음악 다운로드
            preview_url = music_info['preview_url']
            response = requests.get(preview_url, timeout=30)
            response.raise_for_status()
            
            # 파일명 생성
            safe_title = get_standard_safe_title(book_title)
            output_file = output_dir / f"{safe_title}_background.mp3"
            
            with open(output_file, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"   ✅ 다운로드 완료: {output_file.name}")
            return str(output_file)
            
        except Exception as e:
            logger.warning(f"   ⚠️ 다운로드 실패: {e}")
    
    # Freesound 실패 시 Pixabay Music 자동 다운로드 시도
    logger.info("")
    logger.info("💡 Freesound 실패, Pixabay Music에서 자동 다운로드 시도...")
    logger.info("")
    
    # Pixabay Music에서 자동 다운로드
    downloaded_file = download_mp3_from_pixabay(keywords, output_dir, max_tracks=1)
    
    if downloaded_file:
        logger.info("")
        logger.info("✅ Pixabay Music에서 다운로드 완료!")
        return downloaded_file
    
    # 자동 다운로드 실패 시 브라우저 열기
    logger.info("")
    logger.info("💡 자동 다운로드 실패, 브라우저에서 수동 다운로드하세요.")
    logger.info("")
    
    # Pixabay Music 검색 URL 생성
    main_keywords = keywords[:3] if keywords else ['ambient', 'calm', 'cinematic']
    search_query = ' '.join(main_keywords)
    pixabay_url = f"https://pixabay.com/music/search/{urllib.parse.quote(search_query)}/"
    
    logger.info(f"🔍 검색 키워드: {', '.join(keywords)}")
    logger.info(f"🌐 Pixabay Music 검색 페이지를 엽니다...")
    logger.info(f"   URL: {pixabay_url}")
    logger.info("")
    logger.info("📥 다운로드 방법:")
    logger.info("   1. 브라우저에서 원하는 음악을 선택하세요")
    logger.info("   2. 'Free Download' 버튼을 클릭하세요")
    logger.info("   3. 다운로드한 파일을 input/ 폴더에 넣으세요")
    logger.info("   4. 파일명 예: background.mp3, bgm.mp3, music.mp3")
    logger.info("")
    
    # 브라우저 열기
    try:
        webbrowser.open(pixabay_url)
        logger.info("✅ 브라우저가 열렸습니다!")
    except Exception as e:
        logger.warning(f"⚠️ 브라우저를 열 수 없습니다: {e}")
        logger.info(f"   수동으로 다음 URL을 열어주세요: {pixabay_url}")
    
    return None


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description='책 분위기에 맞는 배경음악 자동 다운로드',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python src/21_download_background_music.py --title "마키아벨리 군주론"
  python src/21_download_background_music.py --title "The Prince" --mood "epic"
        """
    )
    
    parser.add_argument(
        '--title',
        type=str,
        required=True,
        help='책 제목'
    )
    
    parser.add_argument(
        '--mood',
        type=str,
        default=None,
        help='선호하는 음악 분위기 (예: calm, epic, emotional, ambient)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='assets/music',
        help='출력 디렉토리 (기본값: assets/music)'
    )
    
    args = parser.parse_args()
    
    try:
        # 책 정보 로드 (있는 경우)
        safe_title = get_standard_safe_title(args.title)
        book_info_path = Path("assets/images") / safe_title / "book_info.json"
        book_info = None
        if book_info_path.exists():
            book_info = load_book_info(str(book_info_path))
        
        # 배경음악 다운로드
        output_path = download_background_music(
            book_title=args.title,
            book_info=book_info,
            output_dir=Path(args.output_dir),
            preferred_mood=args.mood
        )
        
        if output_path:
            print()
            print("=" * 60)
            print("✅ 배경음악 다운로드 완료!")
            print("=" * 60)
            print(f"📁 저장 위치: {output_path}")
            print()
            print("💡 이 파일을 영상 제작 시 배경음악으로 사용하세요:")
            print(f"   python run_episode_maker.py")
            print(f"   (배경음악 경로: {output_path})")
        else:
            print()
            print("=" * 60)
            print("ℹ️ 자동 다운로드 실패")
            print("=" * 60)
            print("위에 안내된 사이트에서 수동으로 다운로드하세요.")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

