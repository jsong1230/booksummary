#!/usr/bin/env python3
"""
Input 폴더의 비디오 파일들을 연결하여 일당백 스타일 영상 생성

Input 폴더에서 part1_video_kr.mp4, part2_video_kr.mp4 등을 찾아서 연결합니다.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.file_utils import get_standard_safe_title
from src.utils.logger import setup_logger

# 로거 설정
logger = setup_logger(__name__)

try:
    from moviepy.editor import VideoFileClip, concatenate_videoclips
    MOVIEPY_AVAILABLE = True
except ImportError as e:
    logger.error(f"❌ MoviePy import 오류: {e}")
    logger.error("pip install moviepy")
    sys.exit(1)


def find_video_files(input_dir: Path, language: str = "kr") -> List[Path]:
    """
    Input 폴더에서 비디오 파일들을 순서대로 찾기
    
    Args:
        input_dir: Input 폴더 경로
        language: 언어 ('kr' 또는 'en')
        
    Returns:
        찾은 비디오 파일 경로 리스트 (순서대로)
    """
    video_files = []
    
    # part1, part2, part3... 순서로 찾기
    part_num = 1
    while True:
        video_file = input_dir / f"part{part_num}_video_{language}.mp4"
        if video_file.exists():
            video_files.append(video_file)
            logger.info(f"✅ Part {part_num} 비디오 발견: {video_file.name}")
            part_num += 1
        else:
            # part{part_num}_video_{language}.mp4가 없으면 중단
            break
    
    return video_files


def concatenate_videos_from_input(
    book_title: str,
    language: str = "kr",
    output_path: Optional[str] = None,
    infographic_duration: float = 10.0
) -> str:
    """
    Input 폴더의 비디오 파일들을 연결하여 전체 에피소드 영상 생성
    
    Args:
        book_title: 책 제목
        language: 언어 ('kr' 또는 'en')
        output_path: 출력 파일 경로 (None이면 자동 생성)
        infographic_duration: 인포그래픽 표시 시간 (초)
        
    Returns:
        생성된 영상 파일 경로
    """
    # 안전한 파일명 생성
    safe_title = get_standard_safe_title(book_title)
    
    # Input 폴더 경로
    input_dir = Path("input")
    
    if not input_dir.exists():
        raise FileNotFoundError(f"Input 폴더를 찾을 수 없습니다: {input_dir}")
    
    logger.info("=" * 60)
    logger.info("🎬 일당백 스타일 영상 생성 시작")
    logger.info("=" * 60)
    logger.info(f"📖 책 제목: {book_title}")
    logger.info(f"🌐 언어: {language.upper()}")
    logger.info(f"📁 입력 디렉토리: {input_dir}")
    logger.info("")
    
    # 비디오 파일 찾기
    video_files = find_video_files(input_dir, language)
    
    if not video_files:
        raise FileNotFoundError(f"Input 폴더에서 비디오 파일을 찾을 수 없습니다: {input_dir}")
    
    logger.info(f"📹 총 {len(video_files)}개의 비디오 파일 발견")
    logger.info("")
    
    # 해상도 설정
    resolution = (1920, 1080)
    fps = 30
    
    video_clips = []
    
    # 각 비디오 파일 로드 및 처리
    for i, video_file in enumerate(video_files, 1):
        logger.info(f"🎥 Part {i} 영상 로드 중...")
        logger.info(f"   파일: {video_file.name}")
        
        clip = VideoFileClip(str(video_file))
        
        # 해상도 통일
        if clip.size != resolution:
            logger.info(f"   🔄 리사이즈 중: {clip.size} -> {resolution}")
            from moviepy.video.fx.all import resize
            clip = resize(clip, newsize=resolution)
        
        # 프레임레이트 통일
        if clip.fps != fps:
            logger.info(f"   🔄 프레임레이트 조정 중: {clip.fps}fps -> {fps}fps")
            clip = clip.set_fps(fps)
        
        logger.info(f"   ✅ 완료: {clip.duration:.2f}초 ({clip.duration/60:.2f}분)")
        logger.info("")
        
        video_clips.append(clip)
        
        # 인포그래픽이 있으면 추가
        info_file = input_dir / f"part{i}_info_{language}.png"
        if info_file.exists():
            logger.info(f"📊 Part {i} 인포그래픽 추가 중...")
            logger.info(f"   파일: {info_file.name}")
            logger.info(f"   효과: 정적 이미지 ({infographic_duration}초)")
            
            from moviepy.editor import ImageClip
            info_clip = ImageClip(str(info_file), duration=infographic_duration)
            
            # 해상도 통일
            if info_clip.size != resolution:
                logger.info(f"   🔄 리사이즈 중: {info_clip.size} -> {resolution}")
                from moviepy.video.fx.all import resize
                info_clip = resize(info_clip, newsize=resolution)
            
            info_clip = info_clip.set_fps(fps)
            logger.info(f"   ✅ 완료: {info_clip.duration:.2f}초")
            logger.info("")
            
            video_clips.append(info_clip)
    
    # 모든 클립 연결
    logger.info("🔗 모든 클립 연결 중...")
    total_duration = sum(clip.duration for clip in video_clips)
    logger.info(f"   총 {len(video_clips)}개 클립")
    logger.info(f"   예상 총 길이: {total_duration:.2f}초 ({total_duration/60:.2f}분)")
    logger.info("")
    
    final_video = concatenate_videoclips(video_clips, method="compose")
    
    logger.info("")
    
    # 출력 경로 설정
    if output_path is None:
        lang_suffix = "kr" if language == "kr" else "en"
        output_path = f"output/{safe_title}_full_episode_{lang_suffix}.mp4"
    
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    # 렌더링
    logger.info("🎞️ 영상 렌더링 중...")
    logger.info(f"   해상도: {resolution[0]}x{resolution[1]}")
    logger.info(f"   프레임레이트: {fps}fps")
    logger.info(f"   총 길이: {final_video.duration:.2f}초 ({final_video.duration/60:.2f}분)")
    logger.info(f"   출력 파일: {output_path}")
    logger.info("")
    
    final_video.write_videofile(
        output_path,
        fps=fps,
        codec='libx264',
        audio_codec='aac',
        bitrate='5000k',
        audio_bitrate='320k',
        preset='medium'
    )
    
    logger.info("=" * 60)
    logger.info("✅ 전체 에피소드 영상 생성 완료!")
    logger.info("=" * 60)
    logger.info(f"📁 저장 위치: {output_path}")
    logger.info(f"📊 총 길이: {final_video.duration:.2f}초 ({final_video.duration/60:.2f}분)")
    
    # 정리
    final_video.close()
    for clip in video_clips:
        clip.close()
    
    return output_path


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description='Input 폴더의 비디오 파일들을 연결하여 일당백 스타일 영상 생성',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python scripts/concatenate_videos_from_input.py --title "난장이가 쏘아올린 작은 공"
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
        default='kr',
        choices=['kr', 'en'],
        help='언어 (기본값: kr)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='출력 파일 경로 (기본값: output/{책제목}_full_episode_{언어}.mp4)'
    )
    
    parser.add_argument(
        '--infographic-duration',
        type=float,
        default=10.0,
        help='인포그래픽 표시 시간 (초, 기본값: 10.0)'
    )
    
    args = parser.parse_args()
    
    try:
        output_path = concatenate_videos_from_input(
            book_title=args.title,
            language=args.language,
            output_path=args.output,
            infographic_duration=args.infographic_duration
        )
        print(f"\n✅ 성공: {output_path}")
        return 0
    except Exception as e:
        logger.error(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())


