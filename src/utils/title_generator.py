#!/usr/bin/env python3
"""
인문학적 가치를 강조하는 제목 생성 유틸리티

AI 강조를 피하고 인문학적 호기심을 자극하는 제목을 생성합니다.
"""

from typing import Optional, Dict
import re


def generate_engaging_title(
    book_title: str,
    author: Optional[str] = None,
    language: str = "ko",
    book_info: Optional[Dict] = None
) -> str:
    """
    인문학적 가치를 강조하는 제목 생성
    
    AI 강조를 피하고 인문학적 호기심을 자극하는 제목을 생성합니다.
    
    Args:
        book_title: 책 제목
        author: 저자 이름
        language: 언어 ('ko' 또는 'en')
        book_info: 책 정보 딕셔너리 (선택사항)
        
    Returns:
        생성된 제목
    """
    from src.utils.translations import (
        translate_book_title,
        translate_book_title_to_korean,
        translate_author_name,
        is_english_title
    )
    
    # 책 제목 번역
    if language == "ko":
        if is_english_title(book_title):
            ko_title = translate_book_title_to_korean(book_title)
        else:
            ko_title = book_title
        
        # 작가 이름 번역
        author_ko = ""
        if author:
            if is_english_title(author):
                author_ko = translate_author_name(author)
            else:
                author_ko = author
        
        # 인문학적 가치를 강조하는 제목 패턴 생성
        # 예: "조지 오웰이 경고한 미래가 현실이 되었다 (1984 깊이 읽기)"
        title_patterns = [
            f"{author_ko}이(가) 경고한 미래가 현실이 되었다 ({ko_title} 깊이 읽기)" if author_ko else f"{ko_title}이(가) 예언한 미래가 현실이 되었다",
            f"{author_ko}이(가) 말한 인생의 진실 ({ko_title} 완전 정리)" if author_ko else f"{ko_title}이(가) 전하는 인생의 진실",
            f"{author_ko}이(가) 그려낸 인간의 초상 ({ko_title} 심층 분석)" if author_ko else f"{ko_title}이(가) 그려낸 인간의 초상",
            f"{ko_title}이(가) 던진 질문, 우리는 답할 수 있을까",
            f"{author_ko}이(가) 보여준 세상의 단면 ({ko_title} 해석)" if author_ko else f"{ko_title}이(가) 보여준 세상의 단면",
        ]
        
        # 가장 적합한 패턴 선택 (간단한 휴리스틱)
        # 제목 길이와 키워드 포함 여부를 고려
        best_title = title_patterns[0]  # 기본값
        
        for pattern in title_patterns:
            if len(pattern) <= 80 and ko_title in pattern:
                best_title = pattern
                break
        
        return best_title
        
    else:  # en
        if not is_english_title(book_title):
            en_title = translate_book_title(book_title)
        else:
            en_title = book_title
        
        # 작가 이름 번역
        author_en = ""
        if author:
            if not is_english_title(author):
                author_en = translate_author_name(author)
            else:
                author_en = author
        
        # 인문학적 가치를 강조하는 제목 패턴 생성
        title_patterns = [
            f"The Future {author_en} Warned Us About ({en_title} Deep Dive)" if author_en else f"The Future {en_title} Predicted",
            f"The Truth {author_en} Revealed ({en_title} Complete Analysis)" if author_en else f"The Truth {en_title} Reveals",
            f"The Human Portrait {author_en} Drew ({en_title} In-Depth Review)" if author_en else f"The Human Portrait {en_title} Draws",
            f"The Question {en_title} Asks: Can We Answer?",
            f"The World {author_en} Showed Us ({en_title} Interpretation)" if author_en else f"The World {en_title} Shows Us",
        ]
        
        # 가장 적합한 패턴 선택
        best_title = title_patterns[0]  # 기본값
        
        for pattern in title_patterns:
            if len(pattern) <= 80 and en_title in pattern:
                best_title = pattern
                break
        
        return best_title


def generate_value_focused_title(
    book_title: str,
    author: Optional[str] = None,
    language: str = "ko",
    book_info: Optional[Dict] = None,
    use_ai_title: bool = False  # AI 생성 제목 사용 여부 (기본값: False)
) -> str:
    """
    가치 중심 제목 생성 (AI 강조 제거)
    
    use_ai_title이 False이면 인문학적 가치를 강조하는 제목을 생성합니다.
    use_ai_title이 True이면 기존 형식을 유지합니다 (하위 호환성).
    
    Args:
        book_title: 책 제목
        author: 저자 이름
        language: 언어 ('ko' 또는 'en')
        book_info: 책 정보 딕셔너리 (선택사항)
        use_ai_title: AI 강조 제목 사용 여부 (기본값: False)
        
    Returns:
        생성된 제목
    """
    if use_ai_title:
        # 기존 형식 유지 (하위 호환성)
        from src.utils.translations import (
            translate_book_title,
            translate_book_title_to_korean,
            translate_author_name,
            is_english_title
        )
        
        if language == "ko":
            if is_english_title(book_title):
                ko_title = translate_book_title_to_korean(book_title)
            else:
                ko_title = book_title
            
            author_part = ""
            if author:
                if is_english_title(author):
                    author_ko = translate_author_name(author)
                    author_part = f" {author_ko}"
                else:
                    author_part = f" {author}"
            
            return f"[핵심 요약] {ko_title} 핵심 정리{author_part}"
        else:
            if not is_english_title(book_title):
                en_title = translate_book_title(book_title)
            else:
                en_title = book_title
            
            author_part = ""
            if author:
                if not is_english_title(author):
                    author_en = translate_author_name(author)
                    author_part = f" {author_en}"
                else:
                    author_part = f" {author}"
            
            return f"[Summary] {en_title} Book Review{author_part}"
    else:
        # 인문학적 가치 강조 제목 생성
        return generate_engaging_title(book_title, author, language, book_info)
