#!/usr/bin/env python3
"""
YouTube 고정 댓글 생성 유틸리티

챕터 타임스탬프와 질문을 포함한 고정 댓글을 생성합니다.
"""

from typing import Optional, Dict, List
from datetime import datetime


def generate_pinned_comment(
    book_title: str,
    timestamps: Optional[Dict] = None,
    language: str = "ko",
    book_info: Optional[Dict] = None,
    author: Optional[str] = None
) -> str:
    """
    고정 댓글 생성
    
    챕터 타임스탬프와 질문을 포함한 고정 댓글을 생성합니다.
    
    Args:
        book_title: 책 제목
        timestamps: 타임스탬프 딕셔너리 (예: {'summary_duration': 300, 'notebooklm_duration': 600})
        language: 언어 ('ko' 또는 'en')
        book_info: 책 정보 딕셔너리 (선택사항)
        author: 저자 이름 (선택사항)
        
    Returns:
        생성된 고정 댓글 텍스트
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
        
        comment = f"📚 {ko_title}"
        if author_ko:
            comment += f" - {author_ko}"
        comment += "\n\n"
        
        # 챕터 타임스탬프 추가
        if timestamps:
            comment += "⏱️ 영상 챕터:\n"
            current_time = 0.0
            
            # Summary 섹션
            if timestamps.get('summary_duration', 0) > 0:
                minutes = int(current_time // 60)
                seconds = int(current_time % 60)
                comment += f"{minutes}:{seconds:02d} - 요약 (Summary)\n"
                current_time += timestamps['summary_duration']
            
            # NotebookLM 섹션
            if timestamps.get('notebooklm_duration', 0) > 0:
                minutes = int(current_time // 60)
                seconds = int(current_time % 60)
                comment += f"{minutes}:{seconds:02d} - NotebookLM 상세 분석\n"
                current_time += timestamps.get('notebooklm_duration', 0)
            
            comment += "\n"
        
        # 질문 추가
        questions = [
            f"여러분이 생각하는 {ko_title}의 명문장은 무엇인가요?",
            f"{ko_title}을(를) 읽으면서 가장 인상 깊었던 부분은 어디인가요?",
            f"{author_ko}의 작품 중 가장 좋아하는 작품은 무엇인가요?" if author_ko else f"{ko_title}과(와) 비슷한 작품을 추천해주세요.",
        ]
        
        comment += "💬 여러분의 생각을 공유해주세요:\n"
        for i, question in enumerate(questions[:2], 1):  # 처음 2개만 사용
            comment += f"{i}. {question}\n"
        
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
        
        comment = f"📚 {en_title}"
        if author_en:
            comment += f" - {author_en}"
        comment += "\n\n"
        
        # 챕터 타임스탬프 추가
        if timestamps:
            comment += "⏱️ Video Chapters:\n"
            current_time = 0.0
            
            # Summary 섹션
            if timestamps.get('summary_duration', 0) > 0:
                minutes = int(current_time // 60)
                seconds = int(current_time % 60)
                comment += f"{minutes}:{seconds:02d} - Summary\n"
                current_time += timestamps['summary_duration']
            
            # NotebookLM 섹션
            if timestamps.get('notebooklm_duration', 0) > 0:
                minutes = int(current_time // 60)
                seconds = int(current_time % 60)
                comment += f"{minutes}:{seconds:02d} - NotebookLM Detailed Analysis\n"
                current_time += timestamps.get('notebooklm_duration', 0)
            
            comment += "\n"
        
        # 질문 추가
        questions = [
            f"What is your favorite quote from {en_title}?",
            f"Which part of {en_title} impressed you the most?",
            f"What is your favorite work by {author_en}?" if author_en else f"Can you recommend a book similar to {en_title}?",
        ]
        
        comment += "💬 Share your thoughts:\n"
        for i, question in enumerate(questions[:2], 1):  # 처음 2개만 사용
            comment += f"{i}. {question}\n"
    
    return comment
