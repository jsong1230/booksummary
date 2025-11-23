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


def load_book_info(book_title: str) -> Optional[Dict]:
    """
    책 정보 로드 (assets/images/{책제목}/book_info.json)
    
    Args:
        book_title: 책 제목
        
    Returns:
        책 정보 딕셔너리 또는 None
    """
    safe_title_str = safe_title(book_title)
    book_info_path = Path("assets/images") / safe_title_str / "book_info.json"
    
    if book_info_path.exists():
        try:
            with open(book_info_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 책 정보 로드 실패: {e}")
            return None
    
    return None

