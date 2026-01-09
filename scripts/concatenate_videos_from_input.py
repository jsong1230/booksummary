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
    from moviepy.editor import VideoFileClip, concatenate_videoclips, ImageClip, AudioFileClip
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
    infographic_duration: float = 30.0,
    background_music_path: Optional[str] = None,
    bgm_volume: float = 0.3
) -> str:
    """
    Input 폴더의 비디오 파일들을 연결하여 전체 에피소드 영상 생성
    
    Args:
        book_title: 책 제목
        language: 언어 ('kr' 또는 'en')
        output_path: 출력 파일 경로 (None이면 자동 생성)
        infographic_duration: 인포그래픽 표시 시간 (초, 기본값: 30.0)
        background_music_path: 배경음악 파일 경로 (선택사항)
        bgm_volume: 배경음악 음량 (0.0 ~ 1.0, 기본값: 0.3)
        
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
    info_clip_indices = []  # 배경음악 처리를 위해 인포그래픽 클립의 인덱스 저장
    
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
            
            info_clip = ImageClip(str(info_file), duration=infographic_duration)
            
            # 해상도 통일
            if info_clip.size != resolution:
                logger.info(f"   🔄 리사이즈 중: {info_clip.size} -> {resolution}")
                from moviepy.video.fx.all import resize
                info_clip = resize(info_clip, newsize=resolution)
            
            info_clip = info_clip.set_fps(fps)
            logger.info(f"   ✅ 완료: {info_clip.duration:.2f}초")
            logger.info("")
            
            # 인포그래픽 클립의 인덱스 저장 (배경음악 추가용)
            info_clip_indices.append(len(video_clips))
            video_clips.append(info_clip)
    
    # 배경음악을 인포그래픽에만 추가
    if background_music_path and Path(background_music_path).exists() and info_clip_indices:
        logger.info("🎵 배경음악 추가 중 (인포그래픽에만 적용)...")
        logger.info(f"   파일: {Path(background_music_path).name}")
        logger.info(f"   음량: {bgm_volume * 100:.0f}%")
        
        try:
            # 배경음악 파일 로드
            logger.info(f"   📂 배경음악 파일 로드 중: {Path(background_music_path).name}")
            try:
                bgm = AudioFileClip(background_music_path)
                if bgm.reader is None:
                    raise ValueError("AudioFileClip reader가 None입니다. 파일이 손상되었거나 지원되지 않는 형식일 수 있습니다.")
            except Exception as load_error:
                logger.error(f"   ❌ 배경음악 파일 로드 실패: {load_error}")
                logger.warning("   배경음악 없이 진행합니다.")
                bgm = None
            
            if bgm is not None:
                bgm_duration = bgm.duration
                
                # 음량 조절
                try:
                    from moviepy.audio.fx.all import volumex
                    bgm = bgm.fx(volumex, bgm_volume)
                except ImportError:
                    try:
                        bgm = bgm.volumex(bgm_volume)
                    except AttributeError:
                        logger.warning("   ⚠️ 음량 조절 실패, 원본 음량 사용")
                
                # 각 인포그래픽 클립에 배경음악 추가
                bgm_start_time = 0
                for i, clip_index in enumerate(info_clip_indices):
                    if clip_index < len(video_clips):
                        info_clip = video_clips[clip_index]
                        # 배경음악 세그먼트 생성 (인포그래픽 길이에 맞춤)
                        clip_duration = info_clip.duration
                        bgm_end_time = min(bgm_start_time + clip_duration, bgm_duration)
                        
                        # 배경음악이 부족하면 처음부터 반복
                        if bgm_end_time <= bgm_start_time:
                            bgm_start_time = 0
                            bgm_end_time = min(clip_duration, bgm_duration)
                        
                        bgm_segment = bgm.subclip(bgm_start_time, bgm_end_time)
                        
                        # 오디오 길이를 정확히 클립 길이에 맞춤
                        if bgm_segment.duration < clip_duration:
                            # 배경음악이 짧으면 반복
                            from moviepy.audio.AudioClip import concatenate_audioclips
                            loops_needed = int(clip_duration / bgm_segment.duration) + 1
                            bgm_segment = concatenate_audioclips([bgm_segment] * loops_needed)
                            bgm_segment = bgm_segment.subclip(0, clip_duration)
                        elif bgm_segment.duration > clip_duration:
                            # 배경음악이 길면 자르기
                            bgm_segment = bgm_segment.subclip(0, clip_duration)
                        
                        # fadeout 효과 추가 (마지막 2초)
                        fadeout_duration = min(2.0, clip_duration * 0.2)  # 최대 2초 또는 클립 길이의 20%
                        try:
                            from moviepy.audio.fx.all import audio_fadeout
                            bgm_segment = bgm_segment.fx(audio_fadeout, fadeout_duration)
                        except (ImportError, AttributeError):
                            try:
                                import numpy as np
                                def make_frame(t):
                                    if t >= bgm_segment.duration - fadeout_duration:
                                        fade_progress = (t - (bgm_segment.duration - fadeout_duration)) / fadeout_duration
                                        volume_factor = 1.0 - fade_progress
                                        return bgm_segment.get_frame(t) * volume_factor
                                    return bgm_segment.get_frame(t)
                                bgm_segment = bgm_segment.fl(make_frame, apply_to=['audio'])
                            except:
                                logger.warning("   ⚠️ fadeout 효과 적용 실패, 원본 음악 사용")
                        
                        # 인포그래픽 클립에 배경음악 추가
                        info_clip_with_audio = info_clip.set_audio(bgm_segment)
                        video_clips[clip_index] = info_clip_with_audio
                        
                        logger.info(f"   ✅ Part {i+1} 인포그래픽에 배경음악 추가")
                        logger.info(f"      - 오디오 길이: {bgm_segment.duration:.2f}초 (클립: {clip_duration:.2f}초)")
                        logger.info(f"      - fadeout: {fadeout_duration:.1f}초")
                        
                        bgm_start_time = bgm_end_time
                        # 배경음악이 끝나면 처음부터 다시 시작
                        if bgm_start_time >= bgm_duration:
                            bgm_start_time = 0
                
                # bgm.close()는 나중에 (렌더링 후) 호출
                logger.info("   ✅ 배경음악 추가 완료 (인포그래픽에만)")
        except Exception as e:
            logger.warning(f"   ⚠️ 배경음악 추가 실패: {e}")
            logger.warning("   배경음악 없이 진행합니다.")
    elif background_music_path:
        logger.warning(f"   ⚠️ 배경음악 파일을 찾을 수 없습니다: {background_music_path}")
        logger.warning("   배경음악 없이 진행합니다.")
    
    logger.info("")
    
    # 배경음악 자동 탐지 (지정되지 않은 경우)
    if background_music_path is None:
        logger.info("🔍 배경음악 자동 탐지 중...")
        
        # 1. input 폴더에서 배경음악 찾기
        bgm_files = []
        if input_dir.exists():
            bgm_patterns = [
                "background*.mp3", "background*.wav", "background*.m4a",
                "bgm*.mp3", "bgm*.wav", "bgm*.m4a",
                "music*.mp3", "music*.wav", "music*.m4a"
            ]
            for pattern in bgm_patterns:
                bgm_files.extend(list(input_dir.glob(pattern)))
            bgm_files = list(set(bgm_files))
        
        # 2. assets/music 폴더에서 배경음악 찾기
        music_dir = Path("assets/music")
        if music_dir.exists():
            bgm_files.extend(list(music_dir.glob("*.mp3")))
            bgm_files.extend(list(music_dir.glob("*.wav")))
            bgm_files.extend(list(music_dir.glob("*.m4a")))
        
        bgm_files = list(set(bgm_files))
        
        if bgm_files:
            # 첫 번째 파일 자동 선택
            background_music_path = str(bgm_files[0])
            logger.info(f"   ✅ 배경음악 자동 선택: {bgm_files[0].name}")
            
            # 배경음악 추가 로직 재실행
            if info_clip_indices:
                try:
                    bgm = AudioFileClip(background_music_path)
                    bgm_duration = bgm.duration
                    
                    # 음량 조절
                    try:
                        from moviepy.audio.fx.all import volumex
                        bgm = bgm.fx(volumex, bgm_volume)
                    except ImportError:
                        try:
                            bgm = bgm.volumex(bgm_volume)
                        except AttributeError:
                            pass
                    
                    # 각 인포그래픽 클립에 배경음악 추가
                    bgm_start_time = 0
                    for i, clip_index in enumerate(info_clip_indices):
                        if clip_index < len(video_clips):
                            info_clip = video_clips[clip_index]
                            clip_duration = info_clip.duration
                            bgm_end_time = min(bgm_start_time + clip_duration, bgm_duration)
                            
                            if bgm_end_time <= bgm_start_time:
                                bgm_start_time = 0
                                bgm_end_time = min(clip_duration, bgm_duration)
                            
                            bgm_segment = bgm.subclip(bgm_start_time, bgm_end_time)
                            
                            if bgm_segment.duration < clip_duration:
                                from moviepy.audio.AudioClip import concatenate_audioclips
                                loops_needed = int(clip_duration / bgm_segment.duration) + 1
                                bgm_segment = concatenate_audioclips([bgm_segment] * loops_needed)
                                bgm_segment = bgm_segment.subclip(0, clip_duration)
                            elif bgm_segment.duration > clip_duration:
                                bgm_segment = bgm_segment.subclip(0, clip_duration)
                            
                            fadeout_duration = min(2.0, clip_duration * 0.2)
                            try:
                                from moviepy.audio.fx.all import audio_fadeout
                                bgm_segment = bgm_segment.fx(audio_fadeout, fadeout_duration)
                            except:
                                pass
                            
                            info_clip_with_audio = info_clip.set_audio(bgm_segment)
                            video_clips[clip_index] = info_clip_with_audio
                            
                            bgm_start_time = bgm_end_time
                            if bgm_start_time >= bgm_duration:
                                bgm_start_time = 0
                    
                    logger.info("   ✅ 배경음악 자동 추가 완료")
                except Exception as e:
                    logger.warning(f"   ⚠️ 배경음악 자동 추가 실패: {e}")
        else:
            logger.info("   💡 배경음악 파일을 찾을 수 없습니다. 배경음악 없이 진행합니다.")
        logger.info("")
    
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
        default=30.0,
        help='인포그래픽 표시 시간 (초, 기본값: 30.0)'
    )
    
    parser.add_argument(
        '--background-music',
        type=str,
        default=None,
        help='배경음악 파일 경로 (선택사항, 자동 탐지 시도)'
    )
    
    parser.add_argument(
        '--bgm-volume',
        type=float,
        default=0.3,
        help='배경음악 음량 (0.0 ~ 1.0, 기본값: 0.3)'
    )
    
    args = parser.parse_args()
    
    try:
        output_path = concatenate_videos_from_input(
            book_title=args.title,
            language=args.language,
            output_path=args.output,
            infographic_duration=args.infographic_duration,
            background_music_path=args.background_music,
            bgm_volume=args.bgm_volume
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


