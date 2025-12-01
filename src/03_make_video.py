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
        print(f"⚠️ MoviePy import 오류: {e}")
        print("pip install moviepy")

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

load_dotenv()


class VideoMaker:
    """영상 제작 클래스"""
    
    def __init__(self, resolution: Tuple[int, int] = (1920, 1080), fps: int = 30):
        """
        Args:
            resolution: 해상도 (width, height)
            fps: 프레임레이트
        """
        self.resolution = resolution
        self.fps = fps
        
        if not MOVIEPY_AVAILABLE:
            raise ImportError("MoviePy가 필요합니다. pip install moviepy")
    
    def load_audio(self, audio_path: str) -> AudioFileClip:
        """오디오 파일 로드"""
        audio_file = Path(audio_path)
        if not audio_file.exists():
            raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")
        
        print(f"🎵 오디오 로드 중: {audio_path}")
        try:
            audio = AudioFileClip(audio_path)
            print(f"   길이: {audio.duration:.2f}초")
        except Exception as e:
            raise ValueError(f"오디오 파일 로드 실패: {e}")
        
        return audio
    
    def concatenate_audios(
        self,
        audio_paths: List[str],
        output_path: str = None,
        fade_duration: float = 1.0,
        gap_duration: float = 3.0
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
        
        print("🔗 오디오 연결 중...")
        audio_clips = []
        
        for i, audio_path in enumerate(audio_paths):
            print(f"   [{i+1}/{len(audio_paths)}] 로드: {Path(audio_path).name}")
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
                    print(f"   ⏸️  {gap_duration}초 간격 추가...")
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
                            print(f"   ⚠️ 간격 추가 실패: {e2}, 간격 없이 연결합니다.")
                
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
        print("   연결 중...")
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
        
        print(f"   ✅ 연결 완료: 총 길이 {final_audio.duration:.2f}초")
        
        # 저장 (선택사항)
        if output_path:
            print(f"   💾 저장 중: {output_path}")
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            final_audio.write_audiofile(output_path, codec='aac', bitrate='192k')
            print(f"   ✅ 저장 완료")
        
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
        
        # 고품질 리사이즈
        img = img.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
        
        # 이미지를 numpy 배열로 변환 (한 번만)
        img_array = np.array(img)
        
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
                cropped = img_array[top:bottom, left:right]
                
                # 빈 배열 체크
                if cropped.size == 0:
                    from PIL import Image as PILImage
                    resized = PILImage.fromarray(img_array).resize((target_width, target_height), Image.Resampling.LANCZOS)
                    return np.array(resized)
                
                # 리사이즈 (고품질)
                from PIL import Image as PILImage
                cropped_img = PILImage.fromarray(cropped)
                resized = cropped_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                return np.array(resized)
            except (IndexError, ValueError) as e:
                # 크롭 실패 시 원본 이미지 리사이즈
                from PIL import Image as PILImage
                resized = PILImage.fromarray(img_array).resize((target_width, target_height), Image.Resampling.LANCZOS)
                return np.array(resized)
        
        # make_frame 함수를 사용하여 클립 생성
        try:
            # fl 메서드를 사용하여 프레임별로 효과 적용
            clip = ImageClip(img_array, duration=duration)
            clip = clip.fl(lambda get_frame, t: make_frame(t), apply_to=['video'])
        except Exception as e:
            # 실패 시 기본 클립 반환 (효과 없이)
            print(f"   ⚠️ Ken Burns 효과 적용 실패, 기본 클립 사용: {e}")
            clip = ImageClip(img_array, duration=duration)
            clip = clip.resized(newsize=self.resolution)
        
        return clip
    
    def create_image_sequence(
        self,
        image_paths: List[str],
        total_duration: float,
        fade_duration: float = 1.5  # 페이드 전환 시간 (1.5초 - 자연스러운 전환)
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
            print(f"   ⚠️ 이미지가 {len(image_paths)}개 이상입니다. 앞에서 {max_images}개만 사용합니다.")
        
        # 영상이 끝날 때까지 필요한 이미지 개수 계산
        num_needed = math.ceil(total_duration / duration_per_image)
        num_cycles = math.ceil(num_needed / len(image_paths))
        
        print(f"   📊 사용할 이미지 개수: {len(image_paths)}개 (최대 100개)")
        print(f"   📊 필요한 총 이미지 개수: {num_needed}개")
        print(f"   ⏱️  이미지당 표시 시간: {duration_per_image:.1f}초")
        print(f"   🎨 페이드 전환 시간: {fade_duration:.1f}초 (fade out/in)")
        print(f"   🔄 반복 횟수: {num_cycles}회 (100개 이미지를 순환 사용)")
        print(f"   💡 시청자 관점 권장: 이미지당 4-5초가 가장 자연스럽고 적절합니다")
        
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
            
            # 정적 이미지만 사용 (줌인 효과 없음)
            clip = ImageClip(image_path, duration=clip_duration)
            # MoviePy 버전에 따라 다른 메서드 사용
            try:
                # MoviePy 1.0+ 버전
                clip = clip.resized(height=self.resolution[1])
            except (TypeError, AttributeError):
                try:
                    # 구버전 호환성
                    clip = clip.resize(height=self.resolution[1])
                except:
                    # 최후의 수단: PIL로 직접 리사이즈
                    from PIL import Image as PILImage
                    img = PILImage.open(image_path)
                    img = img.resize(self.resolution, PILImage.Resampling.LANCZOS)
                    clip = ImageClip(img, duration=clip_duration)
            
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
                    
                    if not is_first:
                        # fade in 적용
                        clip = clip.fx(fadein, fade_duration)
                    if not is_last:
                        # fade out 적용
                        clip = clip.fx(fadeout, fade_duration)
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
        
        print(f"   ✅ 총 {len(clips)}개의 클립 생성 완료")
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
            print("⚠️ Whisper가 설치되지 않았습니다. 자막 생성을 건너뜁니다.")
            return None
        
        print("📝 자막 생성 중 (Whisper)...")
        try:
            model = whisper.load_model("base")
            result = model.transcribe(audio_path, language=language)
            
            subtitles = []
            for segment in result.get("segments", []):
                subtitles.append({
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip()
                })
            
            print(f"   ✅ {len(subtitles)}개의 자막 생성 완료")
            return subtitles
            
        except Exception as e:
            print(f"   ❌ 자막 생성 실패: {e}")
            return None
    
    def add_subtitles(
        self,
        video_clip: CompositeVideoClip,
        subtitles: List[dict],
        font_size: int = 60,
        font_color: str = "white",
        stroke_color: str = "black",
        stroke_width: int = 2
    ) -> CompositeVideoClip:
        """
        자막 오버레이 추가
        
        Args:
            video_clip: 비디오 클립
            subtitles: 자막 리스트
            font_size: 폰트 크기
            font_color: 폰트 색상
            stroke_color: 테두리 색상
            stroke_width: 테두리 두께
        """
        if not subtitles:
            return video_clip
        
        subtitle_clips = []
        
        for subtitle in subtitles:
            try:
                text_clip = TextClip(
                    subtitle["text"],
                    fontsize=font_size,
                    color=font_color,
                    stroke_color=stroke_color,
                    stroke_width=stroke_width,
                    method='caption',
                    size=(self.resolution[0] - 100, None),
                    align='center'
                ).with_duration(subtitle["end"] - subtitle["start"]).with_start(subtitle["start"]).with_position(('center', self.resolution[1] - 150))
                
                subtitle_clips.append(text_clip)
            except Exception as e:
                print(f"   ⚠️ 자막 생성 오류: {e}")
                continue
        
        if subtitle_clips:
            return CompositeVideoClip([video_clip] + subtitle_clips)
        
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
        summary_audio_volume: float = 1.2
    ) -> str:
        """
        최종 영상 생성 (Summary → NotebookLM Video → Audio 순서)
        
        Args:
            audio_path: 리뷰 오디오 파일 경로
            image_dir: 이미지 디렉토리
            output_path: 출력 파일 경로
            add_subtitles_flag: 자막 추가 여부
            language: 자막 언어
            max_duration: 최대 길이 제한
            summary_audio_path: 요약 오디오 파일 경로 (있으면 Summary 부분 생성)
            notebooklm_video_path: NotebookLM 비디오 파일 경로 (있으면 중간에 삽입)
            summary_audio_volume: Summary 오디오 음량 배율 (기본값: 1.2, 20% 증가)
        """
        print("=" * 60)
        print("🎬 영상 제작 시작")
        print("=" * 60)
        print()
        
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
            print(f"⚠️ 표지 이미지 발견: {cover_path.name}")
            print("   → 저작권 문제로 사용하지 않습니다. 무드 이미지만 사용합니다.")
        
        for mood_img in mood_images:
            image_paths.append(str(mood_img))
        
        if not image_paths:
            raise FileNotFoundError(f"이미지를 찾을 수 없습니다: {image_dir}")
        
        print(f"🎨 무드 이미지: {len(image_paths)}개")
        print()
        
        video_clips = []
        
        # 1. Summary 부분: 요약 오디오 + 이미지 슬라이드쇼
        if summary_audio_path and Path(summary_audio_path).exists():
            print("📚 1단계: Summary 부분 영상 생성")
            print("-" * 60)
            summary_audio = self.load_audio(summary_audio_path)
            summary_duration = summary_audio.duration
            
            # Summary 오디오 음량 조정
            if summary_audio_volume != 1.0:
                print(f"   🔊 Summary 오디오 음량 조정: {summary_audio_volume}x")
                try:
                    from moviepy.audio.fx.all import volumex
                    summary_audio = summary_audio.fx(volumex, summary_audio_volume)
                except ImportError:
                    try:
                        # 구버전 호환성
                        summary_audio = summary_audio.volumex(summary_audio_volume)
                    except AttributeError:
                        print("   ⚠️ 음량 조정 실패, 원본 음량 사용")
            
            print(f"   요약 오디오 길이: {summary_duration:.2f}초")
            
            # Summary 부분 이미지 시퀀스 생성
            summary_image_clips = self.create_image_sequence(
                image_paths=image_paths,
                total_duration=summary_duration,
                fade_duration=1.5
            )
            summary_video = concatenate_videoclips(summary_image_clips, method="compose")
            summary_video = summary_video.set_audio(summary_audio)
            
            video_clips.append(summary_video)
            print(f"   ✅ Summary 부분 완료 ({summary_duration:.2f}초)")
            print()
        else:
            print("📚 Summary 부분: 요약 오디오가 없어 건너뜁니다.")
            print()
        
        # 2. NotebookLM Video 부분
        if notebooklm_video_path and Path(notebooklm_video_path).exists():
            print("🎥 2단계: NotebookLM Video 부분")
            print("-" * 60)
            print(f"   비디오 로드 중: {Path(notebooklm_video_path).name}")
            
            notebooklm_video = VideoFileClip(notebooklm_video_path)
            
            # 해상도 및 프레임레이트 통일
            if notebooklm_video.size != self.resolution:
                print(f"   🔄 리사이즈 중: {notebooklm_video.size} -> {self.resolution}")
                notebooklm_video = notebooklm_video.resize(self.resolution)
            
            if notebooklm_video.fps != self.fps:
                print(f"   🔄 프레임레이트 조정 중: {notebooklm_video.fps}fps -> {self.fps}fps")
                notebooklm_video = notebooklm_video.set_fps(self.fps)
            
            video_clips.append(notebooklm_video)
            print(f"   ✅ NotebookLM Video 부분 완료 ({notebooklm_video.duration:.2f}초)")
            print()
        else:
            print("🎥 NotebookLM Video 부분: 비디오 파일이 없어 건너뜁니다.")
            print()
        
        # 3. Audio 부분: 리뷰 오디오 + 이미지 슬라이드쇼
        print("🎵 3단계: Audio 부분 영상 생성")
        print("-" * 60)
        review_audio = self.load_audio(audio_path)
        review_duration = review_audio.duration
        
        # 테스트용: 최대 길이 제한
        if max_duration and review_duration > max_duration:
            print(f"   ⚠️ 오디오 길이 제한: {review_duration:.2f}초 → {max_duration}초")
            review_audio = review_audio.subclip(0, max_duration)
            review_duration = max_duration
        
        print(f"   리뷰 오디오 길이: {review_duration:.2f}초")
        
        # Audio 부분 이미지 시퀀스 생성
        review_image_clips = self.create_image_sequence(
            image_paths=image_paths,
            total_duration=review_duration,
            fade_duration=1.5
        )
        review_video = concatenate_videoclips(review_image_clips, method="compose")
        review_video = review_video.set_audio(review_audio)
        
        video_clips.append(review_video)
        print(f"   ✅ Audio 부분 완료 ({review_duration:.2f}초)")
        print()
        
        # 4. 세 부분 연결 (각 섹션 사이에 3초 silence 추가)
        if not video_clips:
            raise ValueError("생성할 영상 클립이 없습니다.")
        
        # 3초 silence 클립 생성 함수
        def create_silence_clip(duration: float = 3.0):
            """3초 검은색 무음 비디오 클립 생성"""
            silence_video = ColorClip(size=self.resolution, color=(0, 0, 0), duration=duration)
            # 무음 오디오 추가
            try:
                from moviepy.audio.AudioClip import AudioArrayClip
                import numpy as np
                sample_rate = 44100
                silence_array = np.zeros((int(sample_rate * duration), 2))
                silence_audio = AudioArrayClip(silence_array, fps=sample_rate)
                silence_video = silence_video.set_audio(silence_audio)
            except Exception as e:
                # 오디오 추가 실패 시 비디오만 반환
                pass
            return silence_video
        
        # 섹션 사이에 3초 silence 추가
        final_clips = []
        silence_duration = 3.0
        
        for i, clip in enumerate(video_clips):
            final_clips.append(clip)
            
            # 마지막 클립이 아니면 3초 silence 추가
            if i < len(video_clips) - 1:
                print(f"   ⏸️  {silence_duration}초 silence 추가...")
                silence_clip = create_silence_clip(silence_duration)
                final_clips.append(silence_clip)
        
        print("🔗 전체 영상 연결 중...")
        print(f"   총 {len(final_clips)}개 클립 연결 (섹션 {len(video_clips)}개 + silence {len(final_clips) - len(video_clips)}개)")
        for i, clip in enumerate(final_clips, 1):
            if i <= len(video_clips):
                print(f"      [{i}] {clip.duration:.2f}초")
            else:
                print(f"      [{i}] {clip.duration:.2f}초 (silence)")
        
        # 페이드 효과로 자연스럽게 연결
        final_video = concatenate_videoclips(final_clips, method="compose")
        total_duration = final_video.duration
        print(f"   ✅ 연결 완료: 총 길이 {total_duration:.2f}초 ({total_duration/60:.2f}분)")
        print()
        
        # 5. 자막 추가 (선택사항)
        if add_subtitles_flag:
            print("📝 자막 생성 중...")
            subtitles = self.generate_subtitles(audio_path, language)
            if subtitles:
                print("📝 자막 오버레이 추가 중...")
                final_video = self.add_subtitles(final_video, subtitles)
                print("   ✅ 자막 추가 완료")
                print()
        
        # 6. 출력 디렉토리 생성
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # 7. 렌더링
        print("🎞️ 영상 렌더링 중...")
        print(f"   해상도: {self.resolution[0]}x{self.resolution[1]}")
        print(f"   프레임레이트: {self.fps}fps")
        print(f"   총 길이: {total_duration:.2f}초 ({total_duration/60:.2f}분)")
        print()
        
        final_video.write_videofile(
            output_path,
            fps=self.fps,
            codec='libx264',
            audio_codec='aac',
            bitrate='1500k',
            preset='medium'
        )
        
        print()
        print("=" * 60)
        print("✅ 영상 제작 완료!")
        print("=" * 60)
        print(f"📁 저장 위치: {output_path}")
        print()
        
        # 정리
        review_audio.close()
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
    
    print()
    
    # 영상 제작
    maker = VideoMaker(resolution=(1920, 1080), fps=30)
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

