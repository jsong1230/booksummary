"""
영상 생성 및 메타데이터 미리보기 스크립트
- 한글/영문 오디오로 각각 영상 생성
- 메타데이터(제목, 설명, 태그) 생성 및 미리보기
- 썸네일 자동 생성 (선택사항)
- 업로드 전 점검 가능
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Tuple, List

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

# 썸네일 생성 모듈 import
try:
    import importlib.util
    thumbnail_spec = importlib.util.spec_from_file_location("generate_thumbnail", Path(__file__).parent / "10_generate_thumbnail.py")
    thumbnail_module = importlib.util.module_from_spec(thumbnail_spec)
    thumbnail_spec.loader.exec_module(thumbnail_module)
    ThumbnailGenerator = thumbnail_module.ThumbnailGenerator
    THUMBNAIL_AVAILABLE = True
except Exception as e:
    THUMBNAIL_AVAILABLE = False
    print(f"⚠️ 썸네일 생성 모듈 로드 실패: {e}")

# 필요한 모듈 import
import importlib.util
spec = importlib.util.spec_from_file_location("make_video", Path(__file__).parent / "03_make_video.py")
make_video_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(make_video_module)
VideoMaker = make_video_module.VideoMaker

# 공통 유틸리티 import
from src.utils.translations import translate_book_title, translate_author_name, get_book_alternative_title, translate_book_title_to_korean, is_english_title, translate_author_name_to_korean
from src.utils.file_utils import safe_title, load_book_info, get_standard_safe_title

def generate_title(book_title: str, lang: str = "both", author: Optional[str] = None) -> str:
    """
    영상 제목 생성 (SEO 최적화 포함)
    - 검색 키워드 포함 (책 제목, 저자명, "책 리뷰")
    - 두 언어 포함, 언어 표시 포함, 대체 제목 포함
    - 검색량 높은 키워드를 앞쪽에 배치하여 검색 최적화
    """
    # 괄호 안의 한글 추출 (예: "Sátántangó (사탄탱고)" -> ko_title="사탄탱고", en_title="Sátántangó")
    import re
    # 괄호 안의 한글 추출
    bracket_match = re.search(r'\(([^)]+)\)', book_title)
    ko_title_from_bracket = None
    if bracket_match:
        bracket_content = bracket_match.group(1)
        # 괄호 안 내용이 한글인지 확인
        if not is_english_title(bracket_content):
            ko_title_from_bracket = bracket_content
    
    # 괄호 제거한 제목
    book_title_clean = re.sub(r'\s*\([^)]*\)\s*$', '', book_title).strip()
    
    # book_title이 영어인지 한글인지 판단
    if is_english_title(book_title_clean):
        # 영어 제목이 들어온 경우: 한글 제목으로 변환
        ko_title = translate_book_title_to_korean(book_title_clean)
        en_title = book_title_clean  # 이미 영어
        
        # 괄호에서 추출한 한글 제목이 있으면 우선 사용
        if ko_title_from_bracket:
            ko_title = ko_title_from_bracket
        
        # ko_title이 여전히 영어인 경우 (번역 실패), 한글 발음으로 변환 시도
        if is_english_title(ko_title):
            # 간단한 발음 변환 매핑 (추가 필요시 확장)
            pronunciation_map = {
                "Buckeye": "벅아이",
                "Animal Farm": "애니멀 팜",
                "Hamlet": "햄릿",
                "Sunrise on the Reaping": "선라이즈 온 더 리핑",
                "The Anxious Generation": "불안 세대",
                "Sátántangó": "사탄탱고",
            }
            ko_title = pronunciation_map.get(ko_title, ko_title)
    else:
        # 한글 제목이 들어온 경우: 영어 제목으로 변환
        ko_title = book_title  # 이미 한글
        en_title = translate_book_title(book_title)
        
        # en_title이 여전히 한글인 경우 (번역 실패), 에러 발생
        if not is_english_title(en_title):
            # 매핑에 없는 경우, pronunciation_map에서 찾기
            pronunciation_map = {
                "벅아이": "Buckeye",
                "애니멀 팜": "Animal Farm",
                "햄릿": "Hamlet",
                "선라이즈 온 더 리핑": "Sunrise on the Reaping",
                "불안 세대": "The Anxious Generation",
            }
            en_title = pronunciation_map.get(ko_title, en_title)
            
            # 여전히 한글이면 에러
            if not is_english_title(en_title):
                raise ValueError(f"책 제목 '{book_title}'의 영어 번역을 찾을 수 없습니다. src/utils/translations.py에 매핑을 추가하세요.")
    
    alt_titles = get_book_alternative_title(ko_title)  # 한글 제목 기준으로 대체 제목 찾기
    
    # 작가 이름 추가 (검색 최적화)
    author_str = ""
    if author:
        if is_english_title(author):
            ko_author = translate_author_name_to_korean(author)
            en_author = author
        else:
            ko_author = author
            en_author = translate_author_name(author)
    else:
        ko_author = ""
        en_author = ""
    
    if lang == "ko":
        # 한글 먼저, 영어 나중
        # SEO 최적화: 검색량 높은 키워드 앞쪽 배치
        # 형식: "[한국어] {책제목} 책 리뷰 {작가명} | [Korean] {영어제목} Book Review"
        if alt_titles.get("ko"):
            # 대체 제목 포함: "노르웨이의 숲 (상실의 시대)"
            main_title = f"{ko_title} ({alt_titles['ko']})"
        else:
            main_title = ko_title
        
        # 작가명 추가 (검색량 최적화)
        author_part = f" {ko_author}" if ko_author else ""
        title = f"[핵심 요약] {main_title} 핵심 정리{author_part} | [Summary] {en_title} Book Review"
    elif lang == "en":
        # 영어 먼저, 한글 나중
        # SEO 최적화: 검색량 높은 키워드 앞쪽 배치
        # 형식: "[Summary] {영어제목} Book Review {작가명} | [핵심 요약] {한글제목}"
        if alt_titles.get("en"):
            # 대체 제목 포함: "Norwegian Wood (The Age of Loss)"
            en_main_title = f"{en_title} ({alt_titles['en']})"
        else:
            en_main_title = en_title
        
        # 한글 부분: ko_title 사용 (이미 한글로 변환됨)
        if alt_titles.get("ko"):
            # 한글 부분에도 대체 제목 포함
            ko_main_title = f"{ko_title} ({alt_titles['ko']})"
        else:
            ko_main_title = ko_title
        
        # 작가명 추가 (검색 최적화)
        author_part = f" {en_author}" if en_author else ""
        title = f"[Summary] {en_main_title} Book Review{author_part} | [핵심 요약] {ko_main_title} 핵심 정리"
    else:
        # 두 언어 혼합 (기본값)
        title = f"[핵심 요약] {ko_title} | [Summary] {en_title} Book Review"

    # YouTube 제목 최대 길이: 100자
    if len(title) > 100:
        title = title[:97] + "..."
    return title

def generate_description(book_info: Optional[Dict] = None, lang: str = "both", book_title: str = None, timestamps: Optional[Dict] = None, author: Optional[str] = None) -> str:
    """
    영상 설명 생성 (두 언어 포함)
    
    Args:
        book_info: 책 정보 딕셔너리
        lang: 언어 ('ko', 'en', 'both')
        book_title: 책 제목
        timestamps: timestamp 정보 딕셔너리
            - summary_duration: Summary 부분 길이 (초)
            - notebooklm_duration: NotebookLM Video 부분 길이 (초)
            - review_duration: Review Audio 부분 길이 (초)
    """
    if lang == "ko":
        # 한글 먼저, 영어 나중
        return _generate_description_ko(book_info, book_title, timestamps, author)
    elif lang == "en":
        # 영어 설명만 반환
        return _generate_description_en(book_info, book_title, include_header=True, timestamps=timestamps, author=author)
    else:
        ko_desc = _generate_description_ko(book_info, book_title, timestamps, author)
        en_desc = _generate_description_en_with_ko(book_info, book_title, timestamps, author)
        return f"{ko_desc}\n\n{'='*60}\n\n{en_desc}"

def _format_timestamp(seconds: float) -> str:
    """초를 YouTube timestamp 형식으로 변환 (예: 1:36, 8:07)"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"

def _generate_timestamps_section(timestamps: Optional[Dict] = None, lang: str = "ko") -> str:
    """Timestamp 섹션 생성"""
    if not timestamps:
        return ""
    
    summary_duration = timestamps.get('summary_duration', 0)
    notebooklm_duration = timestamps.get('notebooklm_duration', 0)
    
    # Summary가 없으면 timestamp 추가 안 함
    if summary_duration == 0:
        return ""
    
    silence_duration = 2.0  # 섹션 사이 silence
    
    # 첫 번째 timestamp: Summary 끝나고 NotebookLM Video 시작
    timestamp1 = summary_duration
    
    if lang == "ko":
        section = "\n⏱️ 영상 구간:\n"
        section += f"0:00 - 요약 (Summary)\n"
        if notebooklm_duration > 0:
            section += f"{_format_timestamp(timestamp1)} - NotebookLM 상세 분석\n"
    else:  # en
        section = "\n⏱️ Video Chapters:\n"
        section += f"0:00 - Summary\n"
        if notebooklm_duration > 0:
            section += f"{_format_timestamp(timestamp1)} - NotebookLM Detailed Analysis\n"
    
    return section

def _generate_youtube_chapters(timestamps: Optional[Dict] = None, lang: str = "ko") -> str:
    """
    YouTube 챕터 마커 생성 (description 앞부분에 추가)
    
    YouTube는 description의 처음 부분에 특정 형식의 timestamp가 있으면 자동으로 챕터를 생성합니다.
    형식: 0:00 Chapter Title (하이픈 없이도 가능)
    """
    if not timestamps:
        return ""
    
    summary_duration = timestamps.get('summary_duration', 0)
    notebooklm_duration = timestamps.get('notebooklm_duration', 0)
    
    # Summary가 없으면 챕터 추가 안 함
    if summary_duration == 0:
        return ""
    
    silence_duration = 2.0  # 섹션 사이 silence
    
    # 챕터 목록 생성
    chapters = []
    
    # 첫 번째 챕터: Summary (0:00)
    if lang == "ko":
        chapters.append("0:00 요약 (Summary)")
    else:
        chapters.append("0:00 Summary")
    
    # 두 번째 챕터: NotebookLM Video (있는 경우)
    if notebooklm_duration > 0:
        timestamp1 = _format_timestamp(summary_duration)
        if lang == "ko":
            chapters.append(f"{timestamp1} NotebookLM 상세 분석")
        else:
            chapters.append(f"{timestamp1} NotebookLM Detailed Analysis")
    
    # YouTube 챕터 형식으로 반환 (각 챕터는 새 줄에)
    return "\n".join(chapters) + "\n\n"

def _generate_description_ko(book_info: Optional[Dict] = None, book_title: str = None, timestamps: Optional[Dict] = None, author: Optional[str] = None) -> str:
    """한글 설명 생성 (한글 먼저, 영어 나중)"""
    # YouTube 챕터 마커를 description의 맨 앞에 추가
    youtube_chapters = ""
    if timestamps:
        youtube_chapters = _generate_youtube_chapters(timestamps, lang="ko")
    
    # 책 제목 준비
    if is_english_title(book_title):
        ko_title = translate_book_title_to_korean(book_title)
    else:
        ko_title = book_title
    
    # 한글 부분 (검색 최적화: 키워드 자연스럽게 포함)
    ko_desc = youtube_chapters + f"""📚 바쁜 현대인을 위한 핵심 요약 | {ko_title}

이 영상은 NotebookLM과 AI를 활용하여 생성된 '핵심 요약' 영상입니다.
바쁜 일상 속에서 잠시 시간을 내어 책의 핵심을 파악해보세요.

📝 영상 구성:
• 핵심 요약 (GPT 생성) - 책의 주요 메시지와 인사이트
• 상세 심층 분석 (NotebookLM) - 작가의 의도와 깊이 있는 해석

이 영상은 책의 내용을 빠르게 파악하고 싶거나, 읽은 내용을 정리하고 싶은 분들을 위해 제작되었습니다.
"""
    
    # Timestamp 섹션 추가 (중간에 표시용)
    if timestamps:
        ko_desc += _generate_timestamps_section(timestamps, lang="ko")
        ko_desc += "\n"
    
    # 좋아요 유도 문구 중간 삽입 (시청자 유지율 향상)
    ko_desc += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👍 이 영상이 도움이 되셨다면 좋아요를 눌러주세요!
좋아요는 YouTube 알고리즘이 이 영상을 더 많은 사람에게 추천하는 데 큰 도움이 됩니다.
여러분의 좋아요가 채널 성장의 원동력입니다! 💪
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
    
    if book_info:
        # 책 소개 추가 (book_info의 description이 한글인 경우만 사용)
        if book_info.get('description'):
            # description이 있으면 한글인지 확인
            desc = book_info['description'].strip()
            if desc and not is_english_title(desc[:100]):  # 처음 100자로 한글인지 판단
                # 한글 description인 경우만 사용
                ko_desc += f"📖 책 소개:\n{desc[:500]}{'...' if len(desc) > 500 else ''}\n\n"
        if "📖 책 소개:" not in ko_desc:
            # 한글 description이 없거나 영어 description만 있는 경우
            if book_title:
                # description이 없으면 검색 최적화된 기본 메시지
                ko_desc += f"📖 책 소개:\n{book_title}에 대한 상세한 책 리뷰 영상입니다. 이 영상에서는 {book_title}의 주요 내용, 작가의 배경, 작품의 의미 등을 분석합니다. 독서 전 예습이나 독서 후 복습에 활용하실 수 있습니다.\n\n"
        if book_info.get('authors'):
            # 한글과 영어 작가 이름 모두 표시
            authors_ko = []
            authors_en = []
            for author in book_info['authors']:
                if is_english_title(author):
                    # 영어 작가 이름인 경우
                    authors_en.append(author)
                    ko_author = translate_author_name_to_korean(author)
                    authors_ko.append(ko_author if ko_author != author else author)
                else:
                    # 한글 작가 이름인 경우
                    authors_ko.append(author)
                    en_author = translate_author_name(author)
                    authors_en.append(en_author if en_author != author else author)
            
            ko_author_str = ', '.join(authors_ko) if authors_ko else ', '.join(book_info['authors'])
            ko_desc += f"✍️ 작가: {ko_author_str}\n"
        elif author:
            # book_info에 authors가 없지만 author 파라미터가 있는 경우
            if is_english_title(author):
                # 영어 작가 이름인 경우 한글로 변환
                ko_author = translate_author_name_to_korean(author)
            else:
                # 한글 작가 이름인 경우 그대로 사용
                ko_author = author
            ko_desc += f"✍️ 작가: {ko_author}\n"
    elif author:
        # book_info가 없지만 author 파라미터가 있는 경우
        if is_english_title(author):
            # 영어 작가 이름인 경우 한글로 변환
            ko_author = translate_author_name_to_korean(author)
        else:
            # 한글 작가 이름인 경우 그대로 사용
            ko_author = author
        ko_desc += f"✍️ 작가: {ko_author}\n"
    if book_info and book_info.get('publishedDate'):
        ko_desc += f"📅 출간일: {book_info['publishedDate']}\n"
    
    ko_desc += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔔 구독과 좋아요는 영상 제작에 큰 힘이 됩니다!

💬 댓글을 남겨주세요!
이 책을 읽어보셨나요? 어떤 생각이 드셨나요?
댓글로 여러분의 생각과 감상을 공유해주시면 큰 힘이 됩니다.
질문이나 궁금한 점도 언제든지 댓글로 남겨주세요! 💕

📌 이 책에 대한 여러분의 의견이 궁금합니다:
• 이 책을 읽어보신 분들의 솔직한 후기
• 이 책과 비슷한 책 추천
• 이 책의 어떤 부분이 가장 인상 깊으셨나요?
• 작가의 다른 작품 중 추천하고 싶은 책

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#핵심요약 #책리뷰 #독서 #북튜버 #책추천 #지식창고 #BookSummary #Reading
"""
    
    # 영어 부분 (검색 최적화: 키워드 자연스럽게 포함)
    en_desc = """📚 5-Minute Book Summary | Reading | BookTube

This video is a 'Core Summary' generated using NotebookLM and AI.
Grasp the essence of the book in just 5 minutes amidst your busy life.

📝 Video Content:
• 5-Minute Core Summary (GPT Generated) - Key messages and insights
• Detailed Deep Analysis (NotebookLM) - Author's intent and in-depth interpretation

This video is created for those who want to quickly grasp the book's content or organize what they've read.
"""
    if book_info:
        # 영어 책 소개 추가 (book_info의 description이 영어인 경우만 사용)
        if book_info.get('description'):
            # description이 있으면 영어인지 확인
            desc = book_info['description'].strip()
            if desc and is_english_title(desc[:100]):  # 처음 100자로 영어인지 판단
                # 영어 description인 경우만 사용
                en_desc += f"📖 Book Introduction:\n{desc[:500]}{'...' if len(desc) > 500 else ''}\n\n"
        if "📖 Book Introduction:" not in en_desc:
            # 영어 description이 없거나 한글 description만 있는 경우
            if book_title:
                # description이 없으면 하드코딩된 영어 설명 시도
                en_book_desc = get_english_book_description(book_title)
                if en_book_desc:
                    en_desc += f"📖 Book Introduction:\n{en_book_desc[:500]}...\n\n"
        
        if book_info.get('authors'):
            # 영어와 한글 작가 이름 모두 표시
            authors_ko = []
            authors_en = []
            for author_name in book_info['authors']:
                if is_english_title(author_name):
                    # 영어 작가 이름인 경우
                    authors_en.append(author_name)
                    ko_author = translate_author_name_to_korean(author_name)
                    authors_ko.append(ko_author if ko_author != author_name else author_name)
                else:
                    # 한글 작가 이름인 경우
                    authors_ko.append(author_name)
                    en_author = translate_author_name(author_name)
                    authors_en.append(en_author if en_author != author_name else author_name)
            
            en_author_str = ', '.join(authors_en) if authors_en else ', '.join(book_info['authors'])
            en_desc += f"✍️ Author: {en_author_str}\n"
        elif author:
            # book_info에 authors가 없지만 author 파라미터가 있는 경우
            if is_english_title(author):
                en_author = author
            else:
                en_author = translate_author_name(author)
            en_desc += f"✍️ Author: {en_author}\n"
        if book_info.get('publishedDate'):
            en_desc += f"📅 Published: {book_info['publishedDate']}\n"
    
    en_desc += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔔 Subscribe and like to support video creation!

💬 Please leave a comment!
Have you read this book? What are your thoughts?
Your comments and reviews mean a lot to us!
Feel free to share any questions or thoughts in the comments below! 💕

📌 We'd love to hear your thoughts on this book:
• Honest reviews from those who have read it
• Book recommendations similar to this one
• Which part of the book impressed you the most?
• Other works by this author you'd recommend

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#BookSummary #Reading #BookTube #5minReading #Knowledge #책요약 #독서
"""
    
    # 한글 먼저, 영어 나중
    return f"{ko_desc}\n\n{'='*60}\n\n{en_desc}"

# translate_author_name은 utils.translations에서 import

def get_english_book_description(book_title: str) -> str:
    """책 제목에 따른 영어 설명 반환"""
    descriptions = {
        "노르웨이의 숲": """Norwegian Wood is a brilliant diamond in Haruki Murakami's world - the book you must read first to meet Murakami Haruki! This novel, which resonates with the sensitive and delicate emotions of youth, has been loved as an eternal must-read. Set in late 1960s Japan during the period of rapid economic growth, this novel depicts the fragile relationship between individuals and society, and the vivid moments of youth that seem within reach. Translated and introduced in more than 36 countries, it caused a worldwide 'Murakami boom' and widely publicized Murakami Haruki's literary achievements, making it a representative work of modern Japanese literature.""",
        "노르웨이의_숲": """Norwegian Wood is a brilliant diamond in Haruki Murakami's world - the book you must read first to meet Murakami Haruki! This novel, which resonates with the sensitive and delicate emotions of youth, has been loved as an eternal must-read. Set in late 1960s Japan during the period of rapid economic growth, this novel depicts the fragile relationship between individuals and society, and the vivid moments of youth that seem within reach. Translated and introduced in more than 36 countries, it caused a worldwide 'Murakami boom' and widely publicized Murakami Haruki's literary achievements, making it a representative work of modern Japanese literature.""",
        "데미안": """Demian is a coming-of-age novel by Hermann Hesse that explores the tension between the world of illusion and the world of spiritual truth. It follows the story of Emil Sinclair, a young boy raised in a bourgeois home, who struggles to find his true self amidst the conflicting influences of his family and the mysterious Max Demian.""",
        "사피엔스": """Sapiens: A Brief History of Humankind by Yuval Noah Harari explores how Homo sapiens came to dominate the world. The book covers the Cognitive Revolution, the Agricultural Revolution, and the Scientific Revolution, offering a thought-provoking perspective on human history and our future.""",
    }
    
    return descriptions.get(book_title, "")

def _generate_description_en(book_info: Optional[Dict] = None, book_title: str = None, include_header: bool = True, timestamps: Optional[Dict] = None, author: Optional[str] = None) -> str:
    """영문 설명 생성"""
    # YouTube 챕터 마커를 description의 맨 앞에 추가
    youtube_chapters = ""
    if timestamps:
        youtube_chapters = _generate_youtube_chapters(timestamps, lang="en")
    
    description = ""
    
    if include_header:
        description = youtube_chapters + """📚 Core Book Summary for Busy People | Reading | BookTube

This video is a 'Core Summary' generated using NotebookLM and AI.
Grasp the essence of the book in a short time amidst your busy life.

📝 Video Content:
• Core Summary (GPT Generated) - Key messages and insights
• Detailed Deep Analysis (NotebookLM) - Author's intent and in-depth interpretation

This video is created for those who want to quickly grasp the book's content or organize what they've read.
"""
        
        # Timestamp 섹션 추가 (중간에 표시용)
        if timestamps:
            description += _generate_timestamps_section(timestamps, lang="en")
            description += "\n"
        
        # 좋아요 유도 문구 중간 삽입 (시청자 유지율 향상)
        description += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👍 If this video was helpful, please give it a like!
Likes help YouTube's algorithm recommend this video to more people.
Your likes are the driving force behind channel growth! 💪
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
    
    if book_info:
        # 영어 설명 사용 (book_info의 description이 영어인 경우만 사용)
        if book_info.get('description'):
            # description이 있으면 영어인지 확인
            desc = book_info['description'].strip()
            if desc and is_english_title(desc[:100]):  # 처음 100자로 영어인지 판단
                # 영어 description인 경우만 사용
                description += f"📖 Book Introduction:\n{desc[:500]}{'...' if len(desc) > 500 else ''}\n\n"
        if not description or "📖 Book Introduction:" not in description:
            # 영어 description이 없거나 한글 description만 있는 경우
            if book_title:
                # description이 없으면 하드코딩된 영어 설명 시도
                en_desc = get_english_book_description(book_title)
                if en_desc:
                    description += f"📖 Book Introduction:\n{en_desc[:500]}...\n\n"
                else:
                    # 하드코딩된 설명도 없으면 기본 메시지
                    description += f"📖 Book Introduction:\nA book review video about this literary work.\n\n"
        
        if book_info.get('authors'):
            # 영어와 한글 작가 이름 모두 표시
            authors_ko = []
            authors_en = []
            for author_name in book_info['authors']:
                if is_english_title(author_name):
                    # 영어 작가 이름인 경우
                    authors_en.append(author_name)
                    ko_author = translate_author_name_to_korean(author_name)
                    authors_ko.append(ko_author if ko_author != author_name else author_name)
                else:
                    # 한글 작가 이름인 경우
                    authors_ko.append(author_name)
                    en_author = translate_author_name(author_name)
                    authors_en.append(en_author if en_author != author_name else author_name)
            
            en_author_str = ', '.join(authors_en) if authors_en else ', '.join(book_info['authors'])
            description += f"✍️ Author: {en_author_str}\n"
        elif author:
            # book_info에 authors가 없지만 author 파라미터가 있는 경우
            if is_english_title(author):
                en_author = author
            else:
                en_author = translate_author_name(author)
            description += f"✍️ Author: {en_author}\n"
    elif author:
        # book_info가 없지만 author 파라미터가 있는 경우
        if is_english_title(author):
            en_author = author
        else:
            en_author = translate_author_name(author)
        description += f"✍️ Author: {en_author}\n"
    if book_info and book_info.get('publishedDate'):
        description += f"📅 Published: {book_info['publishedDate']}\n"
    
    description += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔔 Subscribe and like to support video creation!

💬 Please leave a comment!
Have you read this book? What are your thoughts?
Your comments and reviews mean a lot to us!
Feel free to share any questions or thoughts in the comments below! 💕

📌 We'd love to hear your thoughts on this book:
• Honest reviews from those who have read it
• Book recommendations similar to this one
• Which part of the book impressed you the most?
• Other works by this author you'd recommend

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#BookSummary #Reading #BookTube #CoreSummary #BookRecommendation #Knowledge
"""
    return description

def _generate_description_en_with_ko(book_info: Optional[Dict] = None, book_title: str = None, timestamps: Optional[Dict] = None, author: Optional[str] = None) -> str:
    """영문 설명 생성 (영어 먼저, 한글 나중)"""
    # 영어 부분
    en_desc = _generate_description_en(book_info, book_title, include_header=True, timestamps=timestamps, author=author)
    
    # 한글 부분
    ko_desc = """📚 5분 만에 읽는 책 | 바쁜 현대인을 위한 핵심 요약

이 영상은 NotebookLM과 AI를 활용하여 생성된 '핵심 요약' 영상입니다.
바쁜 일상 속에서 5분 투자로 책의 핵심을 파악해보세요.

📝 영상 구성:
• 5분 핵심 요약 (GPT 생성) - 책의 주요 메시지와 인사이트
• 상세 심층 분석 (NotebookLM) - 작가의 의도와 깊이 있는 해석

"""
    if book_info:
        # 책 소개 추가 (book_info의 description이 한글인 경우만 사용)
        if book_info.get('description'):
            # description이 있으면 한글인지 확인
            desc = book_info['description'].strip()
            if desc and not is_english_title(desc[:100]):  # 처음 100자로 한글인지 판단
                # 한글 description인 경우만 사용
                ko_desc += f"📖 책 소개:\n{desc[:500]}{'...' if len(desc) > 500 else ''}\n\n"
        if book_info.get('authors'):
            # 한글과 영어 작가 이름 모두 표시
            authors_ko = []
            authors_en = []
            for author in book_info['authors']:
                if is_english_title(author):
                    # 영어 작가 이름인 경우
                    authors_en.append(author)
                    ko_author = translate_author_name_to_korean(author)
                    authors_ko.append(ko_author if ko_author != author else author)
                else:
                    # 한글 작가 이름인 경우
                    authors_ko.append(author)
                    en_author = translate_author_name(author)
                    authors_en.append(en_author if en_author != author else author)
            
            ko_author_str = ', '.join(authors_ko) if authors_ko else ', '.join(book_info['authors'])
            ko_desc += f"✍️ 작가: {ko_author_str}\n"
        elif author:
            # book_info에 authors가 없지만 author 파라미터가 있는 경우
            if is_english_title(author):
                # 영어 작가 이름인 경우 한글로 변환
                ko_author = translate_author_name_to_korean(author)
            else:
                # 한글 작가 이름인 경우 그대로 사용
                ko_author = author
            ko_desc += f"✍️ 작가: {ko_author}\n"
    elif author:
        # book_info가 없지만 author 파라미터가 있는 경우
        if is_english_title(author):
            # 영어 작가 이름인 경우 한글로 변환
            ko_author = translate_author_name_to_korean(author)
        else:
            # 한글 작가 이름인 경우 그대로 사용
            ko_author = author
        ko_desc += f"✍️ 작가: {ko_author}\n"
    if book_info and book_info.get('publishedDate'):
        ko_desc += f"📅 출간일: {book_info['publishedDate']}\n"
    
    ko_desc += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔔 구독과 좋아요는 영상 제작에 큰 힘이 됩니다!

💬 댓글을 남겨주세요!
이 책을 읽어보셨나요? 어떤 생각이 드셨나요?
댓글로 여러분의 생각과 감상을 공유해주시면 큰 힘이 됩니다.
질문이나 궁금한 점도 언제든지 댓글로 남겨주세요! 💕

📌 이 책에 대한 여러분의 의견이 궁금합니다:
• 이 책을 읽어보신 분들의 솔직한 후기
• 이 책과 비슷한 책 추천
• 이 책의 어떤 부분이 가장 인상 깊으셨나요?
• 작가의 다른 작품 중 추천하고 싶은 책

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#책요약 #독서 #북튜버 #5분독서 #지식창고 #BookSummary #Reading
"""
    
    # 영어 먼저, 한글 나중
    return f"{en_desc}\n\n{'='*60}\n\n{ko_desc}"

def detect_genre_tags(book_info: Optional[Dict] = None, book_title: str = None) -> Tuple[list, list]:
    """
    책의 장르를 감지하여 장르별 특화 태그 생성
    
    Returns:
        (한글_장르_태그_리스트, 영문_장르_태그_리스트)
    """
    ko_genre_tags = []
    en_genre_tags = []
    
    if not book_info:
        return ko_genre_tags, en_genre_tags
    
    description = book_info.get('description', '').lower() if book_info.get('description') else ''
    categories = [cat.lower() for cat in book_info.get('categories', [])] if book_info.get('categories') else []
    all_text = ' '.join([description] + categories).lower()
    
    # 장르별 태그 매핑
    genre_mapping = {
        # 소설/문학
        ('소설', 'novel', 'fiction', 'literature', 'literary'): {
            'ko': ['소설', '문학', '소설리뷰', '문학작품', '고전소설', '현대소설', '문학강의', '소설분석'],
            'en': ['Novel', 'Fiction', 'Literature', 'LiteraryFiction', 'ClassicNovel', 'ModernNovel', 'LiteraryAnalysis']
        },
        # 논픽션
        ('논픽션', 'non-fiction', 'nonfiction', 'essay'): {
            'ko': ['논픽션', '에세이', '수필', '비소설', '인문학', '교양서'],
            'en': ['NonFiction', 'Essay', 'NonFictionBook', 'Humanities', 'Educational']
        },
        # 철학
        ('철학', 'philosophy', 'philosophical'): {
            'ko': ['철학', '철학서', '철학책', '인문학', '사상서'],
            'en': ['Philosophy', 'Philosophical', 'PhilosophyBook', 'PhilosophyDiscussion']
        },
        # 과학
        ('과학', 'science', 'scientific', 'cosmos', 'physics'): {
            'ko': ['과학', '과학서', '과학책', '과학도서', '과학강의'],
            'en': ['Science', 'ScienceBook', 'Scientific', 'ScienceEducation', 'Cosmos']
        },
        # 역사
        ('역사', 'history', 'historical'): {
            'ko': ['역사', '역사서', '역사책', '역사도서'],
            'en': ['History', 'Historical', 'HistoryBook', 'HistoricalBook']
        },
        # 심리학
        ('심리', 'psychology', 'psychological'): {
            'ko': ['심리학', '심리서', '심리책', '심리도서'],
            'en': ['Psychology', 'PsychologyBook', 'Psychological', 'MentalHealth']
        },
        # 자기계발
        ('자기계발', 'self-help', 'selfhelp', 'development', 'improvement'): {
            'ko': ['자기계발', '성장', '개발서', '성공서'],
            'en': ['SelfHelp', 'SelfDevelopment', 'PersonalGrowth', 'SuccessBook']
        },
        # 시
        ('시', 'poetry', 'poem', 'poet'): {
            'ko': ['시', '시집', '시인', '시문학'],
            'en': ['Poetry', 'Poem', 'PoetryCollection', 'Poet']
        },
    }
    
    # 장르 감지 및 태그 추가
    for keywords, tags in genre_mapping.items():
        if any(keyword in all_text for keyword in keywords):
            ko_genre_tags.extend(tags['ko'][:3])  # 최대 3개
            en_genre_tags.extend(tags['en'][:3])  # 최대 3개
            break  # 첫 번째 매칭 장르만 사용
    
    return ko_genre_tags, en_genre_tags

def generate_tags(book_title: str = None, book_info: Optional[Dict] = None, lang: str = "both") -> list:
    """태그 생성 (책 정보 활용, 두 언어 포함, 검색 최적화)"""
    # 기본 태그 (SEO 최적화 - 검색 키워드 중심, 검색량 높은 순서)
    ko_base_tags = [
        '책요약', '핵심요약', '줄거리요약', '책리뷰', 
        '독서', '북튜버', '책추천', '독서법', '책읽기', 
        '리뷰영상', '독서후기', '인문학', '지식창고',
        '책분석', '독서모임', '책토론', '책읽는법',
        '독서습관', '자기계발', '북크리에이터'
    ]
    en_base_tags = [
        'BookSummary', 'CoreSummary', 'PlotSummary', 'BookReview',
        'Reading', 'BookTube', 'BookRecommendation', 'ReadingTips', 
        'Books', 'ReviewVideo', 'Literature', 'Knowledge', 
        'BookAnalysis', 'BookClub', 'SelfImprovement', 'ReadingHabit', 
        'BookCreator', 'LiteratureReview', 'ShortSummary'
    ]
    
    # 추천 기관/상/대학 태그 (일반적으로 유용한 태그들)
    # 책의 특성에 따라 선택적으로 추가될 수 있음
    institution_tags_ko = []
    institution_tags_en = []
    
    # 노벨문학상 수상작인 경우 (book_info에서 확인 가능)
    if book_info:
        # book_info의 description이나 categories에서 노벨상 관련 키워드 확인
        description = book_info.get('description', '').lower() if book_info.get('description') else ''
        categories = [cat.lower() for cat in book_info.get('categories', [])] if book_info.get('categories') else []
        
        all_text = ' '.join([description] + categories).lower()
        
        # 노벨상 관련
        if 'nobel' in all_text or '노벨' in all_text:
            institution_tags_en.extend(['NobelPrize', 'NobelLiteraturePrize'])
            institution_tags_ko.append('노벨문학상')
        
        # 맨부커상 관련
        if 'man booker' in all_text or 'booker prize' in all_text or '맨부커' in all_text:
            institution_tags_en.extend(['ManBookerPrize', 'BookerPrize'])
            institution_tags_ko.append('맨부커상')
        
        # 퓰리처상 관련
        if 'pulitzer' in all_text or '퓰리처' in all_text:
            institution_tags_en.append('PulitzerPrize')
            institution_tags_ko.append('퓰리처상')
    
    # 일반적인 추천 기관 태그 (책리뷰 채널에 적합한 기관 목록)
    # 세계적/국내기관 및 미디어
    media_institution_tags_en = [
        'NewYorkTimes', 'Amazon', 'TIMEMagazine', 'CNN', 'Newsweek'
    ]
    media_institution_tags_ko = [
        '뉴욕타임즈', '아마존', '타임지', 'CNN', '뉴스위크'
    ]
    
    # 주요 서점
    bookstore_tags_ko = [
        '교보문고', '알라딘', 'YES24'
    ]
    
    # 주요 도서관
    library_tags_ko = [
        '국립중앙도서관', '서울도서관'
    ]
    
    # 정부기관
    government_tags_ko = [
        '문화체육관광부', '한국출판문화산업진흥원'
    ]
    
    # 유명 대학·교육기관
    university_tags_en = [
        'Harvard', 'UniversityOfChicago', 'TokyoUniversity', 'PekingUniversity', 'CollegeBoard'
    ]
    university_tags_ko = [
        '서울대학교', '고려대학교', '연세대학교', '하버드대학교', '시카고대학교', 
        '도쿄대학교', '베이징대학교', '미국대학위원회'
    ]
    
    # 문학상 및 수상기구 (일부는 이미 위에서 조건부로 추가됨)
    literary_award_tags_en = [
        'GoncourtPrize', 'RenaudotPrize'
    ]
    literary_award_tags_ko = [
        '공쿠르상', '르노도상'
    ]
    
    # 기타 추천 출판사/단체
    other_tags_ko = [
        '출판저널', '학교도서관저널', '서평지', '독서운동', '환경책선정위원회'
    ]
    
    # 모든 기관 태그를 우선순위에 따라 추가
    # 미디어 기관 (높은 우선순위)
    institution_tags_en.extend(media_institution_tags_en[:3])  # 최대 3개
    institution_tags_ko.extend(media_institution_tags_ko[:3])  # 최대 3개
    
    # 서점 (중간 우선순위)
    institution_tags_ko.extend(bookstore_tags_ko[:2])  # 최대 2개
    
    # 도서관 (중간 우선순위)
    institution_tags_ko.extend(library_tags_ko[:1])  # 최대 1개
    
    # 대학 (높은 우선순위)
    institution_tags_en.extend(university_tags_en[:3])  # 최대 3개
    institution_tags_ko.extend(university_tags_ko[:3])  # 최대 3개
    
    # 문학상 (조건부로 이미 추가된 것 외에)
    institution_tags_en.extend(literary_award_tags_en[:1])  # 최대 1개
    institution_tags_ko.extend(literary_award_tags_ko[:1])  # 최대 1개
    
    # 기타 (낮은 우선순위, 공간이 있을 때만)
    if len(institution_tags_ko) < 10:  # 공간이 있으면
        institution_tags_ko.extend(other_tags_ko[:2])  # 최대 2개
    
    # 책 제목 기반 태그
    ko_book_tags = []
    en_book_tags = []
    
    if book_title:
        # book_title이 영어인지 한글인지 판단
        if is_english_title(book_title):
            # 영어 제목이 들어온 경우
            en_title = book_title
            ko_title = translate_book_title_to_korean(book_title)
        else:
            # 한글 제목이 들어온 경우
            ko_title = book_title
            en_title = translate_book_title(book_title)
        
        # 한글 제목 태그 (한글 제목이 있고 영어 제목과 다른 경우만)
        if ko_title and ko_title != en_title and not is_english_title(ko_title):
            ko_book_tags.append(ko_title)
            ko_book_tags.append(f"{ko_title} 리뷰")
            ko_book_tags.append(f"{ko_title} 책")
        
        # 영어 제목 태그 (영어 제목이 있고 한글 제목과 다른 경우만)
        if en_title and en_title != ko_title and is_english_title(en_title):
            en_book_tags.append(en_title)
            en_book_tags.append(f"{en_title} Review")
            en_book_tags.append(f"{en_title} Book")
    
    # 작가 기반 태그
    if book_info and book_info.get('authors'):
        for author in book_info['authors']:
            # 작가 이름이 한글인지 영어인지 판단
            if is_english_title(author):
                # 영어 작가 이름인 경우
                en_author = author
                ko_author = None  # 한글 작가 이름이 없으면 None
            else:
                # 한글 작가 이름인 경우
                ko_author = author
                en_author = translate_author_name(author)
            
            if ko_author:
                ko_book_tags.append(f"{ko_author} 작가")
            if en_author and en_author != ko_author:
                en_book_tags.append(en_author)
                en_book_tags.append(f"{en_author} Author")
    
    # 장르/카테고리 태그 (book_info에서 추출 가능한 경우)
    if book_info and book_info.get('categories'):
        for category in book_info['categories'][:3]:  # 최대 3개
            # 카테고리가 한글인지 영어인지 판단
            if is_english_title(category):
                en_book_tags.append(category)
            else:
                ko_book_tags.append(category)
    
    # 장르별 특화 태그 추가
    ko_genre_tags, en_genre_tags = detect_genre_tags(book_info, book_title)
    
    # 현재 연도 가져오기
    current_year = datetime.now().year
    
    # 트렌딩/검색량 높은 키워드 태그 추가
    ko_trending_tags = [
        f'책추천{current_year}', '독서챌린지', '책읽기습관', '독서모임', '문학토론',
        '책리뷰채널', '북튜버추천', '독서법추천', '책읽는법', '독서습관만들기'
    ]
    en_trending_tags = [
        f'BookRecommendation{current_year}', 'ReadingChallenge', 'BookClub', 'LiteraryDiscussion',
        'BookReviewChannel', 'BookTubeRecommendation', 'ReadingMethod', 'HowToRead'
    ]
    
    # 태그 결합 (중복 제거, 우선순위: 기본 > 장르 > 기관 > 책제목/작가 > 트렌딩)
    # 기관 태그는 검색 최적화에 중요하므로 중간에 배치
    ko_tags = list(dict.fromkeys(
        ko_base_tags[:12] +  # 기본 태그 (검색량 높은 것 우선)
        ko_genre_tags +      # 장르 태그
        institution_tags_ko[:5] +  # 기관 태그 (최대 5개)
        ko_book_tags +       # 책 제목/작가 태그
        ko_trending_tags[:3]  # 트렌딩 태그 (최대 3개)
    ))
    en_tags = list(dict.fromkeys(
        en_base_tags[:12] +  # 기본 태그
        en_genre_tags +      # 장르 태그
        institution_tags_en[:5] +  # 기관 태그 (최대 5개)
        en_book_tags +       # 책 제목/작가 태그
        en_trending_tags[:3]  # 트렌딩 태그 (최대 3개)
    ))
    
    # YouTube 태그 제한 (최대 500자, 약 30-40개 태그)
    # 각 태그는 보통 10-15자이므로 최대 30개 정도로 제한
    max_tags = 30
    ko_tags = ko_tags[:max_tags]
    en_tags = en_tags[:max_tags]
    
    if lang == "ko":
        # 한글 태그 먼저, 영어 태그 나중
        return ko_tags + en_tags
    elif lang == "en":
        # 영어 태그 먼저, 한글 태그 나중
        return en_tags + ko_tags
    else:
        return ko_tags + en_tags


def find_audio_files(audio_dir: str = "assets/audio") -> Tuple[Optional[Path], Optional[Path]]:
    """한글/영문 오디오 파일 찾기"""
    audio_path = Path(audio_dir)
    audio_files = list(audio_path.glob("*.m4a")) + list(audio_path.glob("*.wav")) + list(audio_path.glob("*.mp3"))
    
    korean_audio = None
    english_audio = None
    
    for audio_file in audio_files:
        filename = audio_file.stem
        # 한글 포함 여부 확인
        has_korean = any(ord(c) > 127 for c in filename)
        
        if has_korean:
            korean_audio = audio_file
        else:
            english_audio = audio_file
    
    return korean_audio, english_audio


# load_book_info는 utils.file_utils에서 import됨


def preview_metadata(title: str, description: str, tags: list, lang: str):
    """메타데이터 미리보기"""
    print("=" * 60)
    print(f"📋 메타데이터 미리보기 ({lang.upper()})")
    print("=" * 60)
    print()
    print(f"📌 제목:")
    print(f"   {title}")
    print()
    print(f"📝 설명:")
    print(description)
    print()
    print(f"🏷️ 태그 ({len(tags)}개):")
    print(f"   {', '.join(tags)}")
    print()
    print("=" * 60)
    print()


def calculate_timestamps_from_video(video_path: Path, safe_title_str: str, lang: str) -> Optional[Dict]:
    """
    영상 파일과 관련 오디오/비디오 파일에서 timestamp 정보 계산
    
    Returns:
        timestamps 딕셔너리 또는 None
        {
            'summary_duration': float,
            'notebooklm_duration': float,
            'review_duration': float
        }
    """
    try:
        from moviepy.editor import VideoFileClip, AudioFileClip
        import subprocess
        
        lang_suffix = "kr" if lang == "ko" else "en"
        timestamps = {
            'summary_duration': 0,
            'notebooklm_duration': 0,
            'review_duration': 0
        }
        
        # Summary 오디오 길이 확인 (summary 또는 longform 파일 모두 확인)
        summary_audio_path = None
        possible_paths = [
            Path(f"assets/audio/{safe_title_str}_summary_{lang_suffix}.mp3"),
            Path(f"assets/audio/{safe_title_str}_longform_{lang_suffix}.mp3")
        ]
        
        for path in possible_paths:
            if path.exists():
                summary_audio_path = path
                break
        
        # 호환성을 위해 ko 패턴도 확인
        if not summary_audio_path and lang_suffix == "kr":
            possible_paths_old = [
                Path(f"assets/audio/{safe_title_str}_summary_ko.mp3"),
                Path(f"assets/audio/{safe_title_str}_longform_ko.mp3")
            ]
            for path in possible_paths_old:
                if path.exists():
                    summary_audio_path = path
                    break
        
        if summary_audio_path and summary_audio_path.exists():
            try:
                audio = AudioFileClip(str(summary_audio_path))
                timestamps['summary_duration'] = audio.duration
                audio.close()
            except:
                # ffprobe로 시도
                result = subprocess.run(
                    ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1', str(summary_audio_path)],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    timestamps['summary_duration'] = float(result.stdout.strip().split('=')[1])
        
        # NotebookLM Video 길이 확인
        notebooklm_video_path = Path(f"assets/video/{safe_title_str}_notebooklm_{lang_suffix}.mp4")
        if not notebooklm_video_path.exists() and lang_suffix == "kr":
            notebooklm_video_path = Path(f"assets/video/{safe_title_str}_notebooklm_ko.mp4")
        
        if notebooklm_video_path.exists():
            try:
                video = VideoFileClip(str(notebooklm_video_path))
                timestamps['notebooklm_duration'] = video.duration
                video.close()
            except:
                # ffprobe로 시도
                result = subprocess.run(
                    ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1', str(notebooklm_video_path)],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    timestamps['notebooklm_duration'] = float(result.stdout.strip().split('=')[1])
        
        # Review 오디오 길이 확인
        review_audio_path = Path(f"assets/audio/{safe_title_str}_review_{lang_suffix}.m4a")
        if not review_audio_path.exists() and lang_suffix == "kr":
            review_audio_path = Path(f"assets/audio/{safe_title_str}_review_ko.m4a")
        
        if not review_audio_path.exists():
            # 다른 확장자 시도
            for ext in ['.mp3', '.wav']:
                test_path = Path(f"assets/audio/{safe_title_str}_review_{lang_suffix}{ext}")
                if test_path.exists():
                    review_audio_path = test_path
                    break
        
        if review_audio_path.exists():
            try:
                audio = AudioFileClip(str(review_audio_path))
                timestamps['review_duration'] = audio.duration
                audio.close()
            except:
                # ffprobe로 시도
                result = subprocess.run(
                    ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1', str(review_audio_path)],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    timestamps['review_duration'] = float(result.stdout.strip().split('=')[1])
        
        # Summary가 없으면 timestamp 추가 안 함
        if timestamps['summary_duration'] == 0:
            return None
        
        return timestamps
        
    except Exception as e:
        print(f"⚠️ Timestamp 계산 실패: {e}")
        return None

def find_thumbnail_for_video(video_path: Path, lang: str, safe_title_str: str = None) -> Optional[str]:
    """영상 파일에 맞는 썸네일 찾기"""
    video_dir = video_path.parent
    
    # safe_title_str이 없으면 video_path에서 추출
    if safe_title_str is None:
        video_stem = video_path.stem
        safe_title_str = video_stem.replace('_review_with_summary_ko', '').replace('_review_with_summary_en', '')
        safe_title_str = safe_title_str.replace('_review_ko', '').replace('_review_en', '').replace('_review', '')
        safe_title_str = safe_title_str.replace('_with_summary', '')
    
    # 1순위: 표준 네이밍 규칙 ({safe_title}_thumbnail_{lang}.jpg/png)
    lang_suffix = "kr" if lang == "ko" else "en"
    for ext in [".jpg", ".png"]:
        thumbnail_path = video_dir / f"{safe_title_str}_thumbnail_{lang_suffix}{ext}"
        if not thumbnail_path.exists() and lang_suffix == "kr":
            thumbnail_path = video_dir / f"{safe_title_str}_thumbnail_ko{ext}"
    if thumbnail_path.exists():
        return str(thumbnail_path)
    
    # 2순위: 영상 파일명 기반
    video_stem = video_path.stem
    for ext in [".jpg", ".png"]:
        thumbnail_path = video_dir / f"{video_stem}_thumbnail_{lang_suffix}{ext}"
        if not thumbnail_path.exists() and lang_suffix == "kr":
            thumbnail_path = video_dir / f"{video_stem}_thumbnail_ko{ext}"
    if thumbnail_path.exists():
        return str(thumbnail_path)
    
    # 3순위: 언어 구분 없는 썸네일
    for ext in [".jpg", ".png"]:
        thumbnail_path = video_dir / f"{safe_title_str}_thumbnail{ext}"
    if thumbnail_path.exists():
        return str(thumbnail_path)
    
    return None


def save_metadata(video_path: Path, title: str, description: str, tags: list, lang: str, book_info: Optional[Dict] = None, thumbnail_path: Optional[str] = None, safe_title_str: str = None):
    """메타데이터를 JSON 파일로 저장"""
    # 영문 메타데이터의 경우 book_info의 authors를 영어로 변환
    if lang == "en" and book_info and book_info.get('authors'):
        # book_info를 복사해서 수정 (원본 변경 방지)
        book_info_copy = book_info.copy()
        book_info_copy['authors'] = [translate_author_name(author) for author in book_info['authors']]
        book_info = book_info_copy
    
    metadata = {
        'video_path': str(video_path),
        'title': title,
        'description': description,
        'tags': tags,
        'language': lang,
        'book_info': book_info
    }
    
    # 썸네일 경로 찾기 (제공되지 않았으면 자동으로 찾기)
    if not thumbnail_path:
        thumbnail_path = find_thumbnail_for_video(video_path, lang, safe_title_str)
    
    # 썸네일 경로도 메타데이터에 포함
    if thumbnail_path:
        metadata['thumbnail_path'] = thumbnail_path
    
    metadata_path = video_path.with_suffix('.metadata.json')
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"💾 메타데이터 저장: {metadata_path.name}")
    if thumbnail_path:
        print(f"   📸 썸네일: {Path(thumbnail_path).name}")
    return metadata_path


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='영상 생성 및 메타데이터 미리보기')
    parser.add_argument('--book-title', type=str, default="노르웨이의 숲", help='책 제목')
    parser.add_argument('--author', type=str, help='저자 이름 (메타데이터 생성 시 사용)')
    parser.add_argument('--image-dir', type=str, help='이미지 디렉토리')
    parser.add_argument('--skip-video', action='store_true', help='영상 생성 건너뛰기 (메타데이터만 생성)')
    parser.add_argument('--metadata-only', action='store_true', help='메타데이터만 생성 (영상/오디오 없이)')
    parser.add_argument('--auto-upload', action='store_true', help='자동 업로드 (점검 없이)')
    parser.add_argument('--skip-thumbnail', action='store_true', help='썸네일 생성 건너뛰기')
    parser.add_argument('--use-dalle-thumbnail', action='store_true', help='DALL-E를 사용하여 썸네일 배경 생성')
    
    args = parser.parse_args()
    
    # 메타데이터만 생성하는 경우
    if args.metadata_only:
        print("=" * 60)
        print("📋 메타데이터 생성")
        print("=" * 60)
        print()
        
        # 책 정보 로드 (description이 없으면 Google Books API에서 다시 가져옴)
        # 저자 정보는 book_info.json에서 가져오거나 args.author 사용
        book_info = load_book_info(args.book_title, author=args.author)
        if book_info:
            author = book_info.get('authors', [None])[0] if book_info.get('authors') else args.author
            # description이 없으면 다시 시도
            if not book_info.get('description') or book_info.get('description', '').strip() == '':
                book_info = load_book_info(args.book_title, author=author)
            print(f"📚 책 정보 로드 완료: {book_info.get('title', args.book_title)}")
        else:
            # book_info가 없으면 author 정보로 임시 book_info 생성
            if args.author:
                book_info = {'authors': [args.author]}
                print(f"📚 저자 정보 사용: {args.author}")
        print()
        
        safe_title_str = get_standard_safe_title(args.book_title)
        
        # 한글 메타데이터 생성 (영상 파일이 없어도 생성)
        video_path_ko = Path(f"output/{safe_title_str}_kr.mp4")
        
        print("📋 한글 메타데이터 생성 중...")
        title_ko = generate_title(args.book_title, lang='ko', author=args.author)
        # Timestamp 계산 (영상 파일이 있으면)
        timestamps_ko = None
        if video_path_ko.exists():
            timestamps_ko = calculate_timestamps_from_video(video_path_ko, safe_title_str, 'ko')
        else:
            print(f"⚠️ 한글 영상을 찾을 수 없습니다. Timestamp 없이 메타데이터 생성: {video_path_ko}")
        
        description_ko = generate_description(book_info, lang='ko', book_title=args.book_title, timestamps=timestamps_ko, author=args.author)
        tags_ko = generate_tags(book_title=args.book_title, book_info=book_info, lang='ko')
        
        save_metadata(
            video_path_ko,
            title_ko,
            description_ko,
            tags_ko,
            'ko',
            book_info,
            thumbnail_path=None,  # 자동으로 찾기
            safe_title_str=safe_title_str
        )
        
        # 영문 메타데이터 생성 (영상 파일이 없어도 생성)
        video_path_en = Path(f"output/{safe_title_str}_en.mp4")
        
        print("\n📋 영문 메타데이터 생성 중...")
        title_en = generate_title(args.book_title, lang='en', author=args.author)
        # Timestamp 계산 (영상 파일이 있으면)
        timestamps_en = None
        if video_path_en.exists():
            timestamps_en = calculate_timestamps_from_video(video_path_en, safe_title_str, 'en')
        else:
            print(f"⚠️ 영문 영상을 찾을 수 없습니다. Timestamp 없이 메타데이터 생성: {video_path_en}")
        
        description_en = generate_description(book_info, lang='en', book_title=args.book_title, timestamps=timestamps_en, author=args.author)
        tags_en = generate_tags(book_title=args.book_title, book_info=book_info, lang='en')
        
        save_metadata(
            video_path_en,
            title_en,
            description_en,
            tags_en,
            'en',
            book_info,
            thumbnail_path=None,  # 자동으로 찾기
            safe_title_str=safe_title_str
        )
        
        print("\n✅ 메타데이터 생성 완료!")
        return
    
    # 오디오 파일 찾기
    korean_audio, english_audio = find_audio_files()
    
    print("=" * 60)
    print("🎬 영상 생성 및 메타데이터 준비")
    print("=" * 60)
    print()
    
    if not korean_audio and not english_audio:
        print("❌ 오디오 파일을 찾을 수 없습니다.")
        return
    
    # 책 정보 로드 (description이 없으면 Google Books API에서 다시 가져옴)
    book_info = load_book_info(args.book_title)
    if book_info:
        author = book_info.get('authors', [None])[0] if book_info.get('authors') else None
        # description이 없으면 다시 시도
        if not book_info.get('description') or book_info.get('description', '').strip() == '':
            book_info = load_book_info(args.book_title, author=author)
        print(f"📚 책 정보 로드 완료: {book_info.get('title', args.book_title)}")
        print()
    
    # 이미지 디렉토리 설정
    safe_title_str = get_standard_safe_title(args.book_title)
    if args.image_dir is None:
        args.image_dir = f"assets/images/{safe_title_str}"
    
    videos_created = []
    
    # 한글 영상 제작
    if korean_audio:
        print("🇰🇷 한글 영상")
        print("-" * 60)
        print(f"   오디오: {korean_audio.name}")
        print()
        
        output_path = Path(f"output/{safe_title_str}_kr.mp4")
        
        # 영상 생성
        if not args.skip_video:
            if output_path.exists():
                print(f"⚠️ 영상이 이미 존재합니다: {output_path.name}")
                response = input("   다시 생성하시겠습니까? (y/n, 기본값: n): ").strip().lower()
                if response != 'y':
                    print("   ⏭️ 건너뜀\n")
                else:
                    maker = VideoMaker(resolution=(1920, 1080), fps=30)
                    maker.create_video(
                        audio_path=str(korean_audio),
                        image_dir=args.image_dir,
                        output_path=str(output_path),
                        add_subtitles_flag=False,
                        language="ko"
                    )
                    print()
            else:
                maker = VideoMaker(resolution=(1920, 1080), fps=30)
                maker.create_video(
                    audio_path=str(korean_audio),
                    image_dir=args.image_dir,
                    output_path=str(output_path),
                    add_subtitles_flag=False,
                    language="ko"
                )
                print()
        else:
            print("   ⏭️ 영상 생성 건너뜀 (--skip-video)")
            print()
        
        # 메타데이터 생성
        title = generate_title(args.book_title, lang="ko", author=args.author)
        description = generate_description(book_info, lang="ko", book_title=args.book_title, author=args.author)
        tags = generate_tags(book_title=args.book_title, book_info=book_info, lang="ko")
        
        # 메타데이터 미리보기
        preview_metadata(title, description, tags, "ko")
        
        # 썸네일 생성 (선택사항)
        thumbnail_path = None
        if THUMBNAIL_AVAILABLE and not args.skip_thumbnail:
            try:
                generator = ThumbnailGenerator(use_dalle=args.use_dalle_thumbnail)
                
                # 먼저 output 폴더의 PNG 파일 확인 및 처리
                print("🖼️ 썸네일 처리 중...")
                png_thumbnails = generator.process_png_thumbnails(args.book_title)
                
                if png_thumbnails.get('ko'):
                    thumbnail_path = png_thumbnails['ko']
                    print(f"   ✅ 한글 썸네일: PNG에서 변환 완료")
                    print()
                else:
                    # PNG 파일이 없으면 경고만 출력
                    print("   ⚠️ 한글 썸네일 PNG 파일을 찾을 수 없습니다.")
                    print("   💡 Nano Banana에서 만든 썸네일 PNG 파일을 output 폴더에 넣어주세요.")
                    print("      파일명 예시: {책제목}_kr.png 또는 {책제목}_ko.png")
                    print()
            except Exception as e:
                print(f"⚠️ 썸네일 생성 실패: {e}")
                print()
        
        # 메타데이터 저장
        if output_path.exists():
            metadata_path = save_metadata(output_path, title, description, tags, "ko", book_info, thumbnail_path, safe_title_str=safe_title_str)
            # 저장된 메타데이터에서 썸네일 경로 읽기
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    saved_metadata = json.load(f)
                    thumbnail_path = saved_metadata.get('thumbnail_path')
            videos_created.append({
                'video_path': output_path,
                'metadata_path': metadata_path,
                'thumbnail_path': thumbnail_path,
                'title': title,
                'description': description,
                'tags': tags,
                'language': 'ko'
            })
        
        print()
    
    # 영문 영상 제작
    if english_audio:
        print("🇺🇸 영문 영상")
        print("-" * 60)
        print(f"   오디오: {english_audio.name}")
        print()
        
        output_path = Path(f"output/{safe_title_str}_en.mp4")
        
        # 영상 생성
        if not args.skip_video:
            if output_path.exists():
                print(f"⚠️ 영상이 이미 존재합니다: {output_path.name}")
                response = input("   다시 생성하시겠습니까? (y/n, 기본값: n): ").strip().lower()
                if response != 'y':
                    print("   ⏭️ 건너뜀\n")
                else:
                    maker = VideoMaker(resolution=(1920, 1080), fps=30)
                    maker.create_video(
                        audio_path=str(english_audio),
                        image_dir=args.image_dir,
                        output_path=str(output_path),
                        add_subtitles_flag=False,
                        language="en"
                    )
                    print()
            else:
                maker = VideoMaker(resolution=(1920, 1080), fps=30)
                maker.create_video(
                    audio_path=str(english_audio),
                    image_dir=args.image_dir,
                    output_path=str(output_path),
                    add_subtitles_flag=False,
                    language="en"
                )
                print()
        else:
            print("   ⏭️ 영상 생성 건너뜀 (--skip-video)")
            print()
        
        # 메타데이터 생성
        title = generate_title(args.book_title, lang="en", author=args.author)
        description = generate_description(book_info, lang="en", book_title=args.book_title, author=args.author)
        tags = generate_tags(book_title=args.book_title, book_info=book_info, lang="en")
        
        # 메타데이터 미리보기
        preview_metadata(title, description, tags, "en")
        
        # 썸네일 생성 (선택사항)
        thumbnail_path = None
        if THUMBNAIL_AVAILABLE and not args.skip_thumbnail:
            try:
                generator = ThumbnailGenerator(use_dalle=args.use_dalle_thumbnail)
                
                # 먼저 output 폴더의 PNG 파일 확인 및 처리
                print("🖼️ 썸네일 처리 중...")
                png_thumbnails = generator.process_png_thumbnails(args.book_title)
                
                if png_thumbnails.get('en'):
                    thumbnail_path = png_thumbnails['en']
                    print(f"   ✅ 영어 썸네일: PNG에서 변환 완료")
                    print()
                else:
                    # PNG 파일이 없으면 경고만 출력
                    print("   ⚠️ 영어 썸네일 PNG 파일을 찾을 수 없습니다.")
                    print("   💡 Nano Banana에서 만든 썸네일 PNG 파일을 output 폴더에 넣어주세요.")
                    print("      파일명 예시: {책제목}_en.png")
                    print()
            except Exception as e:
                print(f"⚠️ 썸네일 생성 실패: {e}")
                print()
        
        # 메타데이터 저장
        if output_path.exists():
            metadata_path = save_metadata(output_path, title, description, tags, "en", book_info, thumbnail_path, safe_title_str=safe_title_str)
            # 저장된 메타데이터에서 썸네일 경로 읽기
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    saved_metadata = json.load(f)
                    thumbnail_path = saved_metadata.get('thumbnail_path')
            videos_created.append({
                'video_path': output_path,
                'metadata_path': metadata_path,
                'thumbnail_path': thumbnail_path,
                'title': title,
                'description': description,
                'tags': tags,
                'language': 'en'
            })
        
        print()
    
    # 최종 요약
    print("=" * 60)
    print("✅ 작업 완료!")
    print("=" * 60)
    print()
    
    if videos_created:
        print(f"📹 생성된 영상: {len(videos_created)}개")
        for video_info in videos_created:
            print(f"   • {video_info['video_path'].name} ({video_info['language'].upper()})")
            print(f"     메타데이터: {video_info['metadata_path'].name}")
        print()
        
        # 업로드 옵션
        if not args.auto_upload:
            print("📤 업로드하시겠습니까?")
            print("   메타데이터 파일을 확인한 후 업로드할 수 있습니다.")
            print("   업로드하려면: python src/05_auto_upload.py")
            print()
    else:
        print("⚠️ 생성된 영상이 없습니다.")
        print()


if __name__ == "__main__":
    main()

