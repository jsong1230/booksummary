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
from src.utils.translations import translate_book_title, translate_author_name, translate_book_title_to_korean, translate_author_name_to_korean, is_english_title
from src.utils.affiliate_links import generate_affiliate_section

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


def generate_episode_title(
    book_title: str,
    language: str = "ko",
    book_info: Optional[Dict] = None,
    author: Optional[str] = None
) -> str:
    """
    에피소드 영상 제목 생성
    
    ⚠️ 중요: 각 언어별로 해당 언어의 제목만 반환합니다.
    YouTube의 다국어 메타데이터 기능을 사용하여 시청자의 언어 설정에 따라 자동으로 표시됩니다.
    
    제목 포맷 규칙:
    - 일당백 스타일: [일당백] 책제목: 작가 (부제목)
    - 부제목은 있으면만 추가합니다.
    
    Args:
        book_title: 책 제목
        language: 언어 ('ko' 또는 'en')
        book_info: 책 정보 딕셔너리 (선택사항, 장르 감지용)
        author: 작가명 (선택사항, book_info에 없을 때 사용)
        
    Returns:
        생성된 제목 (해당 언어만 포함)
    """
    import re

    def _truncate_with_ellipsis(text: str, max_len: int = 100) -> str:
        if len(text) <= max_len:
            return text
        if max_len <= 3:
            return text[:max_len]
        return text[: max_len - 3] + "..."

    def _shrink_subtitle_to_fit(prefix_: str, main_: str, author_part_: str, subtitle: Optional[str]) -> str:
        def _compose(sub: Optional[str]) -> str:
            sub_part = f" ({sub})" if sub else ""
            return f"{prefix_} {main_}{author_part_}{sub_part}"

        cand = _compose(subtitle)
        if len(cand) <= 100:
            return cand

        if subtitle and " · " in subtitle:
            parts = [p.strip() for p in subtitle.split(" · ") if p.strip()]
            for k in range(len(parts) - 1, 0, -1):
                sub2 = " · ".join(parts[:k])
                cand2 = _compose(sub2)
                if len(cand2) <= 100:
                    return cand2

        cand3 = _compose(None)
        if len(cand3) <= 100:
            return cand3

        return _truncate_with_ellipsis(cand3, 100)

    def _split_trailing_parenthetical(text: str):
        m = re.search(r"\s*\(([^)]+)\)\s*$", text or "")
        if not m:
            return (text or "").strip(), None
        main = re.sub(r"\s*\([^)]*\)\s*$", "", text or "").strip()
        sub = (m.group(1) or "").strip() or None
        return main, sub

    prefix = "[일당백]" if language != "en" else "[1DANG100]"

    # 1) 입력에서 메인/부제목 분리
    book_title_main, subtitle_from_input = _split_trailing_parenthetical(book_title)

    # 2) 작가명 결정 (book_info 우선, 없으면 args.author)
    resolved_author = None
    if book_info:
        if isinstance(book_info.get("author"), str) and book_info.get("author").strip():
            resolved_author = book_info.get("author").strip()
        elif isinstance(book_info.get("authors"), list) and book_info.get("authors"):
            first = book_info.get("authors")[0]
            if isinstance(first, str) and first.strip():
                resolved_author = first.strip()
    if not resolved_author and author:
        resolved_author = author.strip()

    # 3) 제목/작가 번역 + SEO 부제목 생성
    try:
        from src.utils.title_generator import generate_seo_subtitle
    except Exception:
        generate_seo_subtitle = None

    def _unique_keep_order(items: List[str]) -> List[str]:
        seen = set()
        out: List[str] = []
        for it in items:
            it2 = (it or "").strip()
            if not it2:
                continue
            if it2 in seen:
                continue
            seen.add(it2)
            out.append(it2)
        return out

    if language == "ko":
        if is_english_title(book_title_main):
            ko_title = translate_book_title_to_korean(book_title_main)
            en_title = book_title_main
        else:
            ko_title = book_title_main
            en_title = translate_book_title(book_title_main)
            if not is_english_title(en_title):
                raise ValueError(
                    f"책 제목 '{book_title}'의 영어 번역을 찾을 수 없습니다. "
                    f"src/utils/translations.py에 매핑을 추가하거나, 영문 원제를 함께 입력하세요."
                )

        ko_author = ""
        if resolved_author:
            if is_english_title(resolved_author):
                ko_author = translate_author_name_to_korean(resolved_author) or resolved_author
            else:
                ko_author = resolved_author

        # 부제목(ko): 실제 부제 + 영문 원제 + SEO 키워드
        subtitle_ko_parts: List[str] = []
        if subtitle_from_input:
            subtitle_ko_parts.append(subtitle_from_input)
        # 한국어 제목에서는 "원래 부제목이 없을 때만" 영문 원제를 함께 넣어 검색을 돕습니다.
        if not subtitle_from_input:
            if en_title and en_title != ko_title and is_english_title(en_title):
                subtitle_ko_parts.append(en_title)
        if generate_seo_subtitle:
            subtitle_ko_parts.append(
                generate_seo_subtitle(
                    "ko",
                    ko_title,
                    author=ko_author or None,
                    book_info=book_info,
                    content_type="full_episode",
                )
            )
        subtitle_ko_parts = _unique_keep_order(subtitle_ko_parts)
        subtitle_ko = " · ".join(subtitle_ko_parts) if subtitle_ko_parts else None

        author_part = f": {ko_author}" if ko_author else ""
        title = _shrink_subtitle_to_fit(prefix, ko_title, author_part, subtitle_ko)
        return title

    # language == "en"
    if not is_english_title(book_title_main):
        en_title = translate_book_title(book_title_main)
        if not is_english_title(en_title):
            raise ValueError(
                f"책 제목 '{book_title}'의 영어 번역을 찾을 수 없습니다. "
                f"src/utils/translations.py에 매핑을 추가하거나, 영문 원제를 함께 입력하세요."
            )
        ko_title = book_title_main
    else:
        en_title = book_title_main
        ko_title = translate_book_title_to_korean(book_title_main)

    en_author = ""
    if resolved_author:
        if not is_english_title(resolved_author):
            en_author = translate_author_name(resolved_author) or resolved_author
        else:
            en_author = resolved_author
        # 영문 제목은 "완전 영어"만 허용
        if contains_korean(en_author):
            raise ValueError(
                "영문 작가명에 한글이 포함되어 있습니다. "
                "저자 영문 표기를 함께 입력하거나, src/utils/translations.py에 매핑을 추가하세요."
            )

    # 부제목(en): 영문 부제(있다면) + SEO 키워드 (완전 영어만)
    subtitle_en_parts: List[str] = []
    if subtitle_from_input and is_english_title(subtitle_from_input):
        subtitle_en_parts.append(subtitle_from_input)
    if generate_seo_subtitle:
        subtitle_en_parts.append(
            generate_seo_subtitle(
                "en",
                en_title,
                author=en_author or None,
                book_info=book_info,
                content_type="full_episode",
            )
        )
    subtitle_en_parts = _unique_keep_order(subtitle_en_parts)
    subtitle_en = " · ".join(subtitle_en_parts) if subtitle_en_parts else None

    author_part = f": {en_author}" if en_author else ""
    title = _shrink_subtitle_to_fit(prefix, en_title, author_part, subtitle_en)
    if contains_korean(title):
        raise ValueError(
            "영문 제목에 한글이 포함되어 있습니다. "
            "영문 원제/저자 영문 표기를 함께 입력하거나, src/utils/translations.py에 번역 매핑을 추가하세요."
        )
    return title


def detect_part_count(book_title: str, language: str = "ko") -> int:
    """
    Part 개수를 동적으로 감지

    Args:
        book_title: 책 제목
        language: 언어 ('ko', 'kr' 또는 'en')

    Returns:
        Part 개수
    """
    safe_title = get_standard_safe_title(book_title)
    # 언어 정규화
    normalized_language = "ko" if language in ["ko", "kr"] else "en"
    lang_suffix = "_kr" if language in ["ko", "kr"] else "_en"
    dir_lang = "kr" if language in ["ko", "kr"] else "en"
    input_dir = Path("assets/notebooklm") / safe_title / dir_lang
    
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


def get_actual_part_durations(book_title: str, language: str = "ko", infographic_duration: float = 30.0) -> List[float]:
    """
    실제 Part 비디오 파일의 길이를 계산하여 각 Part의 총 길이 반환
    (비디오 길이 + 인포그래픽 길이)

    우선순위:
    1. 렌더링된 영상의 timing.json 파일에서 읽기 (가장 정확)
    2. 원본 비디오 파일의 duration 사용 (fallback)

    Args:
        book_title: 책 제목
        language: 언어 ('ko', 'kr' 또는 'en')
        infographic_duration: 인포그래픽 표시 시간 (초, 기본값: 30.0)

    Returns:
        각 Part의 총 길이 리스트 (초 단위)
    """
    safe_title = get_standard_safe_title(book_title)

    # 언어 정규화 (파일명용) - create_full_episode.py와 일치: ko 사용 (kr 아님)
    lang_suffix_file = "ko" if language in ["ko", "kr"] else "en"

    # 1. 먼저 렌더링된 영상의 timing.json 파일 확인 (가장 정확)
    video_path = Path(f"output/{safe_title}_full_episode_{lang_suffix_file}.mp4")
    timing_info_path = video_path.with_suffix('.timing.json')
    
    if timing_info_path.exists():
        try:
            with open(timing_info_path, 'r', encoding='utf-8') as f:
                timing_info = json.load(f)
            
            part_clip_info = timing_info.get('part_clip_info', [])
            if part_clip_info:
                # Part별로 그룹화하여 각 Part의 총 길이 계산
                part_durations = {}
                for clip_info in part_clip_info:
                    part_num = clip_info['part_num']
                    if part_num not in part_durations:
                        part_durations[part_num] = 0.0
                    part_durations[part_num] += clip_info['duration']
                
                # Part 번호 순서대로 리스트 반환
                sorted_parts = sorted(part_durations.keys())
                return [part_durations[p] for p in sorted_parts]
        except Exception as e:
            logger.warning(f"⚠️ timing.json 파일 읽기 실패: {e}")
            logger.warning("원본 비디오 파일의 duration을 사용합니다.")
    
    # 2. Fallback: 원본 비디오 파일의 duration 사용
    part_durations = []

    # input 폴더에서 먼저 확인
    input_dir = Path("input")
    lang_suffix = "kr" if language in ["ko", "kr"] else "en"

    # assets/notebooklm 폴더 경로 미리 계산
    lang_suffix_alt = "_kr" if language in ["ko", "kr"] else "_en"
    dir_lang = "kr" if language in ["ko", "kr"] else "en"
    notebooklm_dir = Path("assets/notebooklm") / safe_title / dir_lang
    
    part_num = 1
    while True:
        video_file = input_dir / f"part{part_num}_video_{lang_suffix}.mp4"
        if not video_file.exists():
            # assets/notebooklm 폴더에서 확인
            video_file = notebooklm_dir / f"part{part_num}_video{lang_suffix_alt}.mp4"
            
            if not video_file.exists():
                break
        
        try:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(str(video_file))
            video_duration = clip.duration
            clip.close()
            
            # 인포그래픽 파일 확인
            info_file = input_dir / f"part{part_num}_info_{lang_suffix}.png"
            if not info_file.exists():
                # assets/notebooklm 폴더에서 확인
                info_file = notebooklm_dir / f"part{part_num}_info{lang_suffix_alt}.png"
            
            # 인포그래픽이 있으면 길이 추가
            total_duration = video_duration
            if info_file.exists():
                total_duration += infographic_duration
            
            part_durations.append(total_duration)
            part_num += 1
            
        except Exception as e:
            logger.warning(f"⚠️ Part {part_num} 비디오 길이를 가져올 수 없습니다: {e}")
            break
    
    return part_durations


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
        
        # 타임스탬프 생성 (실제 Part 길이 사용)
        timestamps = ""
        if video_duration:
            # 실제 Part 비디오 파일의 길이 가져오기
            actual_part_durations = get_actual_part_durations(book_title, language, infographic_duration=30.0)
            
            current_time = 0.0
            ts_lines = []
            
            # 실제 Part 길이가 있으면 사용, 없으면 비율로 계산
            if actual_part_durations and len(actual_part_durations) == part_count:
                # 실제 Part 길이 사용
                for i in range(1, part_count + 1):
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
                    
                    # 다음 Part 시작 시간 계산
                    if i < len(actual_part_durations):
                        current_time += actual_part_durations[i - 1]
            else:
                # 실제 Part 길이를 가져올 수 없으면 비율로 계산 (하위 호환성)
                logger.warning("⚠️ 실제 Part 비디오 파일을 찾을 수 없어 비율로 타임스탬프를 계산합니다.")
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
{ko_title}
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
"""

        # 제휴 링크 삽입 (한글)
        # 영문 책 제목 준비
        if is_english_title(book_title):
            en_title_for_link = book_title
            ko_title_for_link = translate_book_title_to_korean(book_title)
        else:
            en_title_for_link = translate_book_title(book_title)
            ko_title_for_link = book_title

        # author 정보 준비
        ko_author = ""
        en_author = ""
        if book_info and 'author' in book_info:
            author_val = book_info['author']
            if is_english_title(author_val):
                en_author = author_val
                # 영문 작가명은 한글로 번역 (translate_author_name은 한글→영문이므로 그대로 사용 불가)
                ko_author = ""  # 현재는 빈 문자열로 처리
            else:
                ko_author = author_val
                en_author = translate_author_name(author_val)

        isbn_ko = book_info.get('isbn_13_ko') or book_info.get('isbn_10_ko') or '' if book_info else ''
        isbn_en = book_info.get('isbn_13_en') or book_info.get('isbn_10_en') or '' if book_info else ''
        affiliate_section = generate_affiliate_section(
            book_title_ko=ko_title_for_link,
            book_title_en=en_title_for_link,
            author_ko=ko_author,
            author_en=en_author,
            language='ko',
            isbn_ko=isbn_ko,
            isbn_en=isbn_en
        )
        description += affiliate_section

        # 장르별 해시태그 생성
        try:
            from src.utils.title_generator import generate_hashtags
            ko_hashtags = generate_hashtags("ko", book_title, book_info=book_info, content_type="full_episode")
        except Exception:
            ko_hashtags = f"#일당백 #{ko_title.replace(' ', '')} #책리뷰 #문학 #{genre_ko}"
        description += f"\n{ko_hashtags}\n"

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

        # Timestamps (실제 Part 길이 사용)
        timestamps = ""
        if video_duration:
            # 실제 Part 비디오 파일의 길이 가져오기
            actual_part_durations = get_actual_part_durations(book_title, language, infographic_duration=30.0)
            
            current_time = 0.0
            ts_lines = []
            
            # 실제 Part 길이가 있으면 사용, 없으면 비율로 계산
            if actual_part_durations and len(actual_part_durations) == part_count:
                # 실제 Part 길이 사용
                for i in range(1, part_count + 1):
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
                    
                    # 다음 Part 시작 시간 계산
                    if i < len(actual_part_durations):
                        current_time += actual_part_durations[i - 1]
            else:
                # 실제 Part 길이를 가져올 수 없으면 비율로 계산 (하위 호환성)
                logger.warning("⚠️ 실제 Part 비디오 파일을 찾을 수 없어 비율로 타임스탬프를 계산합니다.")
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
"""

        # 제휴 링크 삽입 (영문)
        # 영문 책 제목 준비
        if is_english_title(book_title):
            en_title_for_link = book_title
            ko_title_for_link = translate_book_title_to_korean(book_title)
        else:
            en_title_for_link = translate_book_title(book_title)
            ko_title_for_link = book_title

        # author 정보 준비
        ko_author = ""
        en_author = ""
        if book_info and 'author' in book_info:
            author_val = book_info['author']
            if is_english_title(author_val):
                en_author = author_val
                ko_author = ""  # 영문→한글 번역 함수가 없으므로 빈 문자열
            else:
                ko_author = author_val
                en_author = translate_author_name(author_val)

        isbn_ko = book_info.get('isbn_13_ko') or book_info.get('isbn_10_ko') or '' if book_info else ''
        isbn_en = book_info.get('isbn_13_en') or book_info.get('isbn_10_en') or '' if book_info else ''
        affiliate_section = generate_affiliate_section(
            book_title_ko=ko_title_for_link,
            book_title_en=en_title_for_link,
            author_ko=ko_author,
            author_en=en_author,
            language='en',
            isbn_ko=isbn_ko,
            isbn_en=isbn_en
        )
        description += affiliate_section

        # 장르별 영문 해시태그 생성
        try:
            from src.utils.title_generator import generate_hashtags as _gen_ep_hashtags_en
            en_hashtags = _gen_ep_hashtags_en("en", book_title, book_info=book_info, content_type="full_episode")
        except Exception:
            en_hashtags = f"#{safe_en_title} #BookReview #Literature #{safe_genre_en}"
        description += f"\n{en_hashtags}\n"

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
    video_duration: Optional[float] = None,
    author: Optional[str] = None
) -> Dict:
    """
    에피소드 영상 메타데이터 생성

    Args:
        book_title: 책 제목
        language: 언어 ('ko', 'kr' 또는 'en')
        video_path: 영상 파일 경로 (선택사항)
        thumbnail_path: 썸네일 파일 경로 (선택사항)
        video_duration: 영상 길이 (초, 선택사항)

    Returns:
        메타데이터 딕셔너리
    """
    safe_title = get_standard_safe_title(book_title)

    # 언어 정규화 (파일명용) - create_full_episode.py와 일치: ko 사용
    normalized_language = "ko" if language in ["ko", "kr"] else "en"
    lang_suffix_file = "ko" if language in ["ko", "kr"] else "en"

    # 영상 경로가 없으면 자동으로 찾기 (ko/kr 둘 다 시도)
    if not video_path:
        video_path = f"output/{safe_title}_full_episode_{lang_suffix_file}.mp4"
        if not Path(video_path).exists() and lang_suffix_file == "ko":
            alt_path = f"output/{safe_title}_full_episode_kr.mp4"
            if Path(alt_path).exists():
                video_path = alt_path
    
    video_path_obj = Path(video_path)
    
    # 영상이 존재하는지 확인
    if not video_path_obj.exists():
        logger.warning(f"⚠️ 영상 파일을 찾을 수 없습니다: {video_path}")
        logger.warning("메타데이터는 생성되지만 영상 파일이 없습니다.")
    
    # 썸네일 경로가 없으면 자동으로 찾기
    if not thumbnail_path:
        thumbnail_path = f"output/{safe_title}_thumbnail_{lang_suffix_file}.jpg"
    
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
    
    # 메타데이터 생성 (현재 언어) - normalized_language 사용
    title = generate_episode_title(book_title, normalized_language, book_info, author=author)
    description = generate_episode_description(book_title, normalized_language, video_duration, book_info)
    tags = generate_episode_tags(book_title, normalized_language, book_info)

    # 영문 메타데이터인 경우 최종 검증: description과 tags에서 한국어 제거
    if normalized_language == "en":
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
    
    # 양쪽 언어의 제목과 설명 생성 (다국어 메타데이터용)
    other_language = "en" if normalized_language == "ko" else "ko"
    title_other = generate_episode_title(book_title, other_language, book_info, author=author)
    description_other = generate_episode_description(book_title, other_language, video_duration, book_info)
    
    # 영문 설명에서 한국어 제거 (다국어 메타데이터용)
    if other_language == "en":
        if contains_korean(description_other):
            lines = description_other.split('\n')
            cleaned_lines = []
            for line in lines:
                if contains_korean(line):
                    cleaned_line = remove_korean_from_text(line)
                    if cleaned_line.strip():
                        cleaned_lines.append(cleaned_line)
                else:
                    cleaned_lines.append(line)
            description_other = '\n'.join(cleaned_lines)
    
    # 다음 날 19:00 KST (= 10:00 UTC) 예약 업로드
    from datetime import timezone, timedelta
    kst = timezone(timedelta(hours=9))
    now_kst = datetime.now(kst)
    publish_kst = (now_kst + timedelta(days=1)).replace(hour=19, minute=0, second=0, microsecond=0)
    publish_utc = publish_kst.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    metadata = {
        'video_path': str(video_path_obj),
        'title': title,
        'description': description,
        'tags': tags,
        'language': normalized_language,
        'book_title': book_title,
        'video_duration': video_duration,
        'publish_at': publish_utc,
        # 다국어 메타데이터 (YouTube localizations용)
        # 해당 영상의 언어만 포함 (다른 언어 포함 시 뷰어 언어 설정에 따라 제목이 바뀜)
        'localizations': {
            normalized_language: {
                'title': title,
                'description': description
            }
        }
    }
    
    if thumbnail_path:
        metadata['thumbnail_path'] = str(thumbnail_path_obj)
    
    # Part 1 video와 infographic의 종료 시간 추가 (timing.json에서 읽기)
    timing_info_path = video_path_obj.with_suffix('.timing.json')
    if timing_info_path.exists():
        try:
            with open(timing_info_path, 'r', encoding='utf-8') as f:
                timing_info = json.load(f)
            
            if timing_info.get('part1_video_end_time') is not None:
                metadata['part1_video_end_time'] = timing_info['part1_video_end_time']
            if timing_info.get('part1_info_end_time') is not None:
                metadata['part1_info_end_time'] = timing_info['part1_info_end_time']
            
            logger.info(f"📊 Part 1 시간 정보 추가:")
            if metadata.get('part1_video_end_time'):
                minutes = int(metadata['part1_video_end_time'] // 60)
                seconds = int(metadata['part1_video_end_time'] % 60)
                logger.info(f"   Part 1 Video 종료: {minutes}:{seconds:02d} ({metadata['part1_video_end_time']:.2f}초)")
            if metadata.get('part1_info_end_time'):
                minutes = int(metadata['part1_info_end_time'] // 60)
                seconds = int(metadata['part1_info_end_time'] % 60)
                logger.info(f"   Part 1 Infographic 종료: {minutes}:{seconds:02d} ({metadata['part1_info_end_time']:.2f}초)")
        except Exception as e:
            logger.warning(f"⚠️ timing.json 파일 읽기 실패: {e}")
    
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
        '--author',
        type=str,
        default=None,
        help='작가명 (선택, book_info.json에 없을 때 제목에 사용)'
    )
    
    parser.add_argument(
        '--language',
        type=str,
        default='ko',
        choices=['ko', 'kr', 'en'],
        help='언어 (기본값: ko, kr도 ko로 처리됨)'
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
            thumbnail_path=args.thumbnail_path,
            author=args.author
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

