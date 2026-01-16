#!/usr/bin/env python3
"""
NotebookLM 영상과 인포그래픽을 합쳐서 하나의 긴 에피소드 영상으로 생성하는 스크립트

Part 1과 Part 2의 인포그래픽과 영상을 순서대로 합쳐서 전체 에피소드를 만듭니다.
"""

import argparse
import sys
import importlib.util
from pathlib import Path
from typing import Optional

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.file_utils import get_standard_safe_title, load_book_info
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
    
    # 동적으로 모든 Part 찾기
    parts = []
    part_num = 1
    while True:
        video_file = input_dir / f"part{part_num}_video{lang_suffix}.mp4"
        info_file = input_dir / f"part{part_num}_info{lang_suffix}.png"
        
        if video_file.exists():
            parts.append({
                "part_num": part_num,
                "video": video_file,
                "info": info_file if info_file.exists() else None
            })
            part_num += 1
        else:
            # 더 이상 Part가 없으면 중단
            break
    
    if not parts:
        logger.error(f"❌ Part 영상을 찾을 수 없습니다: {input_dir}")
        logger.error(f"   예상 파일명: part1_video{lang_suffix}.mp4, part2_video{lang_suffix}.mp4, ...")
        raise FileNotFoundError(f"Part 영상 파일이 없습니다: {input_dir}")
    
    logger.info(f"✅ 총 {len(parts)}개의 Part 발견")
    for part in parts:
        logger.info(f"   - Part {part['part_num']}: {part['video'].name}")
        if part['info']:
            logger.info(f"     인포그래픽: {part['info'].name}")
        else:
            logger.warning(f"     ⚠️ 인포그래픽 없음: part{part['part_num']}_info{lang_suffix}.png")
    logger.info("")
    
    # 배경음악 자동 탐지 (지정되지 않은 경우)
    if background_music_path is None:
        logger.info("🔍 배경음악 자동 탐지 중...")
        
        # 1. input 폴더에서 배경음악 찾기
        input_dir = Path("input")
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
        else:
            # 배경음악 파일이 없으면 자동 다운로드 시도
            logger.info("   💡 배경음악 파일이 없습니다. 자동 다운로드를 시도합니다...")
            logger.info("")
            
            try:
                # download_background_music 함수 동적 import (파일명이 숫자로 시작)
                download_module_path = project_root / "src" / "21_download_background_music.py"
                if download_module_path.exists():
                    spec = importlib.util.spec_from_file_location("download_background_music", download_module_path)
                    download_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(download_module)
                    download_background_music = download_module.download_background_music
                    
                    # 책 정보 로드 (있는 경우)
                    book_info_path = Path("assets/images") / safe_title / "book_info.json"
                    book_info = None
                    if book_info_path.exists():
                        book_info = load_book_info(str(book_info_path))
                    
                    # 배경음악 다운로드
                    downloaded_bgm = download_background_music(
                        book_title=book_title,
                        book_info=book_info,
                        output_dir=Path("assets/music")
                    )
                    
                    if downloaded_bgm and Path(downloaded_bgm).exists():
                        background_music_path = downloaded_bgm
                        logger.info(f"   ✅ 배경음악 다운로드 완료: {Path(downloaded_bgm).name}")
                    else:
                        logger.warning("   ⚠️ 자동 다운로드 실패. 배경음악 없이 진행합니다.")
                        logger.warning("   💡 수동으로 배경음악을 다운로드하려면:")
                        logger.warning(f"      python src/21_download_background_music.py --title \"{book_title}\"")
                else:
                    logger.warning("   ⚠️ 배경음악 다운로드 모듈을 찾을 수 없습니다.")
                    logger.warning("   배경음악 없이 진행합니다.")
            except Exception as e:
                logger.warning(f"   ⚠️ 배경음악 자동 다운로드 실패: {e}")
                logger.warning("   배경음악 없이 진행합니다.")
        logger.info("")
    
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
    
    # 모든 클립 생성 (각 Part마다 영상 → 인포그래픽 순서)
    video_clips = []
    info_clip_indices = []  # 배경음악 처리를 위해 인포그래픽 클립의 인덱스 저장
    clip_durations = []  # 각 클립의 실제 duration 추적 (metadata용)
    part_clip_info = []  # 각 Part의 클립 정보 저장 (part_num, clip_type, duration)
    
    for i, part in enumerate(parts, 1):
        # 영상 클립
        logger.info(f"🎥 Part {part['part_num']} 영상 로드 중...")
        logger.info(f"   파일: {part['video'].name}")
        video_clip = VideoFileClip(str(part['video']))
        
        # 해상도 통일
        if video_clip.size != resolution:
            logger.info(f"   🔄 리사이즈 중: {video_clip.size} -> {resolution}")
            video_clip = resize_video_clip(video_clip, resolution)
        
        # 프레임레이트 통일
        if video_clip.fps != fps:
            logger.info(f"   🔄 프레임레이트 조정 중: {video_clip.fps}fps -> {fps}fps")
            video_clip = video_clip.set_fps(fps)
        
        logger.info(f"   ✅ 완료: {video_clip.duration:.2f}초")
        logger.info("")
        
        video_clips.append(video_clip)
        part_clip_info.append({
            'part_num': part['part_num'],
            'clip_type': 'video',
            'duration': video_clip.duration
        })
        
        # 인포그래픽 클립 (있는 경우)
        if part['info']:
            logger.info(f"📊 Part {part['part_num']} 인포그래픽 생성 중...")
            logger.info(f"   파일: {part['info'].name}")
            logger.info(f"   효과: 정적 이미지 (고정, {infographic_duration}초)")
            info_clip = ImageClip(str(part['info']), duration=infographic_duration)
            
            # 해상도 통일
            if info_clip.size != resolution:
                logger.info(f"   🔄 리사이즈 중: {info_clip.size} -> {resolution}")
                info_clip = resize_video_clip(info_clip, resolution)
            info_clip = info_clip.set_fps(fps)
            logger.info(f"   ✅ 완료: {info_clip.duration:.2f}초")
            logger.info("")
            
            # 인포그래픽 클립의 인덱스 저장 (배경음악 추가용)
            info_clip_indices.append(len(video_clips))
            video_clips.append(info_clip)
            part_clip_info.append({
                'part_num': part['part_num'],
                'clip_type': 'infographic',
                'duration': info_clip.duration
            })
        else:
            logger.warning(f"   ⚠️ Part {part['part_num']} 인포그래픽 없음, 건너뜀")
            logger.info("")
    
    # Crossfade 효과 적용 (1초) - 오디오 보존
    logger.info("🎨 Crossfade 효과 적용 중...")
    crossfade_duration = 1.0
    
    try:
        if MOVIEPY_VERSION_NEW:
            # 각 클립에 fade 효과 적용 (오디오 보존)
            for i, clip in enumerate(video_clips):
                # 기존 오디오 저장
                original_audio = clip.audio
                
                if i == 0:
                    # 첫 번째 클립: 끝에만 fadeout
                    clip = clip.fx(fadeout, crossfade_duration)
                elif i == len(video_clips) - 1:
                    # 마지막 클립: 시작에만 fadein
                    clip = clip.fx(fadein, crossfade_duration)
                else:
                    # 중간 클립: 양쪽에 fade 효과
                    clip = clip.fx(fadein, crossfade_duration).fx(fadeout, crossfade_duration)
                
                # 오디오가 있으면 다시 추가
                if original_audio is not None:
                    clip = clip.set_audio(original_audio)
                
                video_clips[i] = clip
        else:
            # 구버전 호환성
            for i, clip in enumerate(video_clips):
                # 기존 오디오 저장
                original_audio = clip.audio
                
                if i == 0:
                    clip = clip.fx(FadeOut, crossfade_duration)
                elif i == len(video_clips) - 1:
                    clip = clip.fx(FadeIn, crossfade_duration)
                else:
                    clip = clip.fx(FadeIn, crossfade_duration).fx(FadeOut, crossfade_duration)
                
                # 오디오가 있으면 다시 추가
                if original_audio is not None:
                    clip = clip.set_audio(original_audio)
                
                video_clips[i] = clip
        
        logger.info(f"   ✅ Crossfade 효과 적용 완료 ({crossfade_duration}초)")
        
        # Crossfade 효과 적용 후 실제 duration 업데이트
        for i, clip in enumerate(video_clips):
            if i < len(part_clip_info):
                part_clip_info[i]['duration'] = clip.duration
    except Exception as e:
        logger.warning(f"   ⚠️ Crossfade 효과 적용 실패: {e}")
        logger.warning("   효과 없이 진행합니다.")
    
    logger.info("")
    
    # 배경음악을 인포그래픽에만 추가 (Crossfade 효과 적용 전에 처리)
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
                
                # 각 인포그래픽 클립에 배경음악 추가 (인덱스로 직접 접근)
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
                        
                        logger.info(f"   ✅ Part {parts[i]['part_num']} 인포그래픽에 배경음악 추가")
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
    
    # Part 1 video와 infographic의 종료 시간 계산 및 저장
    try:
        import json
        current_time = 0.0
        part1_video_end_time = None
        part1_info_end_time = None
        
        for clip_info in part_clip_info:
            if clip_info['part_num'] == 1:
                if clip_info['clip_type'] == 'video' and part1_video_end_time is None:
                    part1_video_end_time = current_time + clip_info['duration']
                elif clip_info['clip_type'] == 'infographic' and part1_info_end_time is None:
                    part1_info_end_time = current_time + clip_info['duration']
            
            current_time += clip_info['duration']
        
        # Part 1 시간 정보를 JSON 파일로 저장
        timing_info = {
            'part1_video_end_time': part1_video_end_time,
            'part1_info_end_time': part1_info_end_time,
            'part_clip_info': part_clip_info,
            'total_duration': final_video.duration
        }
        
        timing_info_path = output_path_obj.with_suffix('.timing.json')
        with open(timing_info_path, 'w', encoding='utf-8') as f:
            json.dump(timing_info, f, ensure_ascii=False, indent=2)
        
        if part1_video_end_time is not None:
            logger.info(f"📊 Part 1 Video 종료 시간: {part1_video_end_time:.2f}초 ({int(part1_video_end_time//60)}:{int(part1_video_end_time%60):02d})")
        if part1_info_end_time is not None:
            logger.info(f"📊 Part 1 Infographic 종료 시간: {part1_info_end_time:.2f}초 ({int(part1_info_end_time//60)}:{int(part1_info_end_time%60):02d})")
        logger.info(f"💾 시간 정보 저장: {timing_info_path.name}")
    except Exception as e:
        logger.warning(f"⚠️ 시간 정보 저장 실패: {e}")
    
    # 정리
    final_video.close()
    for clip in video_clips:
        clip.close()
    
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

