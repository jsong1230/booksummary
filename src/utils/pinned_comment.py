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
    author: Optional[str] = None,
    validate_links: bool = False,
) -> str:
    """
    고정 댓글 생성

    챕터 타임스탬프, 제휴 링크, 질문을 포함한 고정 댓글을 생성합니다.

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
    from src.utils.affiliate_links import generate_affiliate_section
    
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

        # 제휴 링크 추가
        if is_english_title(book_title):
            en_title = book_title
            ko_title_for_link = ko_title
        else:
            en_title = translate_book_title(book_title)
            ko_title_for_link = ko_title

        author_en = ""
        if author:
            if is_english_title(author):
                author_en = author
            else:
                author_en = translate_author_name(author)

        affiliate_section = generate_affiliate_section(
            book_title_ko=ko_title_for_link,
            book_title_en=en_title,
            author_ko=author_ko,
            author_en=author_en,
            language='ko',
            validate=validate_links,
        )

        if affiliate_section:
            # 제휴 링크 앞뒤 공백 제거 후 추가
            comment += affiliate_section.strip() + "\n\n"

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

        # CTA 강화: 참여 유도 질문 + 구독/다음 책 추천 요청
        comment += f"\n📌 다음에 어떤 책을 리뷰해드릴까요?\n"
        comment += "댓글로 추천해주시면 적극 반영하겠습니다! 📚\n\n"
        comment += "👍 영상이 도움이 되셨다면 좋아요 부탁드립니다!\n"
        comment += "🔔 구독 + 알림 설정으로 새 리뷰 영상을 놓치지 마세요!\n"

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

        # 제휴 링크 추가
        if not is_english_title(book_title):
            ko_title_for_link = book_title
        else:
            ko_title_for_link = translate_book_title_to_korean(book_title)

        author_ko = ""
        if author:
            if not is_english_title(author):
                author_ko = author
            # 영문→한글 저자명 번역은 현재 지원 안 됨

        affiliate_section = generate_affiliate_section(
            book_title_ko=ko_title_for_link,
            book_title_en=en_title,
            author_ko=author_ko,
            author_en=author_en,
            language='en',
            validate=validate_links,
        )

        if affiliate_section:
            # 제휴 링크 앞뒤 공백 제거 후 추가
            comment += affiliate_section.strip() + "\n\n"

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

        # CTA 강화: 참여 유도 + 구독/다음 책 추천 요청
        comment += f"\n📌 What book should I review next?\n"
        comment += "Drop your recommendations in the comments below! 📚\n\n"
        comment += "👍 If this video was helpful, please give it a like!\n"
        comment += "🔔 Subscribe + hit the bell icon so you never miss a new review!\n"

    return comment
