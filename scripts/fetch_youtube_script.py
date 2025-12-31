#!/usr/bin/env python3
"""
유튜브 영상에서 자막을 가져와서 합치는 스크립트

일당백 채널의 유튜브 영상(Part 1, Part 2)에서 자막을 가져와서
하나의 텍스트 파일로 합쳐서 저장합니다.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.file_utils import get_standard_safe_title
from src.utils.logger import setup_logger

# 로거 설정
logger = setup_logger(__name__)

try:
    from youtube_transcript_api import (
        YouTubeTranscriptApi,
        TranscriptsDisabled,
        NoTranscriptFound,
        VideoUnavailable
    )
except ImportError:
    logger.error("❌ youtube-transcript-api 패키지가 설치되지 않았습니다.")
    logger.error("다음 명령어로 설치해주세요: pip install youtube-transcript-api")
    sys.exit(1)


def extract_video_id(url: str) -> Optional[str]:
    """
    유튜브 URL에서 비디오 ID 추출
    
    Args:
        url: 유튜브 URL (다양한 형식 지원)
        
    Returns:
        비디오 ID 또는 None
    """
    import re
    
    # 다양한 유튜브 URL 패턴 지원
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # URL이 아닌 경우 비디오 ID로 간주
    if len(url) == 11 and url.replace('-', '').replace('_', '').isalnum():
        return url
    
    return None


def fetch_transcript(video_id: str, languages: list = ['ko', 'en']) -> Optional[list]:
    """
    유튜브 영상에서 자막 가져오기
    
    Args:
        video_id: 유튜브 비디오 ID
        languages: 우선순위 언어 리스트 (기본값: ['ko', 'en'])
        
    Returns:
        자막 리스트 또는 None
    """
    try:
        logger.info(f"📹 비디오 ID {video_id}에서 자막 가져오는 중...")
        
        # YouTubeTranscriptApi 인스턴스 생성
        yt_api = YouTubeTranscriptApi()
        
        # 자동으로 사용 가능한 자막 찾기
        transcript_list = yt_api.list(video_id)
        
        # 우선순위에 따라 자막 찾기
        transcript = None
        for lang in languages:
            try:
                transcript = transcript_list.find_transcript([lang])
                logger.info(f"✅ {lang} 자막을 찾았습니다.")
                break
            except:
                continue
        
        # 자동 번역 시도 (한국어가 없으면 영어 자막을 한국어로 번역)
        if transcript is None:
            try:
                # 먼저 영어 자막을 찾고 한국어로 번역
                en_transcript = transcript_list.find_transcript(['en'])
                transcript = en_transcript.translate('ko')
                logger.info("✅ 영어 자막을 한국어로 번역했습니다.")
            except:
                pass
        
        # 영어 자막 시도
        if transcript is None:
            try:
                transcript = transcript_list.find_transcript(['en'])
                logger.info("✅ 영어 자막을 찾았습니다.")
            except:
                pass
        
        if transcript is None:
            logger.error(f"❌ 사용 가능한 자막을 찾을 수 없습니다.")
            return None
        
        # 자막 데이터 가져오기
        transcript_data = transcript.fetch()
        logger.info(f"✅ 총 {len(transcript_data)}개의 자막 세그먼트를 가져왔습니다.")
        
        return transcript_data
        
    except TranscriptsDisabled:
        logger.error(f"❌ 이 영상은 자막이 비활성화되어 있습니다.")
        return None
    except NoTranscriptFound:
        logger.error(f"❌ 이 영상에서 자막을 찾을 수 없습니다.")
        return None
    except VideoUnavailable:
        logger.error(f"❌ 이 영상은 사용할 수 없거나 삭제되었습니다.")
        return None
    except Exception as e:
        logger.error(f"❌ 자막을 가져오는 중 오류 발생: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return None


def format_transcript(transcript_data: list) -> str:
    """
    자막 데이터를 텍스트로 포맷팅
    
    Args:
        transcript_data: 자막 데이터 리스트 (FetchedTranscriptSnippet 객체 리스트)
        
    Returns:
        포맷팅된 텍스트
    """
    text_lines = []
    for entry in transcript_data:
        # FetchedTranscriptSnippet 객체는 text 속성을 가짐
        if hasattr(entry, 'text'):
            text = entry.text.strip()
        elif isinstance(entry, dict):
            text = entry.get('text', '').strip()
        else:
            text = str(entry).strip()
        
        if text:
            text_lines.append(text)
    
    return ' '.join(text_lines)


def save_combined_script(
    part1_text: str,
    part2_text: str,
    book_title: str,
    output_dir: Path
) -> Path:
    """
    두 파트의 자막을 합쳐서 파일로 저장
    
    Args:
        part1_text: Part 1 자막 텍스트
        part2_text: Part 2 자막 텍스트
        book_title: 책 제목
        output_dir: 출력 디렉토리
        
    Returns:
        저장된 파일 경로
    """
    # 출력 디렉토리 생성
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 안전한 파일명 생성
    safe_title = get_standard_safe_title(book_title)
    output_file = output_dir / f"{safe_title}_full_script.txt"
    
    # 텍스트 합치기
    combined_text = f"""Part 1: 작가와 배경

{part1_text}


Part 2: 소설 줄거리

{part2_text}
"""
    
    # 파일 저장
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(combined_text)
        logger.info(f"✅ 자막이 저장되었습니다: {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"❌ 파일 저장 중 오류 발생: {e}")
        raise


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='유튜브 영상(Part 1, Part 2)에서 자막을 가져와서 합치는 스크립트',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python scripts/fetch_youtube_script.py \\
    --url1 "https://www.youtube.com/watch?v=VIDEO_ID_1" \\
    --url2 "https://www.youtube.com/watch?v=VIDEO_ID_2" \\
    --book-title "노인과 바다"
        """
    )
    
    parser.add_argument(
        '--url1',
        type=str,
        required=True,
        help='Part 1 유튜브 URL 또는 비디오 ID'
    )
    
    parser.add_argument(
        '--url2',
        type=str,
        required=True,
        help='Part 2 유튜브 URL 또는 비디오 ID'
    )
    
    parser.add_argument(
        '--book-title',
        type=str,
        required=True,
        help='책 제목 (파일명 생성에 사용)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/source',
        help='출력 디렉토리 (기본값: data/source)'
    )
    
    args = parser.parse_args()
    
    # 비디오 ID 추출
    video_id1 = extract_video_id(args.url1)
    video_id2 = extract_video_id(args.url2)
    
    if not video_id1:
        logger.error(f"❌ Part 1 URL에서 비디오 ID를 추출할 수 없습니다: {args.url1}")
        sys.exit(1)
    
    if not video_id2:
        logger.error(f"❌ Part 2 URL에서 비디오 ID를 추출할 수 없습니다: {args.url2}")
        sys.exit(1)
    
    logger.info(f"📖 책 제목: {args.book_title}")
    logger.info(f"📹 Part 1 비디오 ID: {video_id1}")
    logger.info(f"📹 Part 2 비디오 ID: {video_id2}")
    logger.info("")
    
    # Part 1 자막 가져오기
    logger.info("=" * 60)
    logger.info("Part 1 자막 가져오는 중...")
    logger.info("=" * 60)
    transcript1 = fetch_transcript(video_id1)
    
    if not transcript1:
        logger.error("❌ Part 1 자막을 가져올 수 없습니다.")
        sys.exit(1)
    
    part1_text = format_transcript(transcript1)
    logger.info(f"✅ Part 1 자막 길이: {len(part1_text)} 문자")
    logger.info("")
    
    # Part 2 자막 가져오기
    logger.info("=" * 60)
    logger.info("Part 2 자막 가져오는 중...")
    logger.info("=" * 60)
    transcript2 = fetch_transcript(video_id2)
    
    if not transcript2:
        logger.error("❌ Part 2 자막을 가져올 수 없습니다.")
        sys.exit(1)
    
    part2_text = format_transcript(transcript2)
    logger.info(f"✅ Part 2 자막 길이: {len(part2_text)} 문자")
    logger.info("")
    
    # 합쳐서 저장
    logger.info("=" * 60)
    logger.info("자막 합치기 및 저장 중...")
    logger.info("=" * 60)
    output_dir = Path(args.output_dir)
    output_file = save_combined_script(part1_text, part2_text, args.book_title, output_dir)
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ 작업 완료!")
    logger.info("=" * 60)
    logger.info(f"📄 저장된 파일: {output_file}")
    logger.info(f"📊 Part 1 길이: {len(part1_text)} 문자")
    logger.info(f"📊 Part 2 길이: {len(part2_text)} 문자")
    logger.info(f"📊 전체 길이: {len(part1_text) + len(part2_text)} 문자")


if __name__ == '__main__':
    main()

