#!/usr/bin/env python3
"""
NotebookLM 영상과 인포그래픽을 합쳐서 하나의 긴 에피소드 영상으로 생성하는 스크립트

Part 1과 Part 2의 인포그래픽과 영상을 순서대로 합쳐서 전체 에피소드를 만듭니다.
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
    from moviepy.editor import (
        ImageClip,
        VideoFileClip,
        CompositeVideoClip,
        concatenate_videoclips,
        ColorClip,
        AudioFileClip
    )
    from moviepy.video.fx.all import fadein, fadeout
    MOVIEPY_AVAILABLE = True
    MOVIEPY_VERSION_NEW = True
except ImportError as e:
    try:
        # 구버전 호환성
        from moviepy import (
            ImageClip,
            VideoFileClip,
            CompositeVideoClip,
            concatenate_videoclips,
            ColorClip
        )
        from moviepy.video.fx import FadeIn, FadeOut
        MOVIEPY_AVAILABLE = True
        MOVIEPY_VERSION_NEW = False
    except ImportError:
        MOVIEPY_AVAILABLE = False
        logger.error(f"❌ MoviePy import 오류: {e}")
        logger.error("pip install moviepy")
        sys.exit(1)


def create_ken_burns_image_clip(
    image_path: str,
    duration: float,
    start_scale: float = 1.0,
    end_scale: float = 1.1,
    resolution: tuple = (1920, 1080)
) -> ImageClip:
    """
    Ken Burns 효과를 적용한 이미지 클립 생성 (줌인 효과)
    
    Args:
        image_path: 이미지 파일 경로
        duration: 클립 길이 (초)
        start_scale: 시작 스케일 (기본값: 1.0)
        end_scale: 끝 스케일 (기본값: 1.1)
        resolution: 목표 해상도 (기본값: 1920x1080)
        
    Returns:
        Ken Burns 효과가 적용된 ImageClip
    """
    from PIL import Image
    import numpy as np
    
    # 이미지 로드
    img = Image.open(image_path)
    img_width, img_height = img.size
    
    # RGB로 변환
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # 해상도 비율 계산
    target_width, target_height = resolution
    aspect_ratio = target_width / target_height
    img_aspect = img_width / img_height
    
    # 이미지를 해상도보다 크게 리사이즈 (줌 효과를 위해)
    max_scale = max(end_scale, start_scale) * 1.2  # 20% 여유
    scaled_width = int(target_width * max_scale)
    scaled_height = int(target_height * max_scale)
    
    # 종횡비 유지하며 리사이즈
    if img_aspect > aspect_ratio:
        # 이미지가 더 넓음
        scaled_height = int(scaled_width / img_aspect)
    else:
        # 이미지가 더 높음
        scaled_width = int(scaled_height * img_aspect)
    
    # 고품질 리사이즈
    img = img.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
    img_array = np.array(img)
    
    # Easing 함수 (부드러운 전환)
    def ease_in_out(t: float) -> float:
        """ease-in-out cubic"""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
    
    # Ken Burns 효과 적용
    def make_frame(t):
        # 진행률 계산 (0.0 ~ 1.0)
        progress = t / duration if duration > 0 else 0
        progress = min(1.0, max(0.0, progress))
        
        # Easing 적용
        eased_progress = ease_in_out(progress)
        
        # 스케일 계산 (줌인)
        current_scale = start_scale + (end_scale - start_scale) * eased_progress
        
        # 현재 프레임 크기 계산
        current_width = int(target_width / current_scale)
        current_height = int(target_height / current_scale)
        
        # 중심점 계산 (스케일된 이미지 기준)
        center_x = scaled_width // 2
        center_y = scaled_height // 2
        
        # 크롭 영역 계산
        left = max(0, center_x - current_width // 2)
        top = max(0, center_y - current_height // 2)
        right = min(scaled_width, left + current_width)
        bottom = min(scaled_height, top + current_height)
        
        # 유효성 검사
        if right <= left or bottom <= top:
            # 잘못된 크롭 영역이면 원본 이미지 사용
            from PIL import Image as PILImage
            resized = PILImage.fromarray(img_array).resize((target_width, target_height), Image.Resampling.LANCZOS)
            return np.array(resized)
        
        # 크롭
        try:
            cropped = img_array[top:bottom, left:right]
            
            # 빈 배열 체크
            if cropped.size == 0 or len(cropped.shape) != 3:
                from PIL import Image as PILImage
                resized = PILImage.fromarray(img_array).resize((target_width, target_height), Image.Resampling.LANCZOS)
                return np.array(resized)
            
            # 리사이즈 (고품질)
            from PIL import Image as PILImage
            cropped_img = PILImage.fromarray(cropped)
            resized = cropped_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            return np.array(resized)
        except (IndexError, ValueError, TypeError) as e:
            # 크롭 실패 시 원본 이미지 리사이즈
            from PIL import Image as PILImage
            resized = PILImage.fromarray(img_array).resize((target_width, target_height), Image.Resampling.LANCZOS)
            return np.array(resized)
    
    # make_frame 함수를 사용하여 클립 생성
    try:
        clip = ImageClip(img_array, duration=duration)
        clip = clip.fl(lambda get_frame, t: make_frame(t), apply_to=['video'])
    except Exception as e:
        # 실패 시 기본 클립 반환 (효과 없이)
        logger.warning(f"Ken Burns 효과 적용 실패, 기본 클립 사용: {e}")
        from PIL import Image as PILImage
        resized_img = PILImage.fromarray(img_array).resize((target_width, target_height), Image.Resampling.LANCZOS)
        clip = ImageClip(np.array(resized_img), duration=duration)
        clip = clip.resized(newsize=resolution)
    
    return clip


def resize_video_clip(
    clip,
    target_resolution: tuple = (1920, 1080)
):
    """
    비디오 클립 또는 이미지 클립을 목표 해상도로 리사이즈 (비율 유지하며 꽉 차게)
    
    Args:
        clip: 비디오 클립 또는 이미지 클립
        target_resolution: 목표 해상도 (기본값: 1920x1080)
        
    Returns:
        리사이즈된 클립
    """
    from moviepy.editor import ImageClip, VideoFileClip
    
    target_width, target_height = target_resolution
    clip_width, clip_height = clip.size
    
    # 이미 목표 해상도면 그대로 반환
    if clip.size == target_resolution:
        return clip
    
    # ImageClip인지 확인
    is_image_clip = isinstance(clip, ImageClip)
    
    # 현재 비율과 목표 비율 계산
    clip_aspect = clip_width / clip_height
    target_aspect = target_width / target_height
    
    try:
        if clip_aspect > target_aspect:
            # 클립이 더 넓음 -> 높이에 맞추고 좌우 크롭
            new_height = target_height
            new_width = int(new_height * clip_aspect)
            
            # 리사이즈
            try:
                clip = clip.resized(newsize=(new_width, new_height))
            except AttributeError:
                clip = clip.resize((new_width, new_height))
            
            # ImageClip은 cropped 메서드가 없으므로 PIL로 직접 처리
            if is_image_clip:
                # ImageClip의 경우 PIL로 직접 크롭 및 리사이즈
                from PIL import Image
                import numpy as np
                
                # 중앙 크롭 좌표 계산
                x_center = new_width // 2
                x1 = max(0, x_center - target_width // 2)
                x2 = min(new_width, x_center + target_width // 2)
                y1 = 0
                y2 = new_height
                
                # 원본 이미지 가져오기
                frame = clip.get_frame(0)
                img = Image.fromarray(frame)
                
                # 크롭 및 리사이즈
                cropped = img.crop((x1, y1, x2, y2))
                resized = cropped.resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                # 새로운 ImageClip 생성
                clip = ImageClip(np.array(resized), duration=clip.duration)
            else:
                # VideoFileClip의 경우 cropped 사용
                x_center = new_width // 2
                x1 = max(0, x_center - target_width // 2)
                x2 = min(new_width, x_center + target_width // 2)
                y1 = 0
                y2 = new_height
                
                try:
                    clip = clip.cropped(x1=x1, x2=x2, y1=y1, y2=y2)
                except (TypeError, AttributeError):
                    try:
                        clip = clip.cropped(x1=x1, y1=y1, x2=x2, y2=y2)
                    except:
                        # cropped 실패 시 기본 리사이즈만 사용
                        pass
        else:
            # 클립이 더 높음 -> 너비에 맞추고 상하 크롭
            new_width = target_width
            new_height = int(new_width / clip_aspect)
            
            # 리사이즈
            try:
                clip = clip.resized(newsize=(new_width, new_height))
            except AttributeError:
                clip = clip.resize((new_width, new_height))
            
            # ImageClip은 cropped 메서드가 없으므로 PIL로 직접 처리
            if is_image_clip:
                from PIL import Image
                import numpy as np
                
                # 중앙 크롭 좌표 계산
                x1 = 0
                x2 = new_width
                y_center = new_height // 2
                y1 = max(0, y_center - target_height // 2)
                y2 = min(new_height, y_center + target_height // 2)
                
                # 원본 이미지 가져오기
                frame = clip.get_frame(0)
                img = Image.fromarray(frame)
                
                # 크롭 및 리사이즈
                cropped = img.crop((x1, y1, x2, y2))
                resized = cropped.resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                # 새로운 ImageClip 생성
                clip = ImageClip(np.array(resized), duration=clip.duration)
            else:
                # VideoFileClip의 경우 cropped 사용
                x1 = 0
                x2 = new_width
                y_center = new_height // 2
                y1 = max(0, y_center - target_height // 2)
                y2 = min(new_height, y_center + target_height // 2)
                
                try:
                    clip = clip.cropped(x1=x1, x2=x2, y1=y1, y2=y2)
                except (TypeError, AttributeError):
                    try:
                        clip = clip.cropped(x1=x1, y1=y1, x2=x2, y2=y2)
                    except:
                        # cropped 실패 시 기본 리사이즈만 사용
                        pass
        
        # 최종 해상도 확인 및 조정
        if clip.size != target_resolution:
            try:
                clip = clip.resized(newsize=target_resolution)
            except AttributeError:
                clip = clip.resize(target_resolution)
    except Exception as e:
        logger.warning(f"리사이즈/크롭 실패, 기본 리사이즈 사용: {e}")
        # 폴백: 기본 리사이즈만 사용
        try:
            clip = clip.resized(newsize=target_resolution)
        except AttributeError:
            clip = clip.resize(target_resolution)
    
    # None 체크
    if clip is None:
        logger.error("리사이즈 후 클립이 None입니다.")
        raise ValueError("리사이즈 실패: 클립이 None입니다.")
    
    return clip


def create_full_episode(
    book_title: str,
    output_path: Optional[str] = None,
    language: str = "ko",
    infographic_duration: float = 10.0,
    background_music_path: Optional[str] = None,
    bgm_volume: float = 0.3
) -> str:
    """
    NotebookLM 영상과 인포그래픽을 합쳐서 전체 에피소드 영상 생성
    
    Args:
        book_title: 책 제목
        output_path: 출력 파일 경로 (None이면 자동 생성)
        
    Returns:
        생성된 영상 파일 경로
    """
    # 안전한 파일명 생성
    safe_title = get_standard_safe_title(book_title)
    
    # 언어 접미사
    lang_suffix = "_ko" if language == "ko" else "_en"
    
    # 입력 파일 경로
    input_dir = Path("assets/notebooklm") / safe_title / language
    
    # 필수 파일 확인
    part1_info = input_dir / f"part1_info{lang_suffix}.png"
    part1_video = input_dir / f"part1_video{lang_suffix}.mp4"
    part2_info = input_dir / f"part2_info{lang_suffix}.png"
    part2_video = input_dir / f"part2_video{lang_suffix}.mp4"
    
    required_files = {
        "Part 1 인포그래픽": part1_info,
        "Part 1 영상": part1_video,
        "Part 2 인포그래픽": part2_info,
        "Part 2 영상": part2_video
    }
    
    # 파일 존재 확인
    missing_files = []
    for name, file_path in required_files.items():
        if not file_path.exists():
            missing_files.append(f"{name}: {file_path}")
    
    if missing_files:
        logger.error("❌ 필수 파일을 찾을 수 없습니다:")
        for missing in missing_files:
            logger.error(f"   - {missing}")
        raise FileNotFoundError(f"필수 파일이 없습니다: {input_dir}")
    
    logger.info("=" * 60)
    logger.info("🎬 전체 에피소드 영상 생성 시작")
    logger.info("=" * 60)
    logger.info(f"📖 책 제목: {book_title}")
    logger.info(f"🌐 언어: {language.upper()}")
    logger.info(f"📁 입력 디렉토리: {input_dir}")
    logger.info("")
    
    # 해상도 설정
    resolution = (1920, 1080)
    fps = 30
    
    # Clip 1: Part 1 영상
    logger.info("🎥 Clip 1: Part 1 영상 로드 중...")
    logger.info(f"   파일: {part1_video.name}")
    clip1 = VideoFileClip(str(part1_video))
    
    # 해상도 통일
    if clip1.size != resolution:
        logger.info(f"   🔄 리사이즈 중: {clip1.size} -> {resolution}")
        clip1 = resize_video_clip(clip1, resolution)
    
    # 프레임레이트 통일
    if clip1.fps != fps:
        logger.info(f"   🔄 프레임레이트 조정 중: {clip1.fps}fps -> {fps}fps")
        clip1 = clip1.set_fps(fps)
    
    logger.info(f"   ✅ 완료: {clip1.duration:.2f}초")
    logger.info("")
    
    # Clip 2: Part 1 인포그래픽 (사용자 지정 시간, 정적 이미지)
    logger.info("📊 Clip 2: Part 1 인포그래픽 생성 중...")
    logger.info(f"   파일: {part1_info.name}")
    logger.info(f"   효과: 정적 이미지 (고정, {infographic_duration}초)")
    clip2 = ImageClip(str(part1_info), duration=infographic_duration)
    # 해상도 통일
    if clip2.size != resolution:
        logger.info(f"   🔄 리사이즈 중: {clip2.size} -> {resolution}")
        clip2 = resize_video_clip(clip2, resolution)
    clip2 = clip2.set_fps(fps)
    logger.info(f"   ✅ 완료: {clip2.duration:.2f}초")
    logger.info("")
    
    # Clip 3: Part 2 영상
    logger.info("🎥 Clip 3: Part 2 영상 로드 중...")
    logger.info(f"   파일: {part2_video.name}")
    clip3 = VideoFileClip(str(part2_video))
    
    # 해상도 통일
    if clip3.size != resolution:
        logger.info(f"   🔄 리사이즈 중: {clip3.size} -> {resolution}")
        clip3 = resize_video_clip(clip3, resolution)
    
    # 프레임레이트 통일
    if clip3.fps != fps:
        logger.info(f"   🔄 프레임레이트 조정 중: {clip3.fps}fps -> {fps}fps")
        clip3 = clip3.set_fps(fps)
    
    logger.info(f"   ✅ 완료: {clip3.duration:.2f}초")
    logger.info("")
    
    # Clip 4: Part 2 인포그래픽 (사용자 지정 시간, 정적 이미지)
    logger.info("📊 Clip 4: Part 2 인포그래픽 생성 중...")
    logger.info(f"   파일: {part2_info.name}")
    logger.info(f"   효과: 정적 이미지 (고정, {infographic_duration}초)")
    clip4 = ImageClip(str(part2_info), duration=infographic_duration)
    # 해상도 통일
    if clip4.size != resolution:
        logger.info(f"   🔄 리사이즈 중: {clip4.size} -> {resolution}")
        clip4 = resize_video_clip(clip4, resolution)
    clip4 = clip4.set_fps(fps)
    logger.info(f"   ✅ 완료: {clip4.duration:.2f}초")
    logger.info("")
    
    # Crossfade 효과 적용 (1초)
    logger.info("🎨 Crossfade 효과 적용 중...")
    crossfade_duration = 1.0
    
    try:
        if MOVIEPY_VERSION_NEW:
            # Clip 1 끝에 fadeout
            clip1 = clip1.fx(fadeout, crossfade_duration)
            # Clip 2 시작에 fadein
            clip2 = clip2.fx(fadein, crossfade_duration)
            # Clip 2 끝에 fadeout
            clip2 = clip2.fx(fadeout, crossfade_duration)
            # Clip 3 시작에 fadein
            clip3 = clip3.fx(fadein, crossfade_duration)
            # Clip 3 끝에 fadeout
            clip3 = clip3.fx(fadeout, crossfade_duration)
            # Clip 4 시작에 fadein
            clip4 = clip4.fx(fadein, crossfade_duration)
        else:
            # 구버전 호환성
            clip1 = clip1.fx(FadeOut, crossfade_duration)
            clip2 = clip2.fx(FadeIn, crossfade_duration).fx(FadeOut, crossfade_duration)
            clip3 = clip3.fx(FadeIn, crossfade_duration).fx(FadeOut, crossfade_duration)
            clip4 = clip4.fx(FadeIn, crossfade_duration)
        
        logger.info(f"   ✅ Crossfade 효과 적용 완료 ({crossfade_duration}초)")
    except Exception as e:
        logger.warning(f"   ⚠️ Crossfade 효과 적용 실패: {e}")
        logger.warning("   효과 없이 진행합니다.")
    
    logger.info("")
    
    # 모든 클립 연결
    logger.info("🔗 모든 클립 연결 중...")
    video_clips = [clip1, clip2, clip3, clip4]
    
    total_duration = sum(clip.duration for clip in video_clips)
    logger.info(f"   총 {len(video_clips)}개 클립")
    logger.info(f"   예상 총 길이: {total_duration:.2f}초 ({total_duration/60:.2f}분)")
    logger.info("")
    
    # 배경음악을 인포그래픽에만 추가 (클립 연결 전에 처리)
    if background_music_path and Path(background_music_path).exists():
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
                # 인포그래픽 총 길이 계산 (clip2 + clip4)
                infographic_total_duration = clip2.duration + clip4.duration
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
                
                # Clip 2 (Part 1 인포그래픽)에 배경음악 추가 (fadeout 효과 포함)
                bgm_part1 = bgm.subclip(0, min(clip2.duration, bgm_duration))
                # fadeout 효과 추가 (마지막 2초)
                fadeout_duration = min(2.0, clip2.duration * 0.2)  # 최대 2초 또는 클립 길이의 20%
                try:
                    # MoviePy의 audio fadeout 효과
                    from moviepy.audio.fx.all import audio_fadeout
                    bgm_part1 = bgm_part1.fx(audio_fadeout, fadeout_duration)
                except (ImportError, AttributeError):
                    try:
                        # 대안: volumex를 사용한 fadeout 효과
                        import numpy as np
                        def make_frame(t):
                            if t >= bgm_part1.duration - fadeout_duration:
                                # 마지막 fadeout_duration 동안 점진적으로 음량 감소
                                fade_progress = (t - (bgm_part1.duration - fadeout_duration)) / fadeout_duration
                                volume_factor = 1.0 - fade_progress
                                return bgm_part1.get_frame(t) * volume_factor
                            return bgm_part1.get_frame(t)
                        bgm_part1 = bgm_part1.fl(make_frame, apply_to=['audio'])
                    except:
                        logger.warning("   ⚠️ fadeout 효과 적용 실패, 원본 음악 사용")
                clip2 = clip2.set_audio(bgm_part1)
                logger.info(f"   ✅ Part 1 인포그래픽에 배경음악 추가 (fadeout {fadeout_duration:.1f}초)")
                
                # Clip 4 (Part 2 인포그래픽)에 배경음악 추가 (fadeout 효과 포함)
                bgm_start_time = clip2.duration
                bgm_part2 = bgm.subclip(bgm_start_time, min(bgm_start_time + clip4.duration, bgm_duration))
                # fadeout 효과 추가 (마지막 2초)
                fadeout_duration = min(2.0, clip4.duration * 0.2)  # 최대 2초 또는 클립 길이의 20%
                try:
                    # MoviePy의 audio fadeout 효과
                    from moviepy.audio.fx.all import audio_fadeout
                    bgm_part2 = bgm_part2.fx(audio_fadeout, fadeout_duration)
                except (ImportError, AttributeError):
                    try:
                        # 대안: volumex를 사용한 fadeout 효과
                        import numpy as np
                        def make_frame(t):
                            if t >= bgm_part2.duration - fadeout_duration:
                                # 마지막 fadeout_duration 동안 점진적으로 음량 감소
                                fade_progress = (t - (bgm_part2.duration - fadeout_duration)) / fadeout_duration
                                volume_factor = 1.0 - fade_progress
                                return bgm_part2.get_frame(t) * volume_factor
                            return bgm_part2.get_frame(t)
                        bgm_part2 = bgm_part2.fl(make_frame, apply_to=['audio'])
                    except:
                        logger.warning("   ⚠️ fadeout 효과 적용 실패, 원본 음악 사용")
                clip4 = clip4.set_audio(bgm_part2)
                logger.info(f"   ✅ Part 2 인포그래픽에 배경음악 추가 (fadeout {fadeout_duration:.1f}초)")
                
                # bgm.close()는 나중에 (렌더링 후) 호출
                logger.info("   ✅ 배경음악 추가 완료 (인포그래픽에만)")
        except Exception as e:
            logger.warning(f"   ⚠️ 배경음악 추가 실패: {e}")
            logger.warning("   배경음악 없이 진행합니다.")
    elif background_music_path:
        logger.warning(f"   ⚠️ 배경음악 파일을 찾을 수 없습니다: {background_music_path}")
        logger.warning("   배경음악 없이 진행합니다.")
    
    logger.info("")
    
    # 모든 클립 연결
    logger.info("🔗 모든 클립 연결 중...")
    video_clips = [clip1, clip2, clip3, clip4]
    
    total_duration = sum(clip.duration for clip in video_clips)
    logger.info(f"   총 {len(video_clips)}개 클립")
    logger.info(f"   예상 총 길이: {total_duration:.2f}초 ({total_duration/60:.2f}분)")
    logger.info("")
    
    final_video = concatenate_videoclips(video_clips, method="compose")
    
    logger.info("")
    
    # 출력 경로 설정
    if output_path is None:
        output_path = f"output/{safe_title}_full_episode_{language}.mp4"
    
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
    clip2.close()
    clip4.close()
    
    return output_path


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description='NotebookLM 영상과 인포그래픽을 합쳐서 전체 에피소드 영상 생성',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python src/create_full_episode.py --title "노인과 바다"
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
        help='배경음악 파일 경로 (선택사항)'
    )
    
    parser.add_argument(
        '--bgm-volume',
        type=float,
        default=0.3,
        help='배경음악 음량 (0.0 ~ 1.0, 기본값: 0.3)'
    )
    
    args = parser.parse_args()
    
    try:
        output_path = create_full_episode(
            book_title=args.title,
            output_path=args.output,
            language=args.language,
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

