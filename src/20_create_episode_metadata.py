#!/usr/bin/env python3
"""
일당백 에피소드 영상 메타데이터 생성 스크립트

Part 1과 Part 2로 구성된 에피소드 영상의 메타데이터를 생성합니다.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Dict

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.file_utils import get_standard_safe_title
from src.utils.logger import setup_logger
from utils.translations import translate_book_title, translate_author_name, translate_book_title_to_korean, is_english_title

# 로거 설정
logger = setup_logger(__name__)


def generate_episode_title(book_title: str, language: str = "ko") -> str:
    """
    에피소드 영상 제목 생성
    
    Args:
        book_title: 책 제목
        language: 언어 ('ko' 또는 'en')
        
    Returns:
        생성된 제목
    """
    # 책 제목 번역
    if language == "ko":
        if is_english_title(book_title):
            ko_title = translate_book_title_to_korean(book_title)
        else:
            ko_title = book_title
        return f"[일당백] {ko_title} 완전정복 | 작가와 배경부터 소설 줄거리까지"
    else:
        if not is_english_title(book_title):
            en_title = translate_book_title(book_title)
        else:
            en_title = book_title
        return f"Complete Guide to {en_title} | From Author & Background to Full Story"


def generate_episode_description(book_title: str, language: str = "ko", video_duration: Optional[float] = None) -> str:
    """
    에피소드 영상 설명 생성
    
    Args:
        book_title: 책 제목
        language: 언어 ('ko' 또는 'en')
        video_duration: 영상 길이 (초, 선택사항)
        
    Returns:
        생성된 설명
    """
    # 책 제목 번역
    if language == "ko":
        if is_english_title(book_title):
            ko_title = translate_book_title_to_korean(book_title)
            en_title = book_title
        else:
            ko_title = book_title
            en_title = translate_book_title(book_title)
        
        description = f"""📚 {ko_title} ({en_title}) 완전정복

이 영상은 일당백 채널의 두 편의 영상을 하나로 합친 완전판입니다.

📖 영상 구성:
• Part 1: 작가와 배경 - 작가의 생애와 작품 배경
• Part 2: 소설 줄거리 - 전체 스토리와 주요 인물

🎯 이 영상에서 배울 수 있는 것:
✓ 작가의 생애와 작품 세계
✓ 작품의 시대적 배경과 의미
✓ 소설의 전체 줄거리와 구조
✓ 주요 인물의 성격과 관계
✓ 작품의 핵심 메시지와 주제

📌 타임스탬프:
"""
        
        if video_duration:
            part1_end = video_duration * 0.4  # 대략 Part 1이 40% 정도
            minutes1 = int(part1_end // 60)
            seconds1 = int(part1_end % 60)
            minutes2 = int(video_duration // 60)
            seconds2 = int(video_duration % 60)
            description += f"0:00 - Part 1: 작가와 배경\n"
            description += f"{minutes1}:{seconds1:02d} - Part 2: 소설 줄거리\n\n"
        
        description += f"""💡 일당백 채널에서 더 많은 작품을 만나보세요!

🔔 구독과 좋아요는 다음 영상 제작에 큰 힘이 됩니다!
💬 댓글로 여러분의 생각을 공유해주세요!

#일당백 #{ko_title.replace(' ', '')} #책리뷰 #문학 #소설 #작가 #문학작품"""
        
    else:  # en
        if not is_english_title(book_title):
            en_title = translate_book_title(book_title)
        else:
            en_title = book_title
        
        description = f"""📚 Complete Guide to {en_title}

This video combines two episodes from 1DANG100 channel into one complete guide.

📖 Video Structure:
• Part 1: Author & Background - Author's life and work context
• Part 2: Novel Summary - Full story and main characters

🎯 What You'll Learn:
✓ Author's life and literary world
✓ Historical background and significance
✓ Complete story structure and plot
✓ Main characters' personalities and relationships
✓ Core messages and themes

📌 Timestamps:
"""
        
        if video_duration:
            part1_end = video_duration * 0.4
            minutes1 = int(part1_end // 60)
            seconds1 = int(part1_end % 60)
            minutes2 = int(video_duration // 60)
            seconds2 = int(video_duration % 60)
            description += f"0:00 - Part 1: Author & Background\n"
            description += f"{minutes1}:{seconds1:02d} - Part 2: Novel Summary\n\n"
        
        description += f"""💡 Check out 1DANG100 channel for more literary works!

🔔 Subscribe and like to support future videos!
💬 Share your thoughts in the comments!

#{en_title.replace(' ', '')} #BookReview #Literature #Novel #Author #LiteraryWork"""
    
    return description


def generate_episode_tags(book_title: str, language: str = "ko") -> list:
    """
    에피소드 영상 태그 생성 (YouTube 최대치: 500자, 태그당 30자)
    
    Args:
        book_title: 책 제목
        language: 언어 ('ko' 또는 'en')
        
    Returns:
        생성된 태그 리스트
    """
    from src.utils.file_utils import load_book_info
    
    # 책 정보 로드 시도
    book_info = None
    try:
        safe_title = get_standard_safe_title(book_title)
        book_info = load_book_info(safe_title)
    except:
        pass
    
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
                f"{author_ko}소설",
                f"{author_en}",
                f"{author_en}Book",
            ])
        
        # 기본 문학 태그
        base_tags = [
            # 리뷰/분석
            "책리뷰",
            "책추천",
            "문학리뷰",
            "소설리뷰",
            "문학분석",
            "소설분석",
            "작품분석",
            "문학해석",
            "소설해석",
            "문학비평",
            "문학강의",
            "문학특강",
            "소설강의",
            "문학수업",
            
            # 장르
            "문학",
            "소설",
            "문학작품",
            "고전문학",
            "현대문학",
            "한국문학",
            "세계문학",
            "외국문학",
            "번역문학",
            "문학고전",
            "명작소설",
            "추천소설",
            "베스트셀러",
            
            # 독서 관련
            "독서",
            "독서법",
            "독서습관",
            "독서모임",
            "책읽기",
            "책추천",
            "북리뷰",
            "북튜버",
            "북크리에이터",
            "책유튜버",
            "독서유튜버",
            "문학유튜버",
            
            # 학습/교육
            "문학공부",
            "문학공부법",
            "문학독해",
            "문학이해",
            "문학감상",
            "문학수업",
            "문학특강",
            "문학강좌",
            "문학교육",
            
            # 콘텐츠 유형
            "작가와배경",
            "소설줄거리",
            "작품줄거리",
            "스토리리뷰",
            "인물분석",
            "주제분석",
            "배경분석",
            "시대배경",
            "작품배경",
            
            # 키워드
            "완전정복",
            "완벽정리",
            "총정리",
            "핵심정리",
            "요약",
            "해설",
            "강의",
            "특강",
            "분석",
            "리뷰",
            "추천",
        ]
        
        tags.extend(base_tags)
        
    else:  # en
        if not is_english_title(book_title):
            en_title = translate_book_title(book_title)
        else:
            en_title = book_title
        
        # 작가 이름 추출
        author_name = None
        if book_info and 'author' in book_info:
            author_name = book_info['author']
        
        # 책 제목에서 핵심 키워드 추출 (태그용)
        import re
        # 영어 제목에서 핵심 키워드 추출
        en_title_clean = re.sub(r'[:\-\(\)\[\]「」]', ' ', en_title)
        en_keywords = [word.strip() for word in en_title_clean.split() if len(word.strip()) > 1]
        en_main_keyword = ' '.join(en_keywords[:2]) if len(en_keywords) >= 2 else ' '.join(en_keywords)
        en_main_keyword = en_main_keyword[:20]  # 최대 20자로 제한
        
        tags = [
            # Channel & Series
            "1DANG100",
            "1DANG100BookReview",
            "1DANG100Literature",
            
            # Book Title (핵심 키워드만)
            en_main_keyword if en_main_keyword else en_title[:20],
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
        
        # Add author name if available
        if author_name:
            if is_english_title(author_name):
                author_en = author_name
            else:
                author_en = translate_author_name(author_name)
            
            tags.extend([
                f"{author_en}",
                f"{author_en}Book",
                f"{author_en}Novel",
            ])
        
        # Base literature tags
        base_tags = [
            # Review/Analysis
            "BookReview",
            "BookRecommendation",
            "LiteratureReview",
            "NovelReview",
            "LiteraryAnalysis",
            "NovelAnalysis",
            "WorkAnalysis",
            "LiteraryInterpretation",
            "NovelInterpretation",
            "LiteraryCriticism",
            "LiteratureLecture",
            "NovelLecture",
            "LiteratureClass",
            
            # Genre
            "Literature",
            "Novel",
            "LiteraryWork",
            "ClassicLiterature",
            "ModernLiterature",
            "KoreanLiterature",
            "WorldLiterature",
            "ForeignLiterature",
            "TranslatedLiterature",
            "LiteraryClassic",
            "Masterpiece",
            "Bestseller",
            
            # Reading related
            "Reading",
            "ReadingMethod",
            "ReadingHabit",
            "BookClub",
            "BookReading",
            "BookTube",
            "BookCreator",
            "BookYouTuber",
            "ReadingYouTuber",
            "LiteratureYouTuber",
            
            # Learning/Education
            "LiteratureStudy",
            "LiteratureStudyMethod",
            "LiteraryComprehension",
            "LiteraryAppreciation",
            "LiteratureClass",
            "LiteratureLecture",
            "LiteratureCourse",
            "LiteratureEducation",
            
            # Content Type
            "AuthorAndBackground",
            "NovelSummary",
            "WorkSummary",
            "StoryReview",
            "CharacterAnalysis",
            "ThemeAnalysis",
            "BackgroundAnalysis",
            "HistoricalBackground",
            "WorkBackground",
            
            # Keywords
            "CompleteGuide",
            "PerfectSummary",
            "FullSummary",
            "KeySummary",
            "Summary",
            "Explanation",
            "Lecture",
            "Analysis",
            "Review",
            "Recommendation",
        ]
        
        tags.extend(base_tags)
    
    # 태그 정리: 30자 제한 및 중복 제거
    cleaned_tags = []
    seen = set()
    for tag in tags:
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
    
    # 메타데이터 생성
    title = generate_episode_title(book_title, language)
    description = generate_episode_description(book_title, language, video_duration)
    tags = generate_episode_tags(book_title, language)
    
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

