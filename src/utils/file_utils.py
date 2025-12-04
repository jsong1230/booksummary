"""
파일 관련 유틸리티 함수
"""

import json
from pathlib import Path
from typing import Optional, Dict


def safe_title(title: str) -> str:
    """
    파일명으로 사용할 수 있도록 안전한 제목으로 변환
    
    Args:
        title: 원본 제목
        
    Returns:
        안전한 파일명
    """
    safe = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
    safe = safe.replace(' ', '_')
    return safe


def load_book_info(book_title: str, author: str = None) -> Optional[Dict]:
    """
    책 정보 로드 (assets/images/{책제목}/book_info.json)
    description이 없으면 Google Books API에서 다시 가져옴
    
    Args:
        book_title: 책 제목
        author: 저자 이름 (description이 없을 때 Google Books API 호출용)
        
    Returns:
        책 정보 딕셔너리 또는 None
    """
    safe_title_str = safe_title(book_title)
    book_info_path = Path("assets/images") / safe_title_str / "book_info.json"
    
    book_info = None
    if book_info_path.exists():
        try:
            with open(book_info_path, 'r', encoding='utf-8') as f:
                book_info = json.load(f)
        except Exception as e:
            print(f"⚠️ 책 정보 로드 실패: {e}")
            return None
    
    # description이 없거나 빈 문자열이면 Google Books API에서 다시 가져오기
    if book_info and (not book_info.get('description') or book_info.get('description', '').strip() == ''):
        print(f"📖 책 소개가 없어서 Google Books API에서 다시 가져오는 중...")
        try:
            # ImageDownloader를 사용하여 Google Books API에서 정보 가져오기
            import importlib.util
            images_spec = importlib.util.spec_from_file_location("get_images", Path(__file__).parent.parent / "src" / "02_get_images.py")
            images_module = importlib.util.module_from_spec(images_spec)
            images_spec.loader.exec_module(images_module)
            
            downloader = images_module.ImageDownloader()
            # download_book_cover를 호출하면 book_info.json이 업데이트됨
            downloader.download_book_cover(book_title, author, output_dir=Path("assets/images") / safe_title_str)
            
            # 다시 로드
            if book_info_path.exists():
                with open(book_info_path, 'r', encoding='utf-8') as f:
                    book_info = json.load(f)
        except Exception as e:
            print(f"⚠️ Google Books API에서 책 정보를 가져오는 중 오류 발생: {e}")
            # 기존 book_info 반환 (description 없이)
    
    return book_info

