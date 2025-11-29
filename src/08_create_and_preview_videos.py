"""
영상 생성 및 메타데이터 미리보기 스크립트
- 한글/영문 오디오로 각각 영상 생성
- 메타데이터(제목, 설명, 태그) 생성 및 미리보기
- 썸네일 자동 생성 (선택사항)
- 업로드 전 점검 가능
"""

import sys
import json
from pathlib import Path
from typing import Optional, Dict, Tuple

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
from utils.translations import translate_book_title, translate_author_name, get_book_alternative_title, translate_book_title_to_korean, is_english_title, translate_author_name_to_korean
from utils.file_utils import safe_title, load_book_info

def generate_title(book_title: str, lang: str = "both") -> str:
    """영상 제목 생성 (두 언어 포함, 언어 표시 포함, 대체 제목 포함)"""
    # book_title이 영어인지 한글인지 판단
    if is_english_title(book_title):
        # 영어 제목이 들어온 경우: 한글 제목으로 변환
        ko_title = translate_book_title_to_korean(book_title)
        en_title = book_title  # 이미 영어
    else:
        # 한글 제목이 들어온 경우: 영어 제목으로 변환
        ko_title = book_title  # 이미 한글
        en_title = translate_book_title(book_title)
    
    alt_titles = get_book_alternative_title(ko_title)  # 한글 제목 기준으로 대체 제목 찾기
    
    if lang == "ko":
        # 한글 먼저, 영어 나중
        # 한글 부분: [한국어], 영어 부분: [Korean]
        if alt_titles.get("ko"):
            # 대체 제목 포함: "노르웨이의 숲 (상실의 시대)"
            main_title = f"{ko_title} ({alt_titles['ko']})"
        else:
            main_title = ko_title
        return f"[한국어] {main_title} 책 리뷰 | [Korean] {en_title} Book Review | 일당백 스타일"
    elif lang == "en":
        # 영어 먼저, 한글 나중
        # 영어 부분: [English], 한글 부분: [영어]
        if alt_titles.get("en"):
            # 대체 제목 포함: "Norwegian Wood (The Age of Loss)"
            en_main_title = f"{en_title} ({alt_titles['en']})"
        else:
            en_main_title = en_title
        
        if alt_titles.get("ko"):
            # 한글 부분에도 대체 제목 포함
            ko_main_title = f"{ko_title} ({alt_titles['ko']})"
        else:
            ko_main_title = ko_title
        
        return f"[English] {en_main_title} Book Review | [영어] {ko_main_title} 책 리뷰 | Auto-Generated"
    else:
        return f"{ko_title} 책 리뷰 | {en_title} Book Review | 일당백 스타일"

def generate_description(book_info: Optional[Dict] = None, lang: str = "both", book_title: str = None) -> str:
    """영상 설명 생성 (두 언어 포함)"""
    if lang == "ko":
        # 한글 먼저, 영어 나중
        return _generate_description_ko(book_info, book_title)
    elif lang == "en":
        # 영어 먼저, 한글 나중
        return _generate_description_en_with_ko(book_info, book_title)
    else:
        ko_desc = _generate_description_ko(book_info, book_title)
        en_desc = _generate_description_en_with_ko(book_info, book_title)
        return f"{ko_desc}\n\n{'='*60}\n\n{en_desc}"

def _generate_description_ko(book_info: Optional[Dict] = None, book_title: str = None) -> str:
    """한글 설명 생성 (한글 먼저, 영어 나중)"""
    # 한글 부분
    ko_desc = """📚 책 리뷰 영상

이 영상은 NotebookLM과 AI를 활용하여 자동으로 생성되었습니다.

📝 영상 구성:
• GPT로 생성한 소설 요약 (약 5분)
• NotebookLM으로 생성한 오디오 리뷰

"""
    if book_info:
        if book_info.get('description'):
            ko_desc += f"📖 책 소개:\n{book_info['description'][:500]}...\n\n"
        if book_info.get('authors'):
            ko_desc += f"✍️ 작가: {', '.join(book_info['authors'])}\n"
        if book_info.get('publishedDate'):
            ko_desc += f"📅 출간일: {book_info['publishedDate']}\n"
    
    ko_desc += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔔 구독과 좋아요는 영상 제작에 큰 힘이 됩니다!
💬 댓글로 여러분의 생각을 공유해주세요.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#책리뷰 #독서 #북튜버 #책추천 #BookReview #Reading
"""
    
    # 영어 부분
    en_desc = """📚 Book Review Video

This video was automatically generated using NotebookLM and AI.

📝 Video Content:
• Book summary generated by GPT (approximately 5 minutes)
• Audio review generated by NotebookLM

"""
    if book_info:
        # 영어 책 소개 추가
        if book_title:
            en_book_desc = get_english_book_description(book_title)
            if en_book_desc:
                en_desc += f"📖 Book Introduction:\n{en_book_desc[:500]}...\n\n"
        
        if book_info.get('authors'):
            authors_en = [translate_author_name(author) for author in book_info['authors']]
            en_desc += f"✍️ Author: {', '.join(authors_en)}\n"
        if book_info.get('publishedDate'):
            en_desc += f"📅 Published: {book_info['publishedDate']}\n"
    
    en_desc += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔔 Subscribe and like to support video creation!
💬 Share your thoughts in the comments.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#BookReview #Reading #BookTube #BookRecommendation #책리뷰 #독서
"""
    
    # 한글 먼저, 영어 나중
    return f"{ko_desc}\n\n{'='*60}\n\n{en_desc}"

# translate_author_name은 utils.translations에서 import

def get_english_book_description(book_title: str) -> str:
    """책 제목에 따른 영어 설명 반환"""
    descriptions = {
        "노르웨이의 숲": """Norwegian Wood is a brilliant diamond in Haruki Murakami's world - the book you must read first to meet Murakami Haruki! This novel, which resonates with the sensitive and delicate emotions of youth, has been loved as an eternal must-read. Set in late 1960s Japan during the period of rapid economic growth, this novel depicts the fragile relationship between individuals and society, and the vivid moments of youth that seem within reach. Translated and introduced in more than 36 countries, it caused a worldwide 'Murakami boom' and widely publicized Murakami Haruki's literary achievements, making it a representative work of modern Japanese literature.""",
        "노르웨이의_숲": """Norwegian Wood is a brilliant diamond in Haruki Murakami's world - the book you must read first to meet Murakami Haruki! This novel, which resonates with the sensitive and delicate emotions of youth, has been loved as an eternal must-read. Set in late 1960s Japan during the period of rapid economic growth, this novel depicts the fragile relationship between individuals and society, and the vivid moments of youth that seem within reach. Translated and introduced in more than 36 countries, it caused a worldwide 'Murakami boom' and widely publicized Murakami Haruki's literary achievements, making it a representative work of modern Japanese literature.""",
    }
    
    return descriptions.get(book_title, "")

def _generate_description_en(book_info: Optional[Dict] = None, book_title: str = None, include_header: bool = True) -> str:
    """영문 설명 생성"""
    description = ""
    
    if include_header:
        description = """📚 Book Review Video

This video was automatically generated using NotebookLM and AI.

📝 Video Content:
• Book summary generated by GPT (approximately 5 minutes)
• Audio review generated by NotebookLM

"""
    
    if book_info:
        # 영어 설명 사용
        en_desc = ""
        if book_title:
            en_desc = get_english_book_description(book_title)
        
        if en_desc:
            description += f"📖 Book Introduction:\n{en_desc[:500]}...\n\n"
        elif book_info.get('description'):
            # 영어 설명이 없으면 기본 영어 설명 사용
            description += f"📖 Book Introduction:\nA book review video about this literary work.\n\n"
        
        if book_info.get('authors'):
            # 작가 이름 영어로 변환
            authors_en = [translate_author_name(author) for author in book_info['authors']]
            description += f"✍️ Author: {', '.join(authors_en)}\n"
        if book_info.get('publishedDate'):
            description += f"📅 Published: {book_info['publishedDate']}\n"
    
    description += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔔 Subscribe and like to support video creation!
💬 Share your thoughts in the comments.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#BookReview #Reading #BookTube #BookRecommendation #책리뷰 #독서
"""
    return description

def _generate_description_en_with_ko(book_info: Optional[Dict] = None, book_title: str = None) -> str:
    """영문 설명 생성 (영어 먼저, 한글 나중)"""
    # 영어 부분
    en_desc = _generate_description_en(book_info, book_title, include_header=True)
    
    # 한글 부분
    ko_desc = """📚 책 리뷰 영상

이 영상은 NotebookLM과 AI를 활용하여 자동으로 생성되었습니다.

📝 영상 구성:
• GPT로 생성한 소설 요약 (약 5분)
• NotebookLM으로 생성한 오디오 리뷰

"""
    if book_info:
        if book_info.get('description'):
            ko_desc += f"📖 책 소개:\n{book_info['description'][:500]}...\n\n"
        if book_info.get('authors'):
            # 작가 이름이 영어인지 한글인지 판단하여 한글로 변환
            authors_ko = []
            for author in book_info['authors']:
                if is_english_title(author):
                    # 영어 작가 이름인 경우 한글로 변환
                    ko_author = translate_author_name_to_korean(author)
                    authors_ko.append(ko_author)
                else:
                    authors_ko.append(author)
            ko_desc += f"✍️ 작가: {', '.join(authors_ko)}\n"
        if book_info.get('publishedDate'):
            ko_desc += f"📅 출간일: {book_info['publishedDate']}\n"
    
    ko_desc += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔔 구독과 좋아요는 영상 제작에 큰 힘이 됩니다!
💬 댓글로 여러분의 생각을 공유해주세요.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#책리뷰 #독서 #북튜버 #책추천 #BookReview #Reading
"""
    
    # 영어 먼저, 한글 나중
    return f"{en_desc}\n\n{'='*60}\n\n{ko_desc}"

def generate_tags(book_title: str = None, book_info: Optional[Dict] = None, lang: str = "both") -> list:
    """태그 생성 (책 정보 활용, 두 언어 포함)"""
    # 기본 태그
    ko_base_tags = ['책리뷰', '독서', '북튜버', '책추천', '일당백', '독서법', '책읽기', '리뷰영상']
    en_base_tags = ['BookReview', 'Reading', 'BookTube', 'BookRecommendation', 'ReadingTips', 'Books', 'ReviewVideo']
    
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
    
    # 태그 결합 (중복 제거)
    # 기관 태그를 기본 태그와 책 태그 사이에 추가 (우선순위 고려)
    ko_tags = list(dict.fromkeys(ko_base_tags + institution_tags_ko + ko_book_tags))  # 순서 유지하며 중복 제거
    en_tags = list(dict.fromkeys(en_base_tags + institution_tags_en + en_book_tags))
    
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


def save_metadata(video_path: Path, title: str, description: str, tags: list, lang: str, book_info: Optional[Dict] = None, thumbnail_path: Optional[str] = None):
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
    
    # 썸네일 경로도 메타데이터에 포함
    if thumbnail_path:
        metadata['thumbnail_path'] = thumbnail_path
    
    metadata_path = video_path.with_suffix('.metadata.json')
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"💾 메타데이터 저장: {metadata_path.name}")
    return metadata_path


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='영상 생성 및 메타데이터 미리보기')
    parser.add_argument('--book-title', type=str, default="노르웨이의 숲", help='책 제목')
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
        
        # 책 정보 로드
        book_info = load_book_info(args.book_title)
        if book_info:
            print(f"📚 책 정보 로드 완료: {book_info.get('title', args.book_title)}")
        print()
        
        safe_title_str = safe_title(args.book_title)
        
        # 한글 메타데이터 생성
        video_path_ko = Path(f"output/{safe_title_str}_review_with_summary_ko.mp4")
        thumbnail_path_ko = Path(f"output/{safe_title_str}_thumbnail_ko.jpg")
        
        if thumbnail_path_ko.exists():
            print("📋 한글 메타데이터 생성 중...")
            title_ko = generate_title(args.book_title, lang='ko')
            description_ko = generate_description(book_info, lang='ko', book_title=args.book_title)
            tags_ko = generate_tags(book_title=args.book_title, book_info=book_info, lang='ko')
            
            save_metadata(
                video_path_ko,
                title_ko,
                description_ko,
                tags_ko,
                'ko',
                book_info,
                str(thumbnail_path_ko) if thumbnail_path_ko.exists() else None
            )
        else:
            print(f"⚠️ 한글 썸네일을 찾을 수 없습니다: {thumbnail_path_ko}")
        
        # 영문 메타데이터 생성
        video_path_en = Path(f"output/{safe_title_str}_review_with_summary_en.mp4")
        thumbnail_path_en = Path(f"output/{safe_title_str}_thumbnail_en.jpg")
        
        if thumbnail_path_en.exists():
            print("\n📋 영문 메타데이터 생성 중...")
            title_en = generate_title(args.book_title, lang='en')
            description_en = generate_description(book_info, lang='en', book_title=args.book_title)
            tags_en = generate_tags(book_title=args.book_title, book_info=book_info, lang='en')
            
            save_metadata(
                video_path_en,
                title_en,
                description_en,
                tags_en,
                'en',
                book_info,
                str(thumbnail_path_en) if thumbnail_path_en.exists() else None
            )
        else:
            print(f"⚠️ 영문 썸네일을 찾을 수 없습니다: {thumbnail_path_en}")
        
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
    
    # 책 정보 로드
    book_info = load_book_info(args.book_title)
    if book_info:
        print(f"📚 책 정보 로드 완료: {book_info.get('title', args.book_title)}")
        print()
    
    # 이미지 디렉토리 설정
    safe_title_str = safe_title(args.book_title)
    if args.image_dir is None:
        args.image_dir = f"assets/images/{safe_title_str}"
    
    videos_created = []
    
    # 한글 영상 제작
    if korean_audio:
        print("🇰🇷 한글 영상")
        print("-" * 60)
        print(f"   오디오: {korean_audio.name}")
        print()
        
        output_path = Path(f"output/{safe_title_str}_review_ko.mp4")
        
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
        title = generate_title(args.book_title, lang="ko")
        description = generate_description(book_info, lang="ko", book_title=args.book_title)
        tags = generate_tags(book_title=args.book_title, book_info=book_info, lang="ko")
        
        # 메타데이터 미리보기
        preview_metadata(title, description, tags, "ko")
        
        # 썸네일 생성 (선택사항)
        thumbnail_path = None
        if THUMBNAIL_AVAILABLE and not args.skip_thumbnail:
            try:
                print("🖼️ 썸네일 생성 중...")
                generator = ThumbnailGenerator(use_dalle=args.use_dalle_thumbnail)
                
                # 배경 이미지 찾기
                background_image = None
                if args.image_dir:
                    mood_images = sorted(Path(args.image_dir).glob("mood_*.jpg"))
                    if mood_images:
                        background_image = str(mood_images[0])
                
                thumbnail_path = generator.generate_thumbnail(
                    book_title=args.book_title,
                    author=', '.join(book_info.get('authors', [])) if book_info else '',
                    lang="ko",
                    background_image_path=background_image,
                    output_path=str(output_path.parent / f"{output_path.stem}_thumbnail_ko.jpg")
                )
                print()
            except Exception as e:
                print(f"⚠️ 썸네일 생성 실패: {e}")
                print()
        
        # 메타데이터 저장
        if output_path.exists():
            metadata_path = save_metadata(output_path, title, description, tags, "ko", book_info, thumbnail_path)
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
        
        output_path = Path(f"output/{safe_title_str}_review_en.mp4")
        
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
        title = generate_title(args.book_title, lang="en")
        description = generate_description(book_info, lang="en", book_title=args.book_title)
        tags = generate_tags(book_title=args.book_title, book_info=book_info, lang="en")
        
        # 메타데이터 미리보기
        preview_metadata(title, description, tags, "en")
        
        # 썸네일 생성 (선택사항)
        thumbnail_path = None
        if THUMBNAIL_AVAILABLE and not args.skip_thumbnail:
            try:
                print("🖼️ 썸네일 생성 중...")
                generator = ThumbnailGenerator(use_dalle=args.use_dalle_thumbnail)
                
                # 배경 이미지 찾기
                background_image = None
                if args.image_dir:
                    mood_images = sorted(Path(args.image_dir).glob("mood_*.jpg"))
                    if mood_images:
                        background_image = str(mood_images[0])
                
                # 영어 제목으로 변환
                en_title = translate_book_title(args.book_title)
                thumbnail_path = generator.generate_thumbnail(
                    book_title=en_title,
                    author=', '.join(book_info.get('authors', [])) if book_info else '',
                    lang="en",
                    background_image_path=background_image,
                    output_path=str(output_path.parent / f"{output_path.stem}_thumbnail_en.jpg")
                )
                print()
            except Exception as e:
                print(f"⚠️ 썸네일 생성 실패: {e}")
                print()
        
        # 메타데이터 저장
        if output_path.exists():
            metadata_path = save_metadata(output_path, title, description, tags, "en", book_info, thumbnail_path)
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

