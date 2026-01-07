#!/usr/bin/env python3
"""
일당백 에피소드 영상 메타데이터 생성 스크립트

Part 1과 Part 2로 구성된 에피소드 영상의 메타데이터를 생성합니다.
"""

import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Tuple, List

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.file_utils import get_standard_safe_title
from src.utils.logger import setup_logger
from src.utils.translations import translate_book_title, translate_author_name, translate_book_title_to_korean, is_english_title

# 로거 설정
logger = setup_logger(__name__)


def contains_korean(text: str) -> bool:
    """
    텍스트에 한국어 문자가 포함되어 있는지 확인
    
    Args:
        text: 확인할 텍스트
        
    Returns:
        한국어 문자가 포함되어 있으면 True
    """
    import re
    korean_pattern = re.compile(r'[가-힣]')
    return bool(korean_pattern.search(text))


def remove_korean_from_text(text: str) -> str:
    """
    텍스트에서 한국어 문자를 제거
    
    Args:
        text: 처리할 텍스트
        
    Returns:
        한국어가 제거된 텍스트
    """
    import re
    korean_pattern = re.compile(r'[가-힣]')
    return korean_pattern.sub('', text).strip()


def ensure_english_only(text: str, fallback: str = "") -> str:
    """
    텍스트가 영어만 포함하도록 보장 (한국어가 있으면 제거)
    
    Args:
        text: 확인할 텍스트
        fallback: 한국어가 포함되어 있고 제거 후 빈 문자열이 되면 사용할 기본값
        
    Returns:
        영어만 포함된 텍스트
    """
    if not text:
        return fallback
    
    if contains_korean(text):
        cleaned = remove_korean_from_text(text)
        if not cleaned.strip():
            return fallback
        return cleaned.strip()
    
    return text


def detect_book_genre(book_title: str, book_info: Optional[Dict] = None) -> Tuple[str, str]:
    """
    책의 장르를 감지하여 한글/영문 용어 반환
    
    Args:
        book_title: 책 제목
        book_info: 책 정보 딕셔너리 (선택사항)
        
    Returns:
        (한글_용어, 영문_용어) 튜플
        예: ("소설", "Novel"), ("시", "Poetry"), ("수필", "Essay"), ("작품", "Work")
    """
    title_lower = book_title.lower()
    
    # book_info에서 categories 확인
    if book_info and 'categories' in book_info:
        categories = book_info['categories']
        for category in categories:
            category_lower = category.lower()
            if '소설' in category_lower or 'novel' in category_lower or 'fiction' in category_lower:
                return ("소설", "Novel")
            elif '시' in category_lower or 'poetry' in category_lower or 'poem' in category_lower:
                return ("시", "Poetry")
            elif '수필' in category_lower or 'essay' in category_lower:
                return ("수필", "Essay")
            elif '논픽션' in category_lower or 'non-fiction' in category_lower or 'nonfiction' in category_lower:
                return ("인문학", "Humanities")
            elif '철학' in category_lower or 'philosophy' in category_lower:
                return ("철학", "Philosophy")
            elif '과학' in category_lower or 'science' in category_lower:
                return ("과학", "Science")
            elif '경제' in category_lower or 'economy' in category_lower or 'business' in category_lower:
                return ("경제경영", "Business")
            elif '자기계발' in category_lower or 'self-help' in category_lower:
                return ("자기계발", "SelfHelp")
            elif '역사' in category_lower or 'history' in category_lower:
                return ("역사", "History")
    
    # 제목에서 키워드로 장르 추정
    # 주의: "소설"을 먼저 체크 (다른 단어에 포함될 수 있으므로)
    # 예: "경의를 표하시오"에 "시"가 포함되지만, "소설"이 더 명확한 장르 지표
    import re
    
    # 한글의 경우 단어 경계를 정확히 체크하기 어려우므로, 더 긴 패턴을 우선 체크
    # "소설" 관련 패턴 (우선순위 높음)
    if re.search(r'소설', book_title) or 'novel' in title_lower or 'fiction' in title_lower:
        return ("소설", "Novel")
    # "시" 관련 패턴 - "시집", "시인", "시선" 등 명확한 패턴만 체크
    # 단, "경의", "시각", "시장" 등은 제외하기 위해 더 긴 패턴 우선
    elif re.search(r'시집|시인|시선|시화', book_title) or 'poetry' in title_lower or 'poem' in title_lower:
        return ("시", "Poetry")
    # "수필" 관련 패턴
    elif re.search(r'수필', book_title) or 'essay' in title_lower:
        return ("수필", "Essay")
    # "철학" 관련 패턴
    elif re.search(r'철학', book_title) or 'philosophy' in title_lower:
        return ("철학", "Philosophy")
    # "과학" 관련 패턴
    elif re.search(r'과학', book_title) or 'science' in title_lower:
        return ("과학", "Science")
    # "경제/경영" 관련 패턴
    elif re.search(r'경제|경영|부자|돈', book_title) or 'economy' in title_lower or 'business' in title_lower or 'marketing' in title_lower:
        return ("경제경영", "Business")
    # "역사" 관련 패턴
    elif re.search(r'역사', book_title) or 'history' in title_lower:
        return ("역사", "History")
    # "논픽션" 관련 패턴
    elif '논픽션' in book_title or 'non-fiction' in title_lower or 'nonfiction' in title_lower:
        return ("인문학", "Humanities")
    
    # 기본값: 소설 (하위 호환성)
    return ("소설", "Novel")


def generate_episode_title(book_title: str, language: str = "ko", book_info: Optional[Dict] = None) -> str:
    """
    에피소드 영상 제목 생성
    
    Args:
        book_title: 책 제목
        language: 언어 ('ko' 또는 'en')
        book_info: 책 정보 딕셔너리 (선택사항, 장르 감지용)
        
    Returns:
        생성된 제목
    """
    # 장르 감지
    genre_ko, genre_en = detect_book_genre(book_title, book_info)
    
    # 책 제목 번역
    if language == "ko":
        if is_english_title(book_title):
            ko_title = translate_book_title_to_korean(book_title)
            en_title = book_title
        else:
            ko_title = book_title
            en_title = translate_book_title(book_title)
            
        # 작가 이름 가져오기
        author_name = ""
        if book_info and 'author' in book_info:
            author = book_info['author']
            # 영문 작가명이면 한글로 번역 시도
            if is_english_title(author):
                author_ko = translate_author_name(author)
                author_name = f" {author_ko}"
            else:
                author_name = f" {author}"
        
        return f"[한국어] {ko_title} 책 리뷰{author_name} | [Korean] {en_title} Book Review"
    else:
        if not is_english_title(book_title):
            en_title = translate_book_title(book_title)
            ko_title = book_title
        else:
            en_title = book_title
            ko_title = translate_book_title_to_korean(book_title)
            
        # 작가 이름 가져오기
        author_name = ""
        if book_info and 'author' in book_info:
            author = book_info['author']
            # 한글 작가명이면 영문으로 번역 시도
            if not is_english_title(author):
                author_en = translate_author_name(author)
                author_name = f" {author_en}"
            else:
                author_name = f" {author}"
                
        return f"[English] {en_title} Book Review{author_name} | [영어] {ko_title} 책 리뷰"


def detect_part_count(book_title: str, language: str = "ko") -> int:
    """
    Part 개수를 동적으로 감지
    
    Args:
        book_title: 책 제목
        language: 언어 ('ko' 또는 'en')
        
    Returns:
        Part 개수
    """
    safe_title = get_standard_safe_title(book_title)
    lang_suffix = "_ko" if language == "ko" else "_en"
    input_dir = Path("assets/notebooklm") / safe_title / language
    
    part_count = 0
    part_num = 1
    while True:
        video_file = input_dir / f"part{part_num}_video{lang_suffix}.mp4"
        if video_file.exists():
            part_count += 1
            part_num += 1
        else:
            break
    
    return part_count


def generate_episode_description(book_title: str, language: str = "ko", video_duration: Optional[float] = None, book_info: Optional[Dict] = None) -> str:
    """
    에피소드 영상 설명 생성
    
    Args:
        book_title: 책 제목
        language: 언어 ('ko' 또는 'en')
        video_duration: 영상 길이 (초, 선택사항)
        book_info: 책 정보 딕셔너리 (선택사항, 장르 감지용)
        
    Returns:
        생성된 설명
    """
    # 장르 감지
    genre_ko, genre_en = detect_book_genre(book_title, book_info)
    
    # Part 개수 동적 감지
    part_count = detect_part_count(book_title, language)
    if part_count == 0:
        part_count = 2  # 기본값 (하위 호환성)
    
    # 책 제목 번역
    if language == "ko":
        if is_english_title(book_title):
            ko_title = translate_book_title_to_korean(book_title)
            en_title = book_title
        else:
            ko_title = book_title
            en_title = translate_book_title(book_title)
        
        # 작가 정보
        author_info = ""
        if book_info and 'author' in book_info:
            author_info = f"저자: {book_info['author']}"
            
        # Part 개수에 따라 설명 동적 생성
        part_desc_list = []
        if part_count == 1:
            part_desc_list.append("• Part 1: 작가와 배경 - 작가의 생애와 작품 배경")
        elif part_count == 2:
            part_desc_list.append("• Part 1: 작가와 배경 - 작가의 생애와 작품 배경")
            part_desc_list.append(f"• Part 2: {genre_ko} 줄거리 - 전체 스토리와 주요 인물")
        elif part_count == 3:
            part_desc_list.append("• Part 1: 작가와 배경 - 작가의 생애와 작품 배경")
            part_desc_list.append(f"• Part 2: {genre_ko} 줄거리 (상) - 스토리 전반부와 주요 인물")
            part_desc_list.append(f"• Part 3: {genre_ko} 줄거리 (하) - 스토리 후반부와 결말")
        else:
            for i in range(1, part_count + 1):
                if i == 1:
                    part_desc_list.append(f"• Part {i}: 작가와 배경 - 작가의 생애와 작품 배경")
                else:
                    part_desc_list.append(f"• Part {i}: {genre_ko} 줄거리 - 스토리 {i-1}부")
        part_description = "\n".join(part_desc_list)
        
        # 타임스탬프 생성
        timestamps = ""
        if video_duration:
            current_time = 0.0
            ts_lines = []
            for i in range(1, part_count + 1):
                if i == 1:
                    part_duration = video_duration * (0.35 if part_count >= 2 else 1.0)
                elif i == part_count:
                    part_duration = video_duration - current_time
                else:
                    remaining_time = video_duration - current_time
                    part_duration = remaining_time / (part_count - i + 1)
                
                minutes = int(current_time // 60)
                seconds = int(current_time % 60)
                
                if i == 1:
                    ts_lines.append(f"{minutes}:{seconds:02d} - Part {i}: 작가와 배경")
                elif part_count == 2 and i == 2:
                    ts_lines.append(f"{minutes}:{seconds:02d} - Part {i}: {genre_ko} 줄거리")
                elif part_count == 3:
                    if i == 2:
                        ts_lines.append(f"{minutes}:{seconds:02d} - Part {i}: {genre_ko} 줄거리 (상)")
                    elif i == 3:
                        ts_lines.append(f"{minutes}:{seconds:02d} - Part {i}: {genre_ko} 줄거리 (하)")
                else:
                    ts_lines.append(f"{minutes}:{seconds:02d} - Part {i}: {genre_ko} 줄거리 {i-1}부")
                
                current_time += part_duration
            timestamps = "\n".join(ts_lines)

        description = f"""{timestamps}

📚 책 리뷰 영상 | 독서 | 북튜버 | 책추천

📖 영상 구성:
이 영상은 다음 내용을 포함합니다:
{part_description}

📘 책 소개:
{ko_title} ({en_title})
{author_info}

이 영상은 일당백 채널의 {part_count}편의 영상을 하나로 합친 완전판입니다.
NotebookLM의 심층 분석과 함께 작품을 깊이 있게 이해해보세요.

🎯 주요 내용:
✓ 작가의 생애와 작품 세계 상세 분석
✓ 작품의 시대적 배경과 숨겨진 의미
✓ {genre_ko}의 전체 줄거리와 핵심 메시지

💡 일당백 채널에서 더 많은 작품을 만나보세요!
🔔 구독과 좋아요는 다음 영상 제작에 큰 힘이 됩니다!
💬 댓글로 여러분의 생각을 공유해주세요!

#일당백 #{ko_title.replace(' ', '')} #책리뷰 #문학 #{genre_ko} #작가 #{author_info.replace('저자: ', '').replace(' ', '') if author_info else '문학작품'}"""
        
    else:  # en
        if not is_english_title(book_title):
            en_title = translate_book_title(book_title)
            if not en_title or not is_english_title(en_title):
                en_title = "This Book" if not en_title else en_title
        else:
            en_title = book_title
        
        if not is_english_title(en_title):
            en_title = "This Book"

        # Author info
        author_info = ""
        if book_info and 'author' in book_info:
             author_val = book_info['author']
             if not is_english_title(author_val):
                 author_val = translate_author_name(author_val)
             if author_val and is_english_title(author_val):
                 author_info = f"Author: {author_val}"
        
        # Part description
        part_desc_list = []
        if part_count == 1:
            part_desc_list.append("• Part 1: Author & Background - Author's life and work context")
        elif part_count == 2:
            part_desc_list.append("• Part 1: Author & Background - Author's life and work context")
            part_desc_list.append(f"• Part 2: {genre_en} Summary - Full story and main characters")
        elif part_count == 3:
            part_desc_list.append("• Part 1: Author & Background - Author's life and work context")
            part_desc_list.append(f"• Part 2: {genre_en} Summary (Part 1) - First half of the story and main characters")
            part_desc_list.append(f"• Part 3: {genre_en} Summary (Part 2) - Second half of the story and conclusion")
        else:
            for i in range(1, part_count + 1):
                if i == 1:
                    part_desc_list.append(f"• Part {i}: Author & Background - Author's life and work context")
                else:
                    part_desc_list.append(f"• Part {i}: {genre_en} Summary - Story Part {i-1}")
        part_description = "\n".join(part_desc_list)

        # Timestamps
        timestamps = ""
        if video_duration:
            current_time = 0.0
            ts_lines = []
            for i in range(1, part_count + 1):
                if i == 1:
                    part_duration = video_duration * (0.35 if part_count >= 2 else 1.0)
                elif i == part_count:
                    part_duration = video_duration - current_time
                else:
                    remaining_time = video_duration - current_time
                    part_duration = remaining_time / (part_count - i + 1)
                
                minutes = int(current_time // 60)
                seconds = int(current_time % 60)
                
                if i == 1:
                    ts_lines.append(f"{minutes}:{seconds:02d} - Part {i}: Author & Background")
                elif part_count == 2 and i == 2:
                    ts_lines.append(f"{minutes}:{seconds:02d} - Part {i}: {genre_en} Summary")
                elif part_count == 3:
                    if i == 2:
                        ts_lines.append(f"{minutes}:{seconds:02d} - Part {i}: {genre_en} Summary (Part 1)")
                    elif i == 3:
                        ts_lines.append(f"{minutes}:{seconds:02d} - Part {i}: {genre_en} Summary (Part 2)")
                else:
                    ts_lines.append(f"{minutes}:{seconds:02d} - Part {i}: {genre_en} Summary Part {i-1}")
                
                current_time += part_duration
            timestamps = "\n".join(ts_lines)
        
        safe_en_title = ensure_english_only(en_title.replace(' ', '').replace(':', '').replace('-', ''), "Book")
        safe_genre_en = ensure_english_only(genre_en.replace(' ', ''), "Work")
        
        description = f"""{timestamps}

📚 Book Review | Reading | BookTube | Recommendation

📖 Video Structure:
{part_description}

📘 Book Info:
{en_title}
{author_info}

This video combines {part_count} episodes from 1DANG100 channel into one complete guide.
Deep dive into the masterpiece with NotebookLM analysis.

🎯 What You'll Learn:
✓ Author's life and literary world
✓ Historical background and significance
✓ Complete story structure and plot

💡 Check out 1DANG100 channel for more literary works!
🔔 Subscribe and like to support future videos!
💬 Share your thoughts in the comments!

#{safe_en_title} #BookReview #Literature #{safe_genre_en} #Author #LiteraryWork"""
        
        # 최종 검증: description에서 한국어 제거
        if language == "en":
            # description 전체에서 한국어가 포함된 부분 제거
            lines = description.split('\n')
            cleaned_lines = []
            for line in lines:
                if contains_korean(line):
                    # 한국어가 포함된 라인은 제거하거나 한국어만 제거
                    cleaned_line = remove_korean_from_text(line)
                    if cleaned_line.strip():
                        cleaned_lines.append(cleaned_line)
                else:
                    cleaned_lines.append(line)
            description = '\n'.join(cleaned_lines)
    
    return description


def generate_episode_tags(book_title: str, language: str = "ko", book_info: Optional[Dict] = None) -> list:
    """
    에피소드 영상 태그 생성 (YouTube 최대치: 500자, 태그당 30자)
    
    Args:
        book_title: 책 제목
        language: 언어 ('ko' 또는 'en')
        book_info: 책 정보 (Optional)
        
    Returns:
        생성된 태그 리스트
    """
    from src.utils.file_utils import load_book_info
    
    # 책 정보 로드 시도 (인자로 전달되지 않은 경우)
    if not book_info:
        try:
            safe_title = get_standard_safe_title(book_title)
            book_info = load_book_info(safe_title)
        except:
            pass
            
    # 장르 감지
    genre_ko, genre_en = detect_book_genre(book_title, book_info)
    
    # 책 제목 번역
    if language == "ko":
        if is_english_title(book_title):
            ko_title = translate_book_title_to_korean(book_title)
            en_title = book_title
        else:
            ko_title = book_title
            en_title = translate_book_title(book_title)
        
        # 작가 이름 추출
        author_name = None
        if book_info and 'author' in book_info:
            author_name = book_info['author']
            # 한글 작가 이름도 번역
            if author_name:
                author_ko = translate_author_name(author_name) if is_english_title(author_name) else author_name
        
        # 책 제목에서 핵심 키워드 추출 (태그용)
        # 제목을 공백/구두점으로 분리하여 핵심 단어만 추출
        import re
        # 한글 제목에서 핵심 키워드 추출 (구두점, 특수문자 제거)
        ko_title_clean = re.sub(r'[:\-\(\)\[\]「」]', ' ', ko_title)
        ko_keywords = [word.strip() for word in ko_title_clean.split() if len(word.strip()) > 1]
        # 가장 중요한 키워드 선택 (처음 2-3개 단어)
        ko_main_keyword = ''.join(ko_keywords[:2]) if len(ko_keywords) >= 2 else ''.join(ko_keywords)
        ko_main_keyword = ko_main_keyword[:15]  # 최대 15자로 제한
        
        # 영어 제목도 동일하게 처리
        en_title_clean = re.sub(r'[:\-\(\)\[\]「」]', ' ', en_title)
        en_keywords = [word.strip() for word in en_title_clean.split() if len(word.strip()) > 1]
        en_main_keyword = ' '.join(en_keywords[:2]) if len(en_keywords) >= 2 else ' '.join(en_keywords)
        en_main_keyword = en_main_keyword[:20]  # 최대 20자로 제한
        
        tags = [
            # 채널 및 시리즈
            "일당백",
            "일당백책리뷰",
            "일당백문학",
            
            # 책 제목 핵심 키워드 (자연스러운 태그)
            ko_main_keyword if ko_main_keyword else ko_title[:15],
            f"{ko_main_keyword}리뷰" if ko_main_keyword and len(ko_main_keyword) + 2 <= 30 else "책리뷰",
            f"{ko_main_keyword}분석" if ko_main_keyword and len(ko_main_keyword) + 2 <= 30 else "책분석",
            
            # 작가 관련
            "작가",
            "작가분석",
            "작가이야기",
            "작가생애",
            "문학작가",
        ]
        
        # 작가 이름이 있으면 추가
        if author_name:
            if not is_english_title(author_name):
                author_ko = author_name
                author_en = translate_author_name(author_name)
            else:
                author_en = author_name
                author_ko = translate_author_name(author_name)
            
            tags.extend([
                f"{author_ko}",
                f"{author_ko}작품",
                f"{author_ko}{genre_ko}",
                f"{author_en}",
                f"{author_en}Book",
            ])
            
        # 1. 기본 태그 (검색량 높은 순)
        basic_tags = [
            "책리뷰", "독서", "북튜버", "책추천", "독서법", "책읽기", "서평", "독후감",
            "BookReview", "Reading", "BookTube", "BookRecommendation"
        ]
        
        # 2. 장르 태그
        genre_tags = [
            f"{genre_ko}", f"{genre_ko}추천", f"{genre_ko}베스트셀러",
            "베스트셀러", "스테디셀러", "추천도서", "권장도서",
            "인문학", "교양", "지식", "공부",
        ]
        if genre_ko == "소설":
            genre_tags.extend(["문학", "소설리뷰", "문학작품", "고전문학", "세계문학"])
        elif genre_ko == "철학":
            genre_tags.extend(["철학책", "철학입문", "인문학강의"])
        elif genre_ko == "경제경영":
            genre_tags.extend(["경제공부", "주식", "투자", "성공", "부자"])
        elif genre_ko == "자기계발":
            genre_tags.extend(["동기부여", "성장", "성공학", "마인드셋"])
            
        # 현재 연도 가져오기
        current_year = datetime.now().year
            
        # 3. 기관/트렌드 태그
        trend_tags = [
            f"책추천{current_year}", "독서챌린지", "독서모임", "일당백", "일당백책리뷰"
        ]
        
        # 태그 합치기 (우선순위대로)
        # 이미 추가된 tags(제목/작가) + 기본 + 장르 + 트렌드
        tags = tags + basic_tags + genre_tags + trend_tags
        
    else:  # en
        if not is_english_title(book_title):
            en_title = translate_book_title(book_title)
            # 번역이 실패하거나 한국어가 그대로 남아있는 경우 처리
            if not en_title or not is_english_title(en_title):
                en_title = "Book"  # 기본값
        else:
            en_title = book_title
        
        # 한국어가 포함되어 있지 않은지 최종 확인
        if not is_english_title(en_title):
            en_title = "Book"
        
        # 작가 이름 추출
        author_name = None
        if book_info and 'author' in book_info:
            author_name = book_info['author']
            # 작가 이름도 영어로 변환
            if author_name and not is_english_title(author_name):
                author_name = translate_author_name(author_name)
                # 번역 실패 시 None으로 설정 (한국어 작가 이름 제거)
                if not author_name or not is_english_title(author_name):
                    author_name = None
        
        # 책 제목에서 핵심 키워드 추출 (태그용)
        import re
        # 영어 제목에서 핵심 키워드 추출 (한국어 제외)
        en_title_clean = re.sub(r'[:\-\(\)\[\]「」]', ' ', en_title)
        en_keywords = [word.strip() for word in en_title_clean.split() if len(word.strip()) > 1 and is_english_title(word.strip())]
        en_main_keyword = ' '.join(en_keywords[:2]) if len(en_keywords) >= 2 else ' '.join(en_keywords)
        en_main_keyword = en_main_keyword[:20]  # 최대 20자로 제한
        
        # en_main_keyword가 한국어를 포함하거나 비어있는 경우 처리
        if not en_main_keyword or not is_english_title(en_main_keyword):
            en_main_keyword = None
        
        # en_title도 한국어가 포함되지 않도록 확인
        safe_en_title = en_title[:20] if is_english_title(en_title) else "Book"
        
        tags = [
            # Channel & Series
            "1DANG100",
            "1DANG100BookReview",
            "1DANG100Literature",
            
            # Book Title (핵심 키워드만, 영어만)
            en_main_keyword if en_main_keyword else safe_en_title,
            f"{en_main_keyword}Review" if en_main_keyword and len(en_main_keyword) + 6 <= 30 else "BookReview",
            f"{en_main_keyword}Analysis" if en_main_keyword and len(en_main_keyword) + 8 <= 30 else "BookAnalysis",
            f"{en_main_keyword}Summary" if en_main_keyword and len(en_main_keyword) + 7 <= 30 else "BookSummary",
            f"{en_main_keyword}Guide" if en_main_keyword and len(en_main_keyword) + 5 <= 30 else "BookGuide",
            
            # Author related
            "Author",
            "AuthorAnalysis",
            "AuthorBiography",
            "LiteraryAuthor",
        ]
        
        # Add author name if available (영어만)
        if author_name and is_english_title(author_name):
            tags.extend([
                f"{author_name}",
                f"{author_name}Book",
                f"{author_name}{genre_en}",
            ])
        
        # 1. Basic Tags (High Volume)
        basic_tags = [
            "BookReview", "Reading", "BookTube", "BookRecommendation", "Books",
            "BookSummary", "Audiobook", "Literature", "Bestseller"
        ]
        
        # 2. Genre Tags
        genre_tags = [
            f"{genre_en}", f"{genre_en}Review", f"{genre_en}Recommendation",
            "ClassicLiterature", "ModernLiterature", "MustRead",
            "SelfImprovement" if genre_en == "SelfHelp" else "Education"
        ]
        if genre_en == "Novel":
            genre_tags.extend(["Fiction", "Story", "NovelReview", "LiteraryFiction"])
        elif genre_en == "Philosophy":
            genre_tags.extend(["PhilosophyBook", "Philosophical", "Wisdom"])
        elif genre_en == "Business":
            genre_tags.extend(["BusinessBook", "Finance", "Success", "Investment"])
        
        # 현재 연도 가져오기
        current_year = datetime.now().year
        
        # 3. Trending/Institution Tags
        trend_tags = [
            "BookTok", "BookLover", f"ReadingChallenge{current_year}", "1DANG100"
        ]
        
        tags = tags + basic_tags + genre_tags + trend_tags
    
    # 태그 정리: 30자 제한, 중복 제거, 한국어 제거 (영문일 경우)
    cleaned_tags = []
    seen = set()
    for tag in tags:
        # 영문 메타데이터인 경우 한국어 제거
        if language == "en":
            if contains_korean(tag):
                # 한국어가 포함된 태그는 제거
                continue
            # 한국어가 없는 경우에도 한 번 더 확인
            tag = ensure_english_only(tag, "")
            if not tag:
                continue
        
        # 30자로 자르기
        tag_cleaned = tag[:30] if len(tag) > 30 else tag
        # 중복 제거
        tag_lower = tag_cleaned.lower()
        if tag_lower not in seen and tag_cleaned.strip():
            seen.add(tag_lower)
            cleaned_tags.append(tag_cleaned)
    
    # YouTube 태그 총 길이 제한: 500자 (쉼표 포함)
    # 각 태그 + 쉼표 = 태그길이 + 1
    # 최대 500자까지 가능
    final_tags = []
    total_length = 0
    
    for tag in cleaned_tags:
        # 태그 + 쉼표 길이
        tag_length = len(tag) + 1  # +1 for comma
        if total_length + tag_length <= 500:
            final_tags.append(tag)
            total_length += tag_length
        else:
            break
    
    return final_tags


def create_episode_metadata(
    book_title: str,
    language: str = "ko",
    video_path: Optional[str] = None,
    thumbnail_path: Optional[str] = None,
    video_duration: Optional[float] = None
) -> Dict:
    """
    에피소드 영상 메타데이터 생성
    
    Args:
        book_title: 책 제목
        language: 언어 ('ko' 또는 'en')
        video_path: 영상 파일 경로 (선택사항)
        thumbnail_path: 썸네일 파일 경로 (선택사항)
        video_duration: 영상 길이 (초, 선택사항)
        
    Returns:
        메타데이터 딕셔너리
    """
    safe_title = get_standard_safe_title(book_title)
    
    # 영상 경로가 없으면 자동으로 찾기
    if not video_path:
        video_path = f"output/{safe_title}_full_episode_{language}.mp4"
    
    video_path_obj = Path(video_path)
    
    # 영상이 존재하는지 확인
    if not video_path_obj.exists():
        logger.warning(f"⚠️ 영상 파일을 찾을 수 없습니다: {video_path}")
        logger.warning("메타데이터는 생성되지만 영상 파일이 없습니다.")
    
    # 썸네일 경로가 없으면 자동으로 찾기
    if not thumbnail_path:
        thumbnail_path = f"output/{safe_title}_thumbnail_{language}.jpg"
    
    thumbnail_path_obj = Path(thumbnail_path)
    
    # 썸네일이 존재하는지 확인
    if not thumbnail_path_obj.exists():
        logger.warning(f"⚠️ 썸네일 파일을 찾을 수 없습니다: {thumbnail_path}")
        thumbnail_path = None
    
    # 영상 길이 확인 (video_duration이 없으면)
    if video_duration is None and video_path_obj.exists():
        try:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(str(video_path_obj))
            video_duration = clip.duration
            clip.close()
        except Exception as e:
            logger.warning(f"⚠️ 영상 길이를 가져올 수 없습니다: {e}")
            video_duration = None
    
    # 책 정보 로드 (장르 감지용)
    book_info = None
    try:
        from src.utils.file_utils import load_book_info
        safe_title = get_standard_safe_title(book_title)
        book_info = load_book_info(safe_title)
    except:
        pass
    
    # 메타데이터 생성
    title = generate_episode_title(book_title, language, book_info)
    description = generate_episode_description(book_title, language, video_duration, book_info)
    tags = generate_episode_tags(book_title, language, book_info)
    
    # 영문 메타데이터인 경우 최종 검증: description과 tags에서 한국어 제거
    if language == "en":
        # description에서 한국어 제거
        if contains_korean(description):
            logger.warning("⚠️ Description에 한국어가 포함되어 있습니다. 제거합니다.")
            lines = description.split('\n')
            cleaned_lines = []
            for line in lines:
                if contains_korean(line):
                    cleaned_line = remove_korean_from_text(line)
                    if cleaned_line.strip():
                        cleaned_lines.append(cleaned_line)
                else:
                    cleaned_lines.append(line)
            description = '\n'.join(cleaned_lines)
        
        # tags에서 한국어 제거
        english_only_tags = []
        for tag in tags:
            if contains_korean(tag):
                logger.warning(f"⚠️ Tag '{tag}'에 한국어가 포함되어 있습니다. 제거합니다.")
                continue
            english_only_tags.append(tag)
        tags = english_only_tags
    
    metadata = {
        'video_path': str(video_path_obj),
        'title': title,
        'description': description,
        'tags': tags,
        'language': language,
        'book_title': book_title,
        'video_duration': video_duration
    }
    
    if thumbnail_path:
        metadata['thumbnail_path'] = str(thumbnail_path_obj)
    
    return metadata


def save_metadata(metadata: Dict, output_path: Optional[str] = None) -> Path:
    """
    메타데이터를 JSON 파일로 저장
    
    Args:
        metadata: 메타데이터 딕셔너리
        output_path: 출력 파일 경로 (None이면 자동 생성)
        
    Returns:
        저장된 파일 경로
    """
    if output_path is None:
        video_path = Path(metadata['video_path'])
        output_path = video_path.with_suffix('.metadata.json')
    else:
        output_path = Path(output_path)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    logger.info(f"💾 메타데이터 저장: {output_path}")
    if metadata.get('thumbnail_path'):
        logger.info(f"   📸 썸네일: {Path(metadata['thumbnail_path']).name}")
    
    return output_path


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description='일당백 에피소드 영상 메타데이터 생성',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python src/20_create_episode_metadata.py --title "마키아벨리 군주론" --language ko
  python src/20_create_episode_metadata.py --title "The Prince" --language en
        """
    )
    
    parser.add_argument(
        '--title',
        type=str,
        required=True,
        help='책 제목'
    )
    
    parser.add_argument(
        '--language',
        type=str,
        default='ko',
        choices=['ko', 'en'],
        help='언어 (기본값: ko)'
    )
    
    parser.add_argument(
        '--video-path',
        type=str,
        default=None,
        help='영상 파일 경로 (기본값: output/{책제목}_full_episode_{언어}.mp4)'
    )
    
    parser.add_argument(
        '--thumbnail-path',
        type=str,
        default=None,
        help='썸네일 파일 경로 (기본값: output/{책제목}_thumbnail_{언어}.jpg)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='메타데이터 출력 파일 경로 (기본값: 영상 파일과 같은 위치)'
    )
    
    parser.add_argument(
        '--preview',
        action='store_true',
        help='메타데이터 미리보기만 출력 (저장하지 않음)'
    )
    
    args = parser.parse_args()
    
    try:
        # 메타데이터 생성
        metadata = create_episode_metadata(
            book_title=args.title,
            language=args.language,
            video_path=args.video_path,
            thumbnail_path=args.thumbnail_path
        )
        
        # 미리보기 출력
        print("=" * 60)
        print("📋 메타데이터 미리보기")
        print("=" * 60)
        print()
        print(f"📖 책 제목: {args.title}")
        print(f"🌐 언어: {args.language.upper()}")
        print()
        print("📝 제목:")
        print(f"   {metadata['title']}")
        print()
        print("📄 설명 (처음 200자):")
        print(f"   {metadata['description'][:200]}...")
        print()
        print(f"🏷️ 태그 ({len(metadata['tags'])}개):")
        for i, tag in enumerate(metadata['tags'][:10], 1):  # 처음 10개만 표시
            print(f"   {i}. {tag}")
        if len(metadata['tags']) > 10:
            print(f"   ... 외 {len(metadata['tags']) - 10}개")
        print()
        
        if metadata.get('video_path'):
            print(f"🎬 영상: {Path(metadata['video_path']).name}")
        if metadata.get('thumbnail_path'):
            print(f"📸 썸네일: {Path(metadata['thumbnail_path']).name}")
        if metadata.get('video_duration'):
            minutes = int(metadata['video_duration'] // 60)
            seconds = int(metadata['video_duration'] % 60)
            print(f"⏱️ 길이: {minutes}분 {seconds}초")
        print()
        
        # 저장
        if not args.preview:
            output_path = save_metadata(metadata, args.output)
            print()
            print("=" * 60)
            print("✅ 메타데이터 생성 완료!")
            print("=" * 60)
            print(f"📁 저장 위치: {output_path}")
        else:
            print("ℹ️ 미리보기 모드: 메타데이터를 저장하지 않았습니다.")
            print("   저장하려면 --preview 옵션을 제거하세요.")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

