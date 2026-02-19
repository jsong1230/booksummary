"""
Phase 4: 영상 합성 및 편집 스크립트
- 오디오 로드
- 이미지 시퀀스 생성 (오디오 길이에 맞춰)
- Ken Burns 효과 (줌인/패닝)
- 전환 효과 (페이드)
- 자막 (OpenAI Whisper, 선택사항)
- 렌더링: 1080p, 30fps MP4
"""

import os
import random
import math
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple
from dotenv import load_dotenv

try:
    from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, TextClip, ColorClip, concatenate_videoclips, VideoFileClip
    from moviepy.video.fx.all import fadein, fadeout
    MOVIEPY_AVAILABLE = True
    MOVIEPY_VERSION_NEW = True
except ImportError as e:
    try:
        # 구버전 호환성
        from moviepy import ImageClip, AudioFileClip, CompositeVideoClip, TextClip, ColorClip, concatenate_videoclips, VideoFileClip
        from moviepy.video.fx import FadeIn, FadeOut, CrossFadeIn, CrossFadeOut
        MOVIEPY_AVAILABLE = True
        MOVIEPY_VERSION_NEW = False
    except ImportError:
        MOVIEPY_AVAILABLE = False
        MOVIEPY_VERSION_NEW = False
        # MoviePy import 오류는 모듈 레벨에서 발생하므로 로거를 사용할 수 없음
        # print 문 유지
        print(f"⚠️ MoviePy import 오류: {e}")
        print("pip install moviepy")

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    from utils.logger import get_logger
except ImportError:
    from src.utils.logger import get_logger

load_dotenv()


class VideoMaker:
    """영상 제작 클래스"""
    
    def __init__(self, resolution: Tuple[int, int] = (1920, 1080), fps: int = 30, bitrate: str = "5000k", audio_bitrate: str = "320k"):
        """
        Args:
            resolution: 해상도 (width, height)
            fps: 프레임레이트
            bitrate: 비디오 비트레이트 (기본값: "5000k")
            audio_bitrate: 오디오 비트레이트 (기본값: "320k")
        """
        self.logger = get_logger(__name__)
        self.resolution = resolution
        self.fps = fps
        self.bitrate = bitrate
        self.audio_bitrate = audio_bitrate
        
        if not MOVIEPY_AVAILABLE:
            raise ImportError("MoviePy가 필요합니다. pip install moviepy")
    
    def load_audio(self, audio_path: str) -> AudioFileClip:
        """오디오 파일 로드"""
        audio_file = Path(audio_path)
        if not audio_file.exists():
            raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")
        
        self.logger.info(f"🎵 오디오 로드 중: {audio_path}")
        try:
            audio = AudioFileClip(audio_path)
            self.logger.info(f"   길이: {audio.duration:.2f}초")
        except Exception as e:
            raise ValueError(f"오디오 파일 로드 실패: {e}")
        
        return audio
    
    def concatenate_audios(
        self,
        audio_paths: List[str],
        output_path: str = None,
        fade_duration: float = 1.0,
        gap_duration: float = 2.0
    ) -> AudioFileClip:
        """
        여러 오디오 파일을 연결
        
        Args:
            audio_paths: 오디오 파일 경로 리스트
            output_path: 연결된 오디오 저장 경로 (선택사항)
            fade_duration: 전환 페이드 시간 (초)
            gap_duration: 오디오 간 간격 시간 (초, 기본값: 3.0)
            
        Returns:
            연결된 오디오 클립
        """
        if not audio_paths:
            raise ValueError("오디오 파일 경로가 필요합니다.")
        
        self.logger.info("🔗 오디오 연결 중...")
        audio_clips = []
        
        for i, audio_path in enumerate(audio_paths):
            self.logger.info(f"[{i+1}/{len(audio_paths)}] 로드: {Path(audio_path).name}")
            audio_clip = self.load_audio(audio_path)
            
            # 오디오 클립에 fade 효과 적용 (오디오 전용 메서드 사용)
            if i > 0:
                # 이전 클립에 fade out
                if audio_clips:
                    try:
                        from moviepy.audio.fx.all import audio_fadeout
                        audio_clips[-1] = audio_clips[-1].fx(audio_fadeout, fade_duration)
                    except ImportError:
                        # 구버전 호환성 또는 fade 효과 없이 진행
                        pass
                
                # 오디오 간 간격 추가 (조용한 구간)
                if gap_duration > 0:
                    self.logger.info(f"⏸️  {gap_duration}초 간격 추가...")
                    try:
                        # 무음 오디오 클립 생성
                        from moviepy.audio.AudioClip import AudioArrayClip
                        import numpy as np
                        # 샘플레이트 가져오기
                        sample_rate = audio_clip.fps if hasattr(audio_clip, 'fps') else 44100
                        # 무음 배열 생성 (스테레오)
                        silence_array = np.zeros((int(sample_rate * gap_duration), 2))
                        silence = AudioArrayClip(silence_array, fps=sample_rate)
                        audio_clips.append(silence)
                    except Exception as e:
                        # AudioArrayClip 실패 시 다른 방법 시도
                        try:
                            from moviepy.editor import ColorClip
                            # 검은색 비디오 클립 생성 (무음 오디오 포함)
                            silence_video = ColorClip(size=(1, 1), color=(0, 0, 0), duration=gap_duration)
                            # 무음 오디오 추가
                            from moviepy.audio.AudioClip import AudioClip
                            silence_audio = AudioClip(lambda t: [0, 0], duration=gap_duration, fps=44100)
                            silence_video = silence_video.set_audio(silence_audio)
                            audio_clips.append(silence_video)
                        except Exception as e2:
                            # 간격 추가 실패 시 경고만 출력하고 계속 진행
                            self.logger.warning(f"간격 추가 실패: {e2}, 간격 없이 연결합니다.")
                
                # 현재 클립에 fade in
                try:
                    from moviepy.audio.fx.all import audio_fadein
                    audio_clip = audio_clip.fx(audio_fadein, fade_duration)
                except ImportError:
                    # 구버전 호환성 또는 fade 효과 없이 진행
                    pass
            
            audio_clips.append(audio_clip)
        
        # 마지막 클립에 fade out
        if audio_clips:
            try:
                from moviepy.audio.fx.all import audio_fadeout
                audio_clips[-1] = audio_clips[-1].fx(audio_fadeout, fade_duration)
            except ImportError:
                pass
        
        # 오디오 클립들을 연결
        self.logger.info("연결 중...")
        try:
            from moviepy.audio.AudioClip import concatenate_audioclips
            final_audio = concatenate_audioclips(audio_clips)
        except ImportError:
            # 구버전 호환성: 비디오 클립으로 변환 후 연결
            from moviepy.editor import ColorClip
            video_clips = []
            for audio_clip in audio_clips:
                # 오디오 길이만큼의 검은색 비디오 클립 생성
                video_clip = ColorClip(size=(1, 1), color=(0, 0, 0), duration=audio_clip.duration)
                video_clip = video_clip.set_audio(audio_clip)
                video_clips.append(video_clip)
            concatenated = concatenate_videoclips(video_clips, method="compose")
            final_audio = concatenated.audio
        
        self.logger.info(f"✅ 연결 완료: 총 길이 {final_audio.duration:.2f}초")
        
        # 저장 (선택사항)
        if output_path:
            self.logger.info(f"💾 저장 중: {output_path}")
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            final_audio.write_audiofile(output_path, codec='aac', bitrate='192k')
            self.logger.info("✅ 저장 완료")
        
        return final_audio
    
    def _ease_in_out(self, t: float) -> float:
        """
        부드러운 easing 함수 (ease-in-out cubic)
        시작과 끝에서 느리게, 중간에서 빠르게
        """
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
    
    def create_image_clip_with_ken_burns(
        self,
        image_path: str,
        duration: float,
        effect_type: str = "zoom_in",
        start_scale: float = 1.0,
        end_scale: float = 1.2,
        pan_direction: Optional[str] = None
    ) -> ImageClip:
        """
        Ken Burns 효과가 적용된 이미지 클립 생성 (부드러운 애니메이션)
        
        Args:
            image_path: 이미지 경로
            duration: 클립 길이 (초)
            effect_type: 효과 타입 ("zoom_in", "zoom_out")
            start_scale: 시작 스케일
            end_scale: 끝 스케일
            pan_direction: 패닝 방향 ("left", "right", "up", "down")
        """
        from PIL import Image
        import numpy as np
        
        # 이미지 로드 및 리사이즈 (해상도보다 크게)
        img = Image.open(image_path)
        img_width, img_height = img.size
        
        # 해상도 비율 계산
        target_width, target_height = self.resolution
        aspect_ratio = target_width / target_height
        img_aspect = img_width / img_height
        
        # 이미지를 해상도보다 크게 리사이즈 (줌 효과를 위해)
        # 최대 스케일보다 더 크게 리사이즈하여 패닝 여유 공간 확보
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
        
        # 이미지 모드 변환 (RGB로 통일)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 고품질 리사이즈
        img = img.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
        
        # 이미지를 numpy 배열로 변환 (한 번만)
        img_array = np.array(img)
        
        # 배열 shape 확인 및 수정 (높이, 너비, 채널 순서)
        if len(img_array.shape) == 2:
            # Grayscale 이미지인 경우 RGB로 변환
            img_array = np.stack([img_array, img_array, img_array], axis=-1)
        elif len(img_array.shape) == 3 and img_array.shape[2] != 3:
            # 채널이 3개가 아닌 경우 (예: RGBA)
            if img_array.shape[2] == 4:
                # RGBA -> RGB 변환
                img_array = img_array[:, :, :3]
            else:
                # 다른 채널 수인 경우 RGB로 변환
                img = Image.fromarray(img_array).convert('RGB')
                img_array = np.array(img)
        
        # 세로형 이미지 여부 확인 (높이가 더 긴 이미지)
        is_portrait = img_aspect < aspect_ratio
        
        # Ken Burns 효과 적용 (부드러운 애니메이션)
        def make_frame(t):
            # 진행률 계산 (0.0 ~ 1.0)
            progress = t / duration if duration > 0 else 0
            progress = min(1.0, max(0.0, progress))
            
            # Easing 적용 (부드러운 전환)
            eased_progress = self._ease_in_out(progress)
            
            # 스케일 계산 (easing 적용)
            if effect_type == "zoom_out":
                current_scale = start_scale + (end_scale - start_scale) * (1 - eased_progress)
            else:  # zoom_in or default
                current_scale = start_scale + (end_scale - start_scale) * eased_progress
            
            # 패닝 계산 (easing 적용)
            pan_x = 0
            pan_y = 0
            if pan_direction:
                # 패닝도 easing 적용하여 부드럽게
                pan_amount = 0.15 * eased_progress  # 최대 15% 이동
                if pan_direction == "left":
                    pan_x = -pan_amount
                elif pan_direction == "right":
                    pan_x = pan_amount
                elif pan_direction == "up":
                    pan_y = -pan_amount
                elif pan_direction == "down":
                    pan_y = pan_amount
            
            # 세로형 이미지 처리: 원본 비율 유지하며 높이에 맞춰 중앙 배치
            if is_portrait:
                # 높이를 target_height에 정확히 맞춤 (스케일 효과 없이)
                display_height = target_height
                display_width = int(display_height * img_aspect)
                
                try:
                    # 원본 이미지 배열 확인
                    if len(img_array.shape) != 3 or img_array.shape[2] != 3:
                        from PIL import Image as PILImage
                        img_pil = PILImage.fromarray(img_array).convert('RGB')
                        img_array = np.array(img_pil)
                    
                    # 원본 이미지를 원본 비율 유지하며 리사이즈
                    from PIL import Image as PILImage
                    img_pil = PILImage.fromarray(img_array)
                    resized_img = img_pil.resize((display_width, display_height), Image.Resampling.LANCZOS)
                    
                    # 검은색 배경에 중앙 배치 (letterbox 효과)
                    final_img = Image.new('RGB', (target_width, target_height), (0, 0, 0))
                    paste_x = (target_width - display_width) // 2
                    paste_y = 0  # 높이에 맞춰서 위에서부터 배치
                    final_img.paste(resized_img, (paste_x, paste_y))
                    
                    return np.array(final_img)
                except (IndexError, ValueError, TypeError) as e:
                    # 실패 시 원본 이미지 사용 (비율 유지)
                    from PIL import Image as PILImage
                    img_pil = PILImage.fromarray(img_array).convert('RGB')
                    display_height = target_height
                    display_width = int(display_height * img_aspect)
                    resized = img_pil.resize((display_width, display_height), Image.Resampling.LANCZOS)
                    
                    # 검은색 배경에 중앙 배치
                    final_img = Image.new('RGB', (target_width, target_height), (0, 0, 0))
                    paste_x = (target_width - display_width) // 2
                    paste_y = 0
                    final_img.paste(resized, (paste_x, paste_y))
                    
                    return np.array(final_img)
            else:
                # 가로형 이미지: 기존 로직 유지
                # 현재 프레임 크기 계산
                current_width = int(target_width / current_scale)
                current_height = int(target_height / current_scale)
                
                # 중심점 계산 (스케일된 이미지 기준)
                center_x = scaled_width // 2
                center_y = scaled_height // 2
                
                # 패닝 적용 (스케일된 이미지 크기 기준)
                center_x += int(pan_x * scaled_width)
                center_y += int(pan_y * scaled_height)
                
                # 크롭 영역 계산 (경계 체크 강화)
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
                
                # 크롭 (numpy 배열 슬라이싱 사용 - 더 빠름)
                try:
                    # 배열 shape 확인: (height, width, channels)
                    if len(img_array.shape) != 3 or img_array.shape[2] != 3:
                        # RGB가 아니면 PIL로 변환 후 처리
                        from PIL import Image as PILImage
                        img_pil = PILImage.fromarray(img_array).convert('RGB')
                        img_array = np.array(img_pil)
                    
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
                    if len(img_array.shape) == 3:
                        img_pil = PILImage.fromarray(img_array).convert('RGB')
                    else:
                        img_pil = PILImage.fromarray(img_array).convert('RGB')
                    resized = img_pil.resize((target_width, target_height), Image.Resampling.LANCZOS)
                    return np.array(resized)
        
        # make_frame 함수를 사용하여 클립 생성
        try:
            # fl 메서드를 사용하여 프레임별로 효과 적용
            clip = ImageClip(img_array, duration=duration)
            clip = clip.fl(lambda get_frame, t: make_frame(t), apply_to=['video'])
        except Exception as e:
            # 실패 시 기본 클립 반환 (효과 없이)
            self.logger.warning(f"Ken Burns 효과 적용 실패, 기본 클립 사용: {e}")
            clip = ImageClip(img_array, duration=duration)
            clip = clip.resized(newsize=self.resolution)
        
        return clip
    
    def create_image_sequence(
        self,
        image_paths: List[str],
        total_duration: float,
        fade_duration: float = 1.5,  # 페이드 전환 시간 (1.5초 - 자연스러운 전환)
        use_ken_burns: bool = True  # Ken Burns 줌/패닝 효과 사용 여부
    ) -> List[ImageClip]:
        """
        이미지 시퀀스 생성 (오디오 길이에 맞춰 반복)
        - 이미지 20개를 영상이 끝날 때까지 계속 반복
        - 자연스러운 fade out/in 전환 효과 적용
        
        Args:
            image_paths: 이미지 경로 리스트 (20개)
            total_duration: 전체 길이 (오디오 길이)
            fade_duration: 페이드 전환 시간 (기본값: 1.5초 - 자연스러운 전환)
        """
        if not image_paths:
            raise ValueError("이미지가 필요합니다.")
        
        num_images = len(image_paths)
        
        # 이미지당 최적 표시 시간 계산
        # 시청자 관점에서 최적: 4-5초
        optimal_duration_per_image = 4.5  # 최적 표시 시간: 4.5초
        min_duration_per_image = 4.0  # 최소 표시 시간: 4초
        max_duration_per_image = 6.0  # 최대 표시 시간: 6초
        
        # 전체 길이를 고려하여 이미지당 표시 시간 계산
        calculated_duration = total_duration / num_images
        
        # 최적 범위 내로 조정
        if calculated_duration < min_duration_per_image:
            duration_per_image = min_duration_per_image
        elif calculated_duration > max_duration_per_image:
            duration_per_image = max_duration_per_image
        else:
            duration_per_image = calculated_duration
        
        # 페이드 전환 시간 조정 (이미지 표시 시간의 30% 이하로 제한)
        fade_duration = min(fade_duration, duration_per_image * 0.3)
        
        # 영상 길이와 상관없이 100개 이미지를 번갈아가면서 사용
        # 이미지 경로를 100개로 제한 (더 많으면 앞에서 100개만 사용)
        max_images = 100
        if len(image_paths) > max_images:
            image_paths = image_paths[:max_images]
            self.logger.warning(f"이미지가 {len(image_paths)}개 이상입니다. 앞에서 {max_images}개만 사용합니다.")
        
        # 영상이 끝날 때까지 필요한 이미지 개수 계산
        num_needed = math.ceil(total_duration / duration_per_image)
        num_cycles = math.ceil(num_needed / len(image_paths))
        
        self.logger.info(f"📊 사용할 이미지 개수: {len(image_paths)}개 (최대 100개)")
        self.logger.info(f"📊 필요한 총 이미지 개수: {num_needed}개")
        self.logger.info(f"⏱️  이미지당 표시 시간: {duration_per_image:.1f}초")
        self.logger.info(f"🎨 페이드 전환 시간: {fade_duration:.1f}초 (fade out/in)")
        self.logger.info(f"🔄 반복 횟수: {num_cycles}회 (100개 이미지를 순환 사용)")
        self.logger.info("💡 시청자 관점 권장: 이미지당 4-5초가 가장 자연스럽고 적절합니다")
        
        clips = []
        current_time = 0.0
        image_index = 0  # 이미지 인덱스 (0부터 시작하여 순환)
        
        # 영상이 끝날 때까지 100개 이미지를 순환하면서 사용
        while current_time < total_duration:
            # 현재 사용할 이미지 (순환)
            image_path = image_paths[image_index % len(image_paths)]
            if current_time >= total_duration:
                break
            
            # 클립 길이 계산 (마지막 클립은 남은 시간만큼만)
            remaining_time = total_duration - current_time
            clip_duration = min(duration_per_image, remaining_time)
            
            if clip_duration <= 0:
                break
            
            # Ken Burns 효과 또는 정적 이미지 사용
            from PIL import Image as PILImage
            import numpy as np
            if use_ken_burns:
                # Ken Burns 줌/패닝 효과 적용 (이탈률 감소 효과)
                effect_types = ["zoom_in", "zoom_out"]
                pan_directions = [None, "left", "right", None]
                effect_type = effect_types[image_index % len(effect_types)]
                pan_dir = pan_directions[image_index % len(pan_directions)]
                try:
                    clip = self.create_image_clip_with_ken_burns(
                        image_path=image_path,
                        duration=clip_duration,
                        effect_type=effect_type,
                        start_scale=1.0,
                        end_scale=1.15,
                        pan_direction=pan_dir
                    )
                except Exception as e:
                    self.logger.warning(f"Ken Burns 효과 적용 실패 ({Path(image_path).name}): {e}, 정적 이미지로 대체")
                    use_ken_burns = False  # 이후 이미지는 정적으로
            if not use_ken_burns:
                try:
                    img = PILImage.open(image_path)
                    # RGB로 변환
                    if img.mode != 'RGB':
                        img = img.convert('RGB')

                    # 세로형 이미지 여부 확인
                    img_width, img_height = img.size
                    target_width, target_height = self.resolution
                    aspect_ratio = target_width / target_height
                    img_aspect = img_width / img_height
                    is_portrait = img_aspect < aspect_ratio

                    if is_portrait:
                        # 세로형 이미지: 높이에 맞추고 좌우는 검은색
                        display_height = target_height
                        display_width = int(display_height * img_aspect)
                        resized_img = img.resize((display_width, display_height), PILImage.Resampling.LANCZOS)

                        # 검은색 배경에 중앙 배치
                        final_img = PILImage.new('RGB', (target_width, target_height), (0, 0, 0))
                        paste_x = (target_width - display_width) // 2
                        paste_y = 0
                        final_img.paste(resized_img, (paste_x, paste_y))
                        img_array = np.array(final_img)
                        clip = ImageClip(img_array, duration=clip_duration)
                    else:
                        # 가로형 이미지: 기존 로직 (해상도에 맞게 리사이즈)
                        img = img.resize(self.resolution, PILImage.Resampling.LANCZOS)
                        img_array = np.array(img)

                        # shape 확인: (height, width, channels) 형식이어야 함
                        if len(img_array.shape) != 3 or img_array.shape[2] != 3:
                            img = PILImage.fromarray(img_array).convert('RGB')
                            img_array = np.array(img)
                        clip = ImageClip(img_array, duration=clip_duration)
                except Exception as e:
                    self.logger.warning(f"이미지 로드 실패 ({Path(image_path).name}): {e}, 기본 방법 사용")
                    try:
                        # 예외 처리: 세로형 이미지 처리 포함
                        img = PILImage.open(image_path)
                        if img.mode != 'RGB':
                            img = img.convert('RGB')

                        img_width, img_height = img.size
                        target_width, target_height = self.resolution
                        aspect_ratio = target_width / target_height
                        img_aspect = img_width / img_height
                        is_portrait = img_aspect < aspect_ratio

                        if is_portrait:
                            display_height = target_height
                            display_width = int(display_height * img_aspect)
                            resized_img = img.resize((display_width, display_height), PILImage.Resampling.LANCZOS)
                            final_img = PILImage.new('RGB', (target_width, target_height), (0, 0, 0))
                            paste_x = (target_width - display_width) // 2
                            paste_y = 0
                            final_img.paste(resized_img, (paste_x, paste_y))
                            clip = ImageClip(np.array(final_img), duration=clip_duration)
                        else:
                            clip = ImageClip(image_path, duration=clip_duration)
                            clip = clip.resized(newsize=self.resolution)
                    except Exception:
                        # 최후의 수단: 세로형 이미지 처리 포함
                        img = PILImage.open(image_path).convert('RGB')
                        img_width, img_height = img.size
                        target_width, target_height = self.resolution
                        aspect_ratio = target_width / target_height
                        img_aspect = img_width / img_height
                        is_portrait = img_aspect < aspect_ratio

                        if is_portrait:
                            display_height = target_height
                            display_width = int(display_height * img_aspect)
                            resized_img = img.resize((display_width, display_height), PILImage.Resampling.LANCZOS)
                            final_img = PILImage.new('RGB', (target_width, target_height), (0, 0, 0))
                            paste_x = (target_width - display_width) // 2
                            paste_y = 0
                            final_img.paste(resized_img, (paste_x, paste_y))
                            clip = ImageClip(np.array(final_img), duration=clip_duration)
                        else:
                            img = img.resize(self.resolution, PILImage.Resampling.LANCZOS)
                            clip = ImageClip(np.array(img), duration=clip_duration)
            
            # fade out/in 전환 효과 적용
            # 모든 이미지에 fade out과 fade in을 모두 적용하여 크로스페이드 효과
            if MOVIEPY_AVAILABLE:
                if MOVIEPY_VERSION_NEW:
                    # MoviePy 1.0+ 버전
                    # 첫 번째 이미지가 아니면 fade in 적용
                    # 마지막 이미지가 아니면 fade out 적용
                    # (반복이므로 모든 이미지에 양쪽 모두 적용)
                    
                    # fade in: 이전 이미지에서 전환될 때 (첫 번째가 아니면)
                    # fade out: 다음 이미지로 전환될 때 (마지막이 아니면)
                    is_first = (current_time == 0.0)
                    is_last = (current_time + clip_duration >= total_duration)
                    
                    # fade 효과 적용 전에 클립 크기 확인 및 수정
                    try:
                        # 클립의 첫 프레임을 가져와서 크기 확인
                        test_frame = clip.get_frame(0)
                        if len(test_frame.shape) == 3:
                            # RGB 이미지인 경우
                            expected_shape = (self.resolution[1], self.resolution[0], 3)
                            if test_frame.shape != expected_shape:
                                # 크기가 맞지 않으면 리사이즈
                                clip = clip.resized(newsize=self.resolution)
                    except:
                        # 크기 확인 실패 시 리사이즈 시도
                        try:
                            clip = clip.resized(newsize=self.resolution)
                        except:
                            pass
                    
                    if not is_first:
                        # fade in 적용
                        try:
                            clip = clip.fx(fadein, fade_duration)
                        except Exception as e:
                            self.logger.warning(f"fade in 적용 실패: {e}, fade 효과 없이 진행")
                    if not is_last:
                        # fade out 적용
                        try:
                            clip = clip.fx(fadeout, fade_duration)
                        except Exception as e:
                            self.logger.warning(f"fade out 적용 실패: {e}, fade 효과 없이 진행")
                else:
                    # 구버전 호환성
                    try:
                        if current_time > 0:
                            clip = clip.with_effects([FadeIn(fade_duration)])
                        if (current_time + clip_duration) < total_duration:
                            clip = clip.with_effects([FadeOut(fade_duration)])
                    except:
                        # 페이드 효과 없이 진행
                        pass
            
            clips.append(clip)
            current_time += clip_duration
            image_index += 1  # 다음 이미지로 이동 (순환)
        
        self.logger.info(f"✅ 총 {len(clips)}개의 클립 생성 완료")
        return clips
    
    def generate_subtitles(self, audio_path: str, language: str = "ko") -> Optional[List[dict]]:
        """
        OpenAI Whisper로 자막 생성
        
        Args:
            audio_path: 오디오 파일 경로
            language: 언어 코드 ("ko", "en" 등)
            
        Returns:
            자막 리스트 [{"start": float, "end": float, "text": str}, ...]
        """
        if not WHISPER_AVAILABLE:
            self.logger.warning("Whisper가 설치되지 않았습니다. 자막 생성을 건너뜁니다.")
            return None
        
        self.logger.info("📝 자막 생성 중 (Whisper)...")
        try:
            # 오디오 파일 존재 확인
            audio_file = Path(audio_path)
            if not audio_file.exists():
                self.logger.error(f"오디오 파일을 찾을 수 없습니다: {audio_path}")
                return None
            
            self.logger.info(f"📁 오디오 파일: {audio_file.name}")
            model = whisper.load_model("base")
            result = model.transcribe(str(audio_path), language=language)
            
            if not result or "segments" not in result:
                self.logger.warning("Whisper 결과가 비어있습니다.")
                return None
            
            subtitles = []
            for segment in result.get("segments", []):
                subtitles.append({
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip()
                })
            
            self.logger.info(f"✅ {len(subtitles)}개의 자막 생성 완료")
            return subtitles
            
        except Exception as e:
            self.logger.error(f"자막 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_subtitles_from_text(
        self,
        text: str,
        audio_duration: float,
        language: str = "ko",
        audio_path: Optional[str] = None
    ) -> Optional[List[dict]]:
        """
        Summary 텍스트와 실제 오디오 파일을 기반으로 자막 생성
        오디오 파일이 제공되면 Whisper로 정확한 타이밍을 분석하고,
        원본 텍스트와 매칭하여 자막 생성
        
        Args:
            text: Summary 텍스트
            audio_duration: 오디오 길이 (초)
            language: 언어 코드 ("ko", "en" 등)
            audio_path: 실제 오디오 파일 경로 (있으면 Whisper로 타이밍 분석)
            
        Returns:
            자막 리스트 [{"start": float, "end": float, "text": str}, ...]
        """
        import re
        from difflib import SequenceMatcher
        
        # 오디오 파일이 있으면 Whisper로 정확한 타이밍 분석
        if audio_path and Path(audio_path).exists() and WHISPER_AVAILABLE:
            self.logger.info("📝 자막 생성 중 (Whisper 단어 단위 타이밍 분석)...")
            try:
                audio_file = Path(audio_path)
                if not audio_file.exists():
                    self.logger.error(f"오디오 파일을 찾을 수 없습니다: {audio_path}")
                    return None
                
                self.logger.info(f"📁 오디오 파일: {audio_file.name}")
                # Whisper로 오디오 분석 (단어 단위 타임스탬프 포함)
                model = whisper.load_model("base")
                result = model.transcribe(
                    str(audio_path), 
                    language=language,
                    word_timestamps=True  # 단어 단위 타임스탬프 활성화
                )
                
                if not result:
                    self.logger.warning("Whisper 결과가 비어있습니다.")
                    return None
                
                # 원본 텍스트 정리 (마크다운 제거)
                cleaned_text = self._clean_markdown_text(text)
                
                # 원본 텍스트를 문장 단위로 분할
                original_sentences = self._split_sentences(cleaned_text, language)
                
                # Whisper 결과의 첫 번째 세그먼트 시작 시간 확인 (타이밍 보정용)
                segments = result.get("segments", [])
                time_offset = 0.0
                if segments:
                    first_segment_start = segments[0].get("start", 0.0)
                    if first_segment_start > 0.1:  # 0.1초 이상 차이나면 보정
                        time_offset = first_segment_start
                        self.logger.info(f"⏱️ 타이밍 보정: 첫 세그먼트 시작 시간 {first_segment_start:.2f}초만큼 조정")
                
                # Whisper 단어 단위 타임스탬프 수집 (타이밍 보정 적용)
                whisper_words = []
                for segment in segments:
                    if "words" in segment:
                        for word_info in segment["words"]:
                            # 타이밍 보정: 첫 세그먼트 시작 시간만큼 빼기
                            adjusted_start = max(0.0, word_info["start"] - time_offset)
                            adjusted_end = max(0.0, word_info["end"] - time_offset)
                            whisper_words.append({
                                "word": word_info["word"].strip(),
                                "start": adjusted_start,
                                "end": adjusted_end
                            })
                
                if not whisper_words:
                    self.logger.warning("Whisper 단어 타임스탬프가 없습니다. 세그먼트 단위로 전환합니다.")
                    # 단어 타임스탬프가 없으면 세그먼트 단위로 폴백 (타이밍 보정 적용)
                    whisper_segments = []
                    for segment in segments:
                        # 타이밍 보정: 첫 세그먼트 시작 시간만큼 빼기
                        adjusted_start = max(0.0, segment["start"] - time_offset)
                        adjusted_end = max(0.0, segment["end"] - time_offset)
                        whisper_segments.append({
                            "start": adjusted_start,
                            "end": adjusted_end,
                            "text": segment["text"].strip()
                        })
                    subtitles = self._match_sentences_to_whisper(
                        original_sentences, 
                        whisper_segments, 
                        language
                    )
                    if subtitles:
                        self.logger.info(f"✅ {len(subtitles)}개의 자막 생성 완료 (Whisper 세그먼트 타이밍 사용)")
                        return subtitles
                    else:
                        return self._generate_subtitles_from_text_fallback(text, audio_duration, language)
                
                # 단어 단위 정렬을 사용하여 자막 생성
                subtitles = self._align_words_to_sentences(
                    original_sentences,
                    whisper_words,
                    language
                )
                
                if subtitles:
                    # 타이밍 검증 및 보정: 오디오 길이를 초과하지 않도록
                    subtitles = self._validate_and_adjust_subtitle_timing(subtitles, audio_duration)
                    self.logger.info(f"✅ {len(subtitles)}개의 자막 생성 완료 (Whisper 단어 단위 타이밍 사용)")
                    return subtitles
                else:
                    self.logger.warning("단어 정렬 실패. 세그먼트 단위로 전환합니다.")
                    # 폴백: 세그먼트 단위 매칭 (타이밍 보정 적용)
                    whisper_segments = []
                    for segment in segments:
                        # 타이밍 보정: 첫 세그먼트 시작 시간만큼 빼기
                        adjusted_start = max(0.0, segment["start"] - time_offset)
                        adjusted_end = max(0.0, segment["end"] - time_offset)
                        whisper_segments.append({
                            "start": adjusted_start,
                            "end": adjusted_end,
                            "text": segment["text"].strip()
                        })
                    subtitles = self._match_sentences_to_whisper(
                        original_sentences, 
                        whisper_segments, 
                        language
                    )
                    if subtitles:
                        # 타이밍 검증 및 보정: 오디오 길이를 초과하지 않도록
                        subtitles = self._validate_and_adjust_subtitle_timing(subtitles, audio_duration)
                        self.logger.info(f"✅ {len(subtitles)}개의 자막 생성 완료 (Whisper 세그먼트 타이밍 사용)")
                        return subtitles
                    else:
                        return self._generate_subtitles_from_text_fallback(text, audio_duration, language)
                    
            except Exception as e:
                self.logger.warning(f"Whisper 분석 실패: {e}. 텍스트 기반으로 전환합니다.")
                import traceback
                traceback.print_exc()
                # Whisper 실패 시 폴백
                return self._generate_subtitles_from_text_fallback(text, audio_duration, language)
        else:
            # 오디오 파일이 없거나 Whisper가 없으면 기존 방식 사용
            if not audio_path:
                self.logger.info("📝 자막 생성 중 (Summary 텍스트 기반, 오디오 파일 없음)...")
            elif not WHISPER_AVAILABLE:
                self.logger.info("📝 자막 생성 중 (Summary 텍스트 기반, Whisper 미설치)...")
            return self._generate_subtitles_from_text_fallback(text, audio_duration, language)
    
    def _clean_markdown_text(self, text: str) -> str:
        """마크다운 문법 제거 및 메타데이터 필터링"""
        import re
        
        # HTML 주석 제거 (<!-- -->)
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        
        # 파일 시작 부분의 메타데이터 제거
        lines = text.split('\n')
        cleaned_lines = []
        skip_metadata = True
        metadata_patterns = [
            r'^📘',  # 책 이모지
            r'^📖',  # 책 이모지
            r'^TTS 기준',
            r'^서머리 스크립트',
            r'^Summary script',
            r'^TTS 기준.*서머리',
            r'^TTS 기준.*스크립트',
            r'^.*약.*분.*서머리',
            r'^.*약.*분.*스크립트',
        ]
        
        for i, line in enumerate(lines):
            # 빈 줄이 나오면 메타데이터 구간 종료로 간주
            if skip_metadata and line.strip() == '':
                if i + 1 < len(lines) and lines[i + 1].strip():
                    skip_metadata = False
                    continue
            
            # 메타데이터 구간에서는 패턴 매칭하여 제거
            if skip_metadata:
                is_metadata = False
                for pattern in metadata_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        is_metadata = True
                        break
                
                # 첫 3줄 내에서 저자 이름이나 책 제목만 있는 경우도 메타데이터로 간주
                if i < 3 and line.strip() and not any(tag in line for tag in ['[HOOK]', '[SUMMARY]', '[BRIDGE]', '[CLOSING]']):
                    if len(line.strip()) < 50 and not line.strip().startswith('['):
                        is_metadata = True
                
                if is_metadata:
                    continue
            
            cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        # 구조적 태그 제거
        text = re.sub(r'\[HOOK\s*–?\s*[^\]]*\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[HOOK\]', '', text)
        text = re.sub(r'\[SUMMARY\s*–?\s*[^\]]*\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[SUMMARY\]', '', text)
        text = re.sub(r'\[BRIDGE\s*–?\s*[^\]]*\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[BRIDGE\]', '', text)
        text = re.sub(r'\[CLOSING\s*–?\s*[^\]]*\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[CLOSING\]', '', text)
        
        # 기타 구조적 태그 제거
        text = re.sub(r'\[[^\]]+\]\s*$', '', text, flags=re.MULTILINE)
        
        text = re.sub(r'#+\s*', '', text)  # 헤더 제거
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **볼드** 제거
        text = re.sub(r'\*([^*]+)\*', r'\1', text)  # *이탤릭* 제거
        text = re.sub(r'---+\s*', '\n', text)  # 구분선 제거
        text = re.sub(r'^\s*[①-⑳]\s*', '', text, flags=re.MULTILINE)  # 번호 기호 제거
        text = re.sub(r'^\s*[0-9]+\.\s*', '', text, flags=re.MULTILINE)  # 번호 리스트 제거
        text = re.sub(r'^\s*[-*]\s*', '', text, flags=re.MULTILINE)  # 리스트 마커 제거
        text = re.sub(r'『([^』]+)』', r'"\1"', text)  # 『』를 ""로 변환
        text = re.sub(r'「([^」]+)」', r'"\1"', text)  # 「」를 ""로 변환
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # 연속된 빈 줄 정리
        return text.strip()
    
    def _split_sentences(self, text: str, language: str) -> List[str]:
        """텍스트를 문장 단위로 분할"""
        import re
        if language == "ko":
            text = re.sub(r'\n+', ' ', text)
            sentences = re.split(r'([.!?。！？]\s+)', text)
            sentences = [sentences[i] + (sentences[i+1] if i+1 < len(sentences) else '') 
                         for i in range(0, len(sentences), 2) if sentences[i].strip()]
        else:
            text = re.sub(r'\n+', ' ', text)
            sentences = re.split(r'([.!?]\s+)', text)
            sentences = [sentences[i] + (sentences[i+1] if i+1 < len(sentences) else '') 
                         for i in range(0, len(sentences), 2) if sentences[i].strip()]
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]
    
    def _align_words_to_sentences(
        self,
        original_sentences: List[str],
        whisper_words: List[dict],
        language: str
    ) -> Optional[List[dict]]:
        """
        단어 단위 정렬을 사용하여 문장별 자막 생성
        원본 문장의 단어들을 Whisper 단어 타임스탬프와 매칭
        """
        import re
        from difflib import SequenceMatcher
        
        subtitles = []
        whisper_word_idx = 0
        
        # Whisper 단어들을 텍스트로 변환 (매칭용)
        whisper_text = ' '.join([w["word"] for w in whisper_words])
        
        for orig_sentence in original_sentences:
            if whisper_word_idx >= len(whisper_words):
                break
            
            # 원본 문장을 단어로 분할
            if language == "ko":
                # 한국어: 공백과 구두점으로 분할
                orig_words = re.findall(r'\S+', orig_sentence.lower())
            else:
                # 영어: 공백으로 분할
                orig_words = [w.lower().strip('.,!?;:') for w in orig_sentence.split() if w.strip()]
            
            if not orig_words:
                continue
            
            # 현재 위치부터 시작하여 원본 문장의 단어들을 찾기
            matched_word_indices = []
            search_start = whisper_word_idx
            
            # 각 원본 단어를 Whisper 단어 리스트에서 찾기
            for orig_word in orig_words:
                # 원본 단어 정리 (구두점 제거)
                clean_orig_word = re.sub(r'[^\w\s]', '', orig_word.lower())
                if not clean_orig_word:
                    continue
                
                # 현재 위치부터 최대 20개 단어까지 검색
                best_match_idx = -1
                best_similarity = 0.0
                
                for i in range(search_start, min(search_start + 20, len(whisper_words))):
                    whisper_word = re.sub(r'[^\w\s]', '', whisper_words[i]["word"].lower())
                    
                    # 정확히 일치하는 경우
                    if clean_orig_word == whisper_word:
                        best_match_idx = i
                        best_similarity = 1.0
                        break
                    
                    # 유사도 계산
                    sim = SequenceMatcher(None, clean_orig_word, whisper_word).ratio()
                    if sim > best_similarity and sim > 0.6:  # 60% 이상 유사도
                        best_similarity = sim
                        best_match_idx = i
                
                if best_match_idx >= 0:
                    matched_word_indices.append(best_match_idx)
                    search_start = best_match_idx + 1
                else:
                    # 매칭 실패 시 다음 단어로 넘어감
                    continue
            
            # 매칭된 단어가 있으면 자막 생성
            if matched_word_indices:
                # 첫 번째와 마지막 단어의 타임스탬프 사용
                start_time = whisper_words[matched_word_indices[0]]["start"]
                end_time = whisper_words[matched_word_indices[-1]]["end"]
                
                subtitles.append({
                    "start": start_time,
                    "end": end_time,
                    "text": orig_sentence  # 원본 텍스트 사용
                })
                
                # 다음 문장을 위해 마지막 매칭 단어 다음으로 이동
                whisper_word_idx = matched_word_indices[-1] + 1
            else:
                # 매칭 실패 시 현재 위치의 Whisper 단어 시간 사용
                if whisper_word_idx < len(whisper_words):
                    # 다음 몇 개 단어의 시간 범위 사용
                    end_idx = min(whisper_word_idx + len(orig_words), len(whisper_words) - 1)
                    start_time = whisper_words[whisper_word_idx]["start"]
                    end_time = whisper_words[end_idx]["end"]
                    
                    subtitles.append({
                        "start": start_time,
                        "end": end_time,
                        "text": orig_sentence
                    })
                    
                    whisper_word_idx = end_idx + 1
        
        return subtitles if subtitles else None
    
    def _match_sentences_to_whisper(
        self, 
        original_sentences: List[str], 
        whisper_segments: List[dict],
        language: str
    ) -> Optional[List[dict]]:
        """원본 문장과 Whisper 결과를 매칭하여 자막 생성"""
        from difflib import SequenceMatcher
        
        subtitles = []
        whisper_text = ' '.join([seg["text"] for seg in whisper_segments])
        
        # 원본 텍스트 전체와 Whisper 텍스트 전체의 유사도 확인
        original_full = ' '.join(original_sentences)
        similarity = SequenceMatcher(None, original_full.lower(), whisper_text.lower()).ratio()
        
        if similarity < 0.3:  # 유사도가 너무 낮으면 매칭 실패
            return None
        
        # 각 원본 문장을 Whisper 세그먼트와 매칭
        whisper_idx = 0
        for orig_sentence in original_sentences:
            if whisper_idx >= len(whisper_segments):
                break
            
            # 현재 Whisper 세그먼트부터 시작하여 매칭 시도
            best_match_idx = whisper_idx
            best_similarity = 0.0
            best_end_idx = whisper_idx
            
            # 여러 세그먼트를 합쳐서 매칭 시도 (최대 5개 세그먼트까지)
            for end_idx in range(whisper_idx, min(whisper_idx + 5, len(whisper_segments))):
                combined_whisper = ' '.join([
                    whisper_segments[i]["text"] 
                    for i in range(whisper_idx, end_idx + 1)
                ])
                sim = SequenceMatcher(
                    None, 
                    orig_sentence.lower(), 
                    combined_whisper.lower()
                ).ratio()
                
                if sim > best_similarity:
                    best_similarity = sim
                    best_end_idx = end_idx
            
            # 유사도가 0.4 이상이면 매칭 성공
            if best_similarity >= 0.4:
                start_time = whisper_segments[whisper_idx]["start"]
                end_time = whisper_segments[best_end_idx]["end"]
                
                subtitles.append({
                    "start": start_time,
                    "end": end_time,
                    "text": orig_sentence  # 원본 텍스트 사용
                })
                
                whisper_idx = best_end_idx + 1
            else:
                # 매칭 실패 시 현재 세그먼트만 사용하고 다음으로
                if whisper_idx < len(whisper_segments):
                    subtitles.append({
                        "start": whisper_segments[whisper_idx]["start"],
                        "end": whisper_segments[whisper_idx]["end"],
                        "text": orig_sentence  # 원본 텍스트 사용
                    })
                    whisper_idx += 1
        
        return subtitles if subtitles else None
    
    def _validate_and_adjust_subtitle_timing(
        self,
        subtitles: List[dict],
        audio_duration: float
    ) -> List[dict]:
        """
        자막 타이밍 검증 및 보정
        - 오디오 길이를 초과하지 않도록 조정
        - 음수 타이밍 제거
        - 타이밍 순서 정렬
        """
        if not subtitles:
            return subtitles
        
        validated_subtitles = []
        for subtitle in subtitles:
            start = max(0.0, subtitle.get("start", 0.0))
            end = min(audio_duration, subtitle.get("end", audio_duration))
            
            # 시작 시간이 끝 시간보다 크면 스왑
            if start > end:
                start, end = end, start
            
            # 최소 자막 길이 확인 (0.5초)
            if end - start < 0.5:
                end = start + 0.5
                if end > audio_duration:
                    end = audio_duration
                    start = max(0.0, end - 0.5)
            
            validated_subtitles.append({
                "start": start,
                "end": end,
                "text": subtitle.get("text", "")
            })
        
        # 시작 시간 순으로 정렬
        validated_subtitles.sort(key=lambda x: x["start"])
        
        # 중복 제거 및 겹치는 자막 병합
        merged_subtitles = []
        for subtitle in validated_subtitles:
            if not merged_subtitles:
                merged_subtitles.append(subtitle)
            else:
                last = merged_subtitles[-1]
                # 이전 자막과 겹치거나 너무 가까우면 병합
                if subtitle["start"] <= last["end"] + 0.3:
                    last["end"] = max(last["end"], subtitle["end"])
                    last["text"] = last["text"] + " " + subtitle["text"]
                else:
                    merged_subtitles.append(subtitle)
        
        return merged_subtitles
    
    def _generate_subtitles_from_text_fallback(
        self,
        text: str,
        audio_duration: float,
        language: str = "ko"
    ) -> Optional[List[dict]]:
        """텍스트 기반 자막 생성 (폴백 방식)"""
        import re
        
        try:
            # 텍스트 정리
            cleaned_text = self._clean_markdown_text(text)
            
            # 문장 분할
            sentences = self._split_sentences(cleaned_text, language)
            
            if not sentences:
                self.logger.warning("문장을 찾을 수 없습니다.")
                return None
            
            # 각 문장의 길이에 비례하여 시간 할당
            total_chars = sum(len(s) for s in sentences)
            if total_chars == 0:
                return None
            
            subtitles = []
            current_time = 0.0
            
            # 각 문장의 기본 시간 계산
            sentence_durations = []
            for sentence in sentences:
                base_duration = (len(sentence) / total_chars) * audio_duration
                min_duration = 2.0
                max_duration = 8.0
                base_duration = max(min_duration, min(max_duration, base_duration))
                sentence_durations.append(base_duration)
            
            # 전체 예상 시간 계산
            total_estimated = sum(sentence_durations)
            
            # 실제 오디오 시간과의 비율 계산
            if total_estimated > 0:
                time_ratio = audio_duration / total_estimated
            else:
                time_ratio = 1.0
            
            # 비율을 적용하여 시간 할당
            for i, (sentence, base_duration) in enumerate(zip(sentences, sentence_durations)):
                sentence_duration = base_duration * time_ratio
                
                if i == len(sentences) - 1:
                    end_time = audio_duration
                else:
                    end_time = current_time + sentence_duration
                    if end_time > audio_duration:
                        end_time = audio_duration
                
                subtitles.append({
                    "start": current_time,
                    "end": end_time,
                    "text": sentence
                })
                
                current_time = end_time
                
                if current_time >= audio_duration:
                    break
            
            self.logger.info(f"✅ {len(subtitles)}개의 자막 생성 완료 (텍스트 기반)")
            return subtitles
            
        except Exception as e:
            self.logger.error(f"자막 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def add_subtitles(
        self,
        video_clip: CompositeVideoClip,
        subtitles: List[dict],
        font_size: int = 70,  # 개선: 60 -> 70 (가독성 향상)
        font_color: str = "white",
        stroke_color: str = "black",
        stroke_width: int = 3,  # 개선: 2 -> 3 (가독성 향상)
        language: str = "ko"
    ) -> CompositeVideoClip:
        """
        자막 오버레이 추가 (PIL/Pillow 사용하여 ImageMagick 없이 자막 생성)
        
        Args:
            video_clip: 비디오 클립
            subtitles: 자막 리스트
            font_size: 폰트 크기
            font_color: 폰트 색상
            stroke_color: 테두리 색상
            stroke_width: 테두리 두께
            language: 언어 코드 ("ko", "en" 등)
        """
        if not subtitles:
            self.logger.warning("자막 리스트가 비어있습니다")
            return video_clip
        
        # 언어별 폰트 경로 설정
        font_path = None
        if language == "ko":
            # macOS 한글 폰트 경로
            korean_font_paths = [
                '/System/Library/Fonts/Supplemental/AppleGothic.ttf',
                '/System/Library/Fonts/AppleGothic.ttf',
                '/Library/Fonts/AppleGothic.ttf',
            ]
            for path in korean_font_paths:
                if os.path.exists(path):
                    font_path = path
                    break
        else:
            # 영어 폰트 경로
            english_font_paths = [
                '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
                '/System/Library/Fonts/Supplemental/Arial.ttf',
                '/Library/Fonts/Arial.ttf',
            ]
            for path in english_font_paths:
                if os.path.exists(path):
                    font_path = path
                    break
        
        subtitle_clips = []
        failed_count = 0
        
        # PIL/Pillow를 사용하여 자막 이미지 생성
        try:
            from PIL import Image, ImageDraw, ImageFont
            PIL_AVAILABLE = True
        except ImportError:
            PIL_AVAILABLE = False
            self.logger.error("PIL/Pillow가 설치되지 않았습니다. pip install Pillow")
            return video_clip
        
        self.logger.info(f"📝 {len(subtitles)}개의 자막 클립 생성 중 (PIL 사용)...")
        
        # 폰트 로드
        font_obj = None
        if font_path and os.path.exists(font_path):
            try:
                font_obj = ImageFont.truetype(font_path, font_size)
                self.logger.info(f"📝 폰트 사용: {os.path.basename(font_path)}")
            except Exception as e:
                self.logger.warning(f"폰트 로드 실패: {e}, 기본 폰트 사용")
                font_obj = ImageFont.load_default()
        else:
            self.logger.warning("폰트를 찾을 수 없어 기본 폰트 사용")
            font_obj = ImageFont.load_default()
        
        for i, subtitle in enumerate(subtitles):
            try:
                # 자막 텍스트
                text = subtitle["text"]
                duration = subtitle["end"] - subtitle["start"]
                
                # 텍스트 크기 계산
                temp_img = Image.new('RGB', (100, 100), (0, 0, 0))
                temp_draw = ImageDraw.Draw(temp_img)
                
                # 텍스트가 화면 너비에 맞도록 줄바꿈 처리
                max_width = self.resolution[0] - 200  # 좌우 여백 100px씩
                words = text.split()
                lines = []
                current_line = []
                
                for word in words:
                    test_line = ' '.join(current_line + [word])
                    bbox = temp_draw.textbbox((0, 0), test_line, font=font_obj)
                    text_width = bbox[2] - bbox[0]
                    
                    if text_width <= max_width:
                        current_line.append(word)
                    else:
                        if current_line:
                            lines.append(' '.join(current_line))
                        current_line = [word]
                
                if current_line:
                    lines.append(' '.join(current_line))
                
                if not lines:
                    lines = [text]
                
                # 자막 이미지 생성 (개선: 배경 반투명 박스 추가)
                line_height = font_size + 15  # 개선: 10 -> 15 (줄 간격 증가)
                padding = 20  # 좌우 여백
                img_height = len(lines) * line_height + padding * 2
                subtitle_img = Image.new('RGBA', (self.resolution[0], img_height), (0, 0, 0, 0))
                draw = ImageDraw.Draw(subtitle_img)
                
                # 배경 반투명 박스 그리기 (가독성 향상)
                box_margin = 50  # 좌우 여백
                box_y_start = 10
                box_y_end = img_height - 10
                box_alpha = 180  # 반투명도 (0-255, 180 = 약 70% 불투명)
                box_color = (0, 0, 0, box_alpha)
                draw.rectangle(
                    [(box_margin, box_y_start), (self.resolution[0] - box_margin, box_y_end)],
                    fill=box_color
                )
                
                # 각 줄 그리기
                y_offset = padding
                # 개선: 더 밝은 흰색 사용 (가독성 향상)
                bright_white = (255, 255, 255)
                for line in lines:
                    bbox = draw.textbbox((0, 0), line, font=font_obj)
                    text_width = bbox[2] - bbox[0]
                    x = (self.resolution[0] - text_width) // 2
                    
                    # 테두리 그리기 (stroke 효과) - 개선: 더 두꺼운 테두리
                    if stroke_width > 0:
                        for adj_x in range(-stroke_width, stroke_width + 1):
                            for adj_y in range(-stroke_width, stroke_width + 1):
                                if adj_x != 0 or adj_y != 0:
                                    draw.text((x + adj_x, y_offset + adj_y), line, font=font_obj, fill=stroke_color)
                    
                    # 메인 텍스트 그리기 (밝은 흰색 사용)
                    draw.text((x, y_offset), line, font=font_obj, fill=bright_white)
                    y_offset += line_height
                
                # PIL 이미지를 numpy 배열로 변환
                import numpy as np
                img_array = np.array(subtitle_img)
                
                # ImageClip 생성
                text_clip = ImageClip(img_array, duration=duration)
                
                # 위치 설정 (화면 하단 중앙) - 개선: 약간 위로 이동 (가독성 향상)
                y_position = self.resolution[1] - img_height - 80  # 50 -> 80 (위로 이동)
                # MoviePy 버전 호환성: with_start/set_start, with_position/set_position
                try:
                    text_clip = text_clip.with_start(subtitle["start"]).with_position(('center', y_position))
                except AttributeError:
                    # 구버전 호환성
                    text_clip = text_clip.set_start(subtitle["start"]).set_position(('center', y_position))
                
                subtitle_clips.append(text_clip)
                
                if (i + 1) % 10 == 0:
                    self.logger.info(f"{i + 1}/{len(subtitles)}개 생성됨...")
                    
            except Exception as e:
                failed_count += 1
                if failed_count <= 3:  # 처음 3개 오류만 상세 출력
                    self.logger.warning(f"자막 생성 오류 ({i+1}번째): {e}")
                    self.logger.warning(f"텍스트: {subtitle['text'][:50]}...")
                    import traceback
                    traceback.print_exc()
                continue
        
        if failed_count > 0:
            self.logger.warning(f"{failed_count}개의 자막 생성 실패")
        
        if subtitle_clips:
            self.logger.info(f"✅ {len(subtitle_clips)}개의 자막 클립 생성 완료")
            try:
                result = CompositeVideoClip([video_clip] + subtitle_clips)
                self.logger.info("✅ 자막 오버레이 합성 완료")
                return result
            except Exception as e:
                self.logger.error(f"자막 오버레이 합성 실패: {e}")
                import traceback
                traceback.print_exc()
                return video_clip
        
        self.logger.warning("생성된 자막 클립이 없습니다")
        return video_clip
    
    def create_video(
        self,
        audio_path: str,
        image_dir: str,
        output_path: str,
        add_subtitles_flag: bool = False,
        language: str = "ko",
        max_duration: Optional[float] = None,
        summary_audio_path: Optional[str] = None,
        notebooklm_video_path: Optional[str] = None,
        summary_audio_volume: float = 1.2,
        summary_text: Optional[str] = None
    ) -> str:
        """
        최종 영상 생성 (Summary -> NotebookLM Video 순서)
        
        Args:
            audio_path: (사용 안 함, 하위 호환성을 위해 유지)
            image_dir: 이미지 디렉토리
            output_path: 출력 파일 경로
            add_subtitles_flag: 자막 추가 여부
            language: 자막 언어
            max_duration: 최대 길이 제한 (사용 안 함)
            summary_audio_path: 요약 오디오 파일 경로 (있으면 Summary 부분 생성)
            notebooklm_video_path: NotebookLM 비디오 파일 경로 (있으면 중간에 삽입)
            summary_audio_volume: Summary 오디오 음량 배율 (기본값: 1.2, 20% 증가)
            summary_text: Summary 텍스트 (자막 생성용, 선택사항)
        """
        self.logger.info("=" * 60)
        self.logger.info("🎬 영상 제작 시작")
        self.logger.info("=" * 60)
        
        # 이미지 경로 수집
        image_dir_path = Path(image_dir)
        if not image_dir_path.exists():
            raise FileNotFoundError(f"이미지 디렉토리를 찾을 수 없습니다: {image_dir}")
        
        cover_path = image_dir_path / "cover.jpg"
        mood_images = sorted(image_dir_path.glob("mood_*.jpg"))
        
        if not mood_images:
            raise FileNotFoundError(f"무드 이미지를 찾을 수 없습니다: {image_dir}")
        
        image_paths = []
        
        # ⚠️ 표지 이미지는 저작권 문제로 사용하지 않습니다.
        if cover_path.exists():
            self.logger.warning(f"표지 이미지 발견: {cover_path.name}")
            self.logger.info("→ 저작권 문제로 사용하지 않습니다. 무드 이미지만 사용합니다.")
        
        for mood_img in mood_images:
            image_paths.append(str(mood_img))
        
        if not image_paths:
            raise FileNotFoundError(f"이미지를 찾을 수 없습니다: {image_dir}")
        
        self.logger.info(f"🎨 무드 이미지: {len(image_paths)}개")
        
        video_clips = []
        
        # 1. Summary 부분: 요약 오디오 + 이미지 슬라이드쇼
        if summary_audio_path and Path(summary_audio_path).exists():
            self.logger.info("📚 1단계: Summary 부분 영상 생성")
            self.logger.info("-" * 60)
            summary_audio = self.load_audio(summary_audio_path)
            summary_duration = summary_audio.duration
            
            # Summary 오디오 음량 조정
            if summary_audio_volume != 1.0:
                self.logger.info(f"🔊 Summary 오디오 음량 조정: {summary_audio_volume}x")
                try:
                    from moviepy.audio.fx.all import volumex
                    summary_audio = summary_audio.fx(volumex, summary_audio_volume)
                except ImportError:
                    try:
                        # 구버전 호환성
                        summary_audio = summary_audio.volumex(summary_audio_volume)
                    except AttributeError:
                        self.logger.warning("음량 조정 실패, 원본 음량 사용")
            
            self.logger.info(f"요약 오디오 길이: {summary_duration:.2f}초")
            
            # Summary 부분 이미지 시퀀스 생성
            summary_image_clips = self.create_image_sequence(
                image_paths=image_paths,
                total_duration=summary_duration,
                fade_duration=1.5
            )
            summary_video = concatenate_videoclips(summary_image_clips, method="compose")
            summary_video = summary_video.set_audio(summary_audio)
            
            # 영상 시각화 개선: 동적 자막, 파형 등 추가 (정지 화면 방어)
            try:
                import os
                from src.utils.video_enhancements import enhance_video_with_visuals
                self.logger.info("🎨 영상 시각화 개선 적용 중...")
                self.logger.info("   - 동적 자막 (Kinetic Typography): 핵심 키워드 강조")
                self.logger.info("   - 파형 시각화: 오디오 스펙트럼 표시")
                enable_waveform = os.getenv("ENABLE_WAVEFORM", "1").lower() not in ("0", "false", "no")
                
                summary_video = enhance_video_with_visuals(
                    video_clip=summary_video,
                    audio_path=summary_audio_path,
                    text=summary_text,
                    language=language,
                    enable_kinetic_typography=True,  # 동적 자막 활성화
                    enable_waveform=enable_waveform,  # 기본 ON (ENABLE_WAVEFORM=0 로 끄기)
                    enable_footage=False  # 푸티지는 선택사항 (Pexels API 키 필요)
                )
                self.logger.info("✅ 영상 시각화 개선 완료")
            except ImportError as e:
                self.logger.warning(f"영상 시각화 개선 모듈을 찾을 수 없습니다: {e}")
                self.logger.warning("기본 영상만 사용합니다.")
            except Exception as e:
                self.logger.warning(f"영상 시각화 개선 실패 (기본 영상 사용): {e}")
                import traceback
                traceback.print_exc()
            
            # Summary 부분에 자막 추가 (텍스트가 있고 자막 옵션이 켜져 있는 경우)
            self.logger.info(f"🔍 자막 옵션 확인: add_subtitles_flag={add_subtitles_flag}, summary_text={'있음' if summary_text else '없음'}")
            if add_subtitles_flag and summary_text:
                self.logger.info("📝 Summary 자막 생성 중...")
                summary_subtitles = self.generate_subtitles_from_text(
                    text=summary_text,
                    audio_duration=summary_duration,
                    language=language,
                    audio_path=summary_audio_path  # 실제 오디오 파일 경로 전달
                )
                if summary_subtitles:
                    self.logger.info(f"📝 {len(summary_subtitles)}개의 자막 생성됨")
                    self.logger.info("📝 Summary 자막 오버레이 추가 중...")
                    summary_video = self.add_subtitles(
                        summary_video,
                        summary_subtitles,
                        font_size=70,  # 개선: 60 -> 70
                        font_color="white",
                        stroke_color="black",
                        stroke_width=3,  # 개선: 2 -> 3
                        language=language
                    )
                    self.logger.info("✅ Summary 자막 추가 완료")
                else:
                    self.logger.warning("자막 생성 실패 또는 빈 자막")
            else:
                if not add_subtitles_flag:
                    self.logger.warning("자막 옵션이 비활성화되어 있습니다")
                if not summary_text:
                    self.logger.warning("Summary 텍스트가 없습니다")
            
            video_clips.append(summary_video)
            self.logger.info(f"✅ Summary 부분 완료 ({summary_duration:.2f}초)")
        else:
            self.logger.info("📚 Summary 부분: 요약 오디오가 없어 건너뜁니다.")
        
        # 2. NotebookLM Video 부분
        if notebooklm_video_path and Path(notebooklm_video_path).exists():
            self.logger.info("🎥 2단계: NotebookLM Video 부분")
            self.logger.info("-" * 60)
            self.logger.info(f"비디오 로드 중: {Path(notebooklm_video_path).name}")
            
            notebooklm_video = VideoFileClip(notebooklm_video_path)
            
            # 해상도 및 프레임레이트 통일
            if notebooklm_video.size != self.resolution:
                self.logger.info(f"🔄 리사이즈 중: {notebooklm_video.size} -> {self.resolution}")
                notebooklm_video = notebooklm_video.resize(self.resolution)
            
            if notebooklm_video.fps != self.fps:
                self.logger.info(f"🔄 프레임레이트 조정 중: {notebooklm_video.fps}fps -> {self.fps}fps")
                notebooklm_video = notebooklm_video.set_fps(self.fps)
            
            video_clips.append(notebooklm_video)
            self.logger.info(f"✅ NotebookLM Video 부분 완료 ({notebooklm_video.duration:.2f}초)")
        else:
            self.logger.info("🎥 NotebookLM Video 부분: 비디오 파일이 없어 건너뜁니다.")
        
        # 3. 두 부분 연결 (각 섹션 사이에 2초 silence 추가)
        if not video_clips:
            raise ValueError("생성할 영상 클립이 없습니다.")
        
        # 전환 효과 강화: 섹션 전환 시 명확한 신호 제공
        def create_transition_clip(duration: float = 1.5, section_name: str = ""):
            """
            섹션 전환 클립 생성 (개선: 페이드 효과 강화)
            - 검은색 배경에 페이드 인/아웃 효과
            - 섹션 이름 표시 (선택사항)
            """
            transition_video = ColorClip(size=self.resolution, color=(0, 0, 0), duration=duration)
            
            # 무음 오디오 추가
            try:
                from moviepy.audio.AudioClip import AudioArrayClip
                import numpy as np
                sample_rate = 44100
                silence_array = np.zeros((int(sample_rate * duration), 2))
                silence_audio = AudioArrayClip(silence_array, fps=sample_rate)
                transition_video = transition_video.set_audio(silence_audio)
            except Exception as e:
                pass
            
            # 페이드 효과 적용 (전환 강화)
            if MOVIEPY_AVAILABLE and MOVIEPY_VERSION_NEW:
                try:
                    fade_duration = min(0.5, duration / 3)  # 전환 시간의 1/3, 최대 0.5초
                    transition_video = transition_video.fx(fadein, fade_duration).fx(fadeout, fade_duration)
                except Exception as e:
                    self.logger.warning(f"전환 페이드 효과 적용 실패: {e}")
            
            return transition_video
        
        # 섹션 사이에 전환 클립 추가 (개선: 페이드 효과 강화)
        final_clips = []
        transition_duration = 1.5  # 개선: 2초 -> 1.5초 (더 빠른 전환)
        
        for i, clip in enumerate(video_clips):
            # 클립 끝에 페이드 아웃 효과 추가 (전환 강화)
            if MOVIEPY_AVAILABLE and MOVIEPY_VERSION_NEW:
                try:
                    fade_duration = 0.5  # 0.5초 페이드 아웃
                    clip = clip.fx(fadeout, fade_duration)
                except Exception as e:
                    self.logger.warning(f"페이드 아웃 효과 적용 실패: {e}")
            
            final_clips.append(clip)
            
            # 마지막 클립이 아니면 전환 클립 추가
            if i < len(video_clips) - 1:
                section_names = ["Summary", "NotebookLM Analysis", "Review"]
                section_name = section_names[i] if i < len(section_names) else ""
                self.logger.info(f"🔄 전환 효과 추가 ({transition_duration}초, 섹션: {section_name})...")
                transition_clip = create_transition_clip(transition_duration, section_name)
                final_clips.append(transition_clip)
                
                # 다음 클립에 페이드 인 효과 추가 (전환 강화)
                if i + 1 < len(video_clips):
                    next_clip = video_clips[i + 1]
                    if MOVIEPY_AVAILABLE and MOVIEPY_VERSION_NEW:
                        try:
                            fade_duration = 0.5  # 0.5초 페이드 인
                            next_clip = next_clip.fx(fadein, fade_duration)
                            video_clips[i + 1] = next_clip
                        except Exception as e:
                            self.logger.warning(f"페이드 인 효과 적용 실패: {e}")
        
        self.logger.info("🔗 전체 영상 연결 중...")
        self.logger.info(f"총 {len(final_clips)}개 클립 연결 (섹션 {len(video_clips)}개 + 전환 {len(final_clips) - len(video_clips)}개)")
        for i, clip in enumerate(final_clips, 1):
            if i <= len(video_clips):
                self.logger.info(f"[{i}] {clip.duration:.2f}초 (섹션)")
            else:
                self.logger.info(f"[{i}] {clip.duration:.2f}초 (전환)")
        
        # 페이드 효과로 자연스럽게 연결 (개선: 전환 효과 강화)
        final_video = concatenate_videoclips(final_clips, method="compose")
        total_duration = final_video.duration
        self.logger.info(f"✅ 연결 완료: 총 길이 {total_duration:.2f}초 ({total_duration/60:.2f}분)")
        
        # 5. 자막 추가 (선택사항)
        # Note: Summary 부분의 자막은 이미 위에서 추가되었습니다.
        # 전체 영상에 대한 추가 자막이 필요한 경우에만 여기서 처리합니다.
        # 현재는 Summary 부분에만 자막을 추가하므로 이 부분은 사용하지 않습니다.
        
        # 6. 출력 디렉토리 생성
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # 7. 렌더링
        self.logger.info("🎞️ 영상 렌더링 중...")
        self.logger.info(f"해상도: {self.resolution[0]}x{self.resolution[1]}")
        self.logger.info(f"프레임레이트: {self.fps}fps")
        self.logger.info(f"총 길이: {total_duration:.2f}초 ({total_duration/60:.2f}분)")
        
        final_video.write_videofile(
            output_path,
            fps=self.fps,
            codec='libx264',
            audio_codec='aac',
            bitrate=self.bitrate,
            audio_bitrate=self.audio_bitrate,
            preset='medium'
        )
        
        self.logger.info("=" * 60)
        self.logger.info("✅ 영상 제작 완료!")
        self.logger.info("=" * 60)
        self.logger.info(f"📁 저장 위치: {output_path}")
        
        # 정리
        final_video.close()
        if summary_audio_path and Path(summary_audio_path).exists():
            summary_audio.close()
        if notebooklm_video_path and Path(notebooklm_video_path).exists():
            notebooklm_video.close()
        
        return output_path


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='책 리뷰 영상 제작')
    parser.add_argument('--audio', type=str, help='오디오 파일 경로')
    parser.add_argument('--summary-audio', type=str, help='요약 오디오 파일 경로 (선택사항)')
    parser.add_argument('--book-title', type=str, help='책 제목')
    parser.add_argument('--image-dir', type=str, help='이미지 디렉토리')
    parser.add_argument('--output', type=str, help='출력 파일 경로')
    parser.add_argument('--subtitles', action='store_true', help='자막 추가 (Whisper)')
    parser.add_argument('--language', type=str, default='ko', help='자막 언어 (기본값: ko)')
    parser.add_argument('--max-duration', type=float, help='최대 영상 길이 (초, 테스트용)')
    parser.add_argument('--bitrate', type=str, default="5000k", help='비디오 비트레이트 (기본값: 5000k)')
    parser.add_argument('--audio-bitrate', type=str, default="320k", help='오디오 비트레이트 (기본값: 320k)')
    
    args = parser.parse_args()
    
    # 기본값 설정
    if args.audio is None:
        # 자동으로 오디오 파일 찾기
        audio_dir = Path("assets/audio")
        audio_files = list(audio_dir.glob("*.m4a")) + list(audio_dir.glob("*.wav")) + list(audio_dir.glob("*.mp3"))
        if audio_files:
            # 한글 오디오 우선 선택 (파일명에 한글이 포함된 것)
            korean_audio = [f for f in audio_files if any(ord(c) > 127 for c in f.stem)]
            if korean_audio:
                args.audio = str(korean_audio[0])
                print(f"📁 한글 오디오 파일 자동 선택: {args.audio}")
            else:
                args.audio = str(audio_files[0])
                print(f"📁 오디오 파일 자동 선택: {args.audio}")
        else:
            print("❌ 오디오 파일을 찾을 수 없습니다.")
            return
    
    if args.book_title is None:
        # 오디오 파일명에서 책 제목 추출
        audio_name = Path(args.audio).stem
        args.book_title = audio_name.replace("_review", "").replace("_Review", "")
        print(f"📚 책 제목 자동 추출: {args.book_title}")
    
    if args.image_dir is None:
        from utils.file_utils import safe_title
        safe_title_str = safe_title(args.book_title)
        args.image_dir = f"assets/images/{safe_title_str}"
        print(f"🖼️ 이미지 디렉토리: {args.image_dir}")
    
    if args.output is None:
        from utils.file_utils import safe_title
        safe_title_str = safe_title(args.book_title)
        args.output = f"output/{safe_title_str}_review.mp4"
        print(f"📁 출력 파일: {args.output}")
    
    # 영상 제작
    maker = VideoMaker(
        resolution=(1920, 1080), 
        fps=30,
        bitrate=args.bitrate,
        audio_bitrate=args.audio_bitrate
    )
    maker.create_video(
        audio_path=args.audio,
        image_dir=args.image_dir,
        output_path=args.output,
        add_subtitles_flag=args.subtitles,
        language=args.language,
        max_duration=args.max_duration,
        summary_audio_path=args.summary_audio
    )


if __name__ == "__main__":
    main()

