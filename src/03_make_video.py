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
    from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, TextClip, ColorClip, concatenate_videoclips
    from moviepy.video.fx.all import fadein, fadeout
    MOVIEPY_AVAILABLE = True
    MOVIEPY_VERSION_NEW = True
except ImportError as e:
    try:
        # 구버전 호환성
        from moviepy import ImageClip, AudioFileClip, CompositeVideoClip, TextClip, ColorClip, concatenate_videoclips
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
        fade_duration: float = 2.0  # 페이드 시간 (2초로 적당하게)
    ) -> List[ImageClip]:
        """
        이미지 시퀀스 생성 (오디오 길이에 맞춰)
        
        Args:
            image_paths: 이미지 경로 리스트
            total_duration: 전체 길이 (오디오 길이)
            fade_duration: 페이드 전환 시간
        """
        if not image_paths:
            raise ValueError("이미지가 필요합니다.")
        
        num_images = len(image_paths)
        # 이미지당 최소 표시 시간 보장 (너무 빠르게 바뀌지 않도록)
        min_duration_per_image = 5.0  # 최소 5초 (적당한 속도)
        duration_per_image = max(total_duration / num_images, min_duration_per_image)
        
        # 실제 필요한 이미지 개수 재계산 (너무 많은 이미지 사용 방지)
        if duration_per_image > total_duration / num_images:
            # 이미지 개수를 줄여서 각 이미지가 더 오래 표시되도록
            effective_num_images = min(num_images, int(total_duration / min_duration_per_image))
            if effective_num_images < num_images:
                # 이미지 선택 (균등하게 분산)
                step = num_images / effective_num_images
                image_paths = [image_paths[int(i * step)] for i in range(effective_num_images)]
                num_images = effective_num_images
                duration_per_image = total_duration / num_images
        
        print(f"   📊 이미지 개수: {num_images}개 (각 {duration_per_image:.1f}초 표시)")
        
        clips = []
        
        for i, image_path in enumerate(image_paths):
            # 정적 이미지만 사용 (줌인 효과 제거)
            clip = ImageClip(image_path, duration=duration_per_image)
            clip = clip.resize(newsize=self.resolution)
            
            # 페이드 효과 추가
            if MOVIEPY_AVAILABLE:
                if MOVIEPY_VERSION_NEW:
                    # MoviePy 1.0+ 버전
                    if i == 0:
                        # 첫 번째: 페이드인
                        clip = clip.fx(fadein, fade_duration)
                    elif i == len(image_paths) - 1:
                        # 마지막: 페이드아웃
                        clip = clip.fx(fadeout, fade_duration)
                    else:
                        # 중간: 양쪽 모두 페이드 (크로스페이드 효과)
                        # 페이드인과 페이드아웃을 모두 적용하여 부드러운 전환
                        fade_out_duration = min(fade_duration, duration_per_image / 2)
                        fade_in_duration = min(fade_duration, duration_per_image / 2)
                        clip = clip.fx(fadein, fade_in_duration).fx(fadeout, fade_out_duration)
                else:
                    # 구버전 호환성
                    try:
                        if i == 0:
                            clip = clip.with_effects([FadeIn(fade_duration)])
                        elif i == len(image_paths) - 1:
                            clip = clip.with_effects([FadeOut(fade_duration)])
                        else:
                            clip = clip.with_effects([CrossFadeIn(fade_duration)])
                    except:
                        # 페이드 효과 없이 진행
                        pass
            
            clips.append(clip)
        
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
        max_duration: Optional[float] = None
    ) -> str:
        """
        최종 영상 생성
        
        Args:
            audio_path: 오디오 파일 경로
            image_dir: 이미지 디렉토리
            output_path: 출력 파일 경로
            add_subtitles_flag: 자막 추가 여부
            language: 자막 언어
        """
        print("=" * 60)
        print("🎬 영상 제작 시작")
        print("=" * 60)
        print()
        
        # 1. 오디오 로드
        audio = self.load_audio(audio_path)
        audio_duration = audio.duration
        
        # 테스트용: 최대 길이 제한
        if max_duration and audio_duration > max_duration:
            print(f"⚠️ 오디오 길이 제한: {audio_duration:.2f}초 → {max_duration}초")
            audio = audio.subclip(0, max_duration)
            audio_duration = max_duration
        
        print()
        
        # 2. 이미지 경로 수집
        image_dir_path = Path(image_dir)
        if not image_dir_path.exists():
            raise FileNotFoundError(f"이미지 디렉토리를 찾을 수 없습니다: {image_dir}")
        
        cover_path = image_dir_path / "cover.jpg"
        mood_images = sorted(image_dir_path.glob("mood_*.jpg"))
        
        if not mood_images:
            raise FileNotFoundError(f"무드 이미지를 찾을 수 없습니다: {image_dir}")
        
        image_paths = []
        
        # ⚠️ 표지 이미지는 저작권 문제로 사용하지 않습니다.
        # 저작권 없는 무드 이미지만 사용합니다.
        if cover_path.exists():
            print(f"⚠️ 표지 이미지 발견: {cover_path.name}")
            print("   → 저작권 문제로 사용하지 않습니다. 무드 이미지만 사용합니다.")
        
        for mood_img in mood_images:
            image_paths.append(str(mood_img))
            print(f"🎨 무드 이미지 추가: {mood_img.name}")
        
        if not image_paths:
            raise FileNotFoundError(f"이미지를 찾을 수 없습니다: {image_dir}")
        
        print(f"\n총 {len(image_paths)}개의 이미지 사용")
        print()
        
        # 3. 이미지 시퀀스 생성
        print("🖼️ 이미지 시퀀스 생성 중...")
        image_clips = self.create_image_sequence(
            image_paths=image_paths,
            total_duration=audio_duration,
            fade_duration=2.0  # 페이드 시간 (2초)
        )
        print(f"   ✅ {len(image_clips)}개의 클립 생성 완료")
        print()
        
        # 4. 클립 연결
        print("🔗 클립 연결 중...")
        video = concatenate_videoclips(image_clips, method="compose")
        print("   ✅ 연결 완료")
        print()
        
        # 5. 오디오 추가
        print("🎵 오디오 추가 중...")
        try:
            # MoviePy 1.0+ 버전
            video = video.set_audio(audio)
        except AttributeError:
            # 구버전 호환성
            video = video.with_audio(audio)
        print("   ✅ 오디오 추가 완료")
        print()
        
        # 6. 자막 추가 (선택사항)
        subtitles = None
        if add_subtitles_flag:
            subtitles = self.generate_subtitles(audio_path, language)
            if subtitles:
                print("📝 자막 오버레이 추가 중...")
                video = self.add_subtitles(video, subtitles)
                print("   ✅ 자막 추가 완료")
                print()
        
        # 7. 출력 디렉토리 생성
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # 8. 렌더링
        print("🎞️ 영상 렌더링 중...")
        print(f"   해상도: {self.resolution[0]}x{self.resolution[1]}")
        print(f"   프레임레이트: {self.fps}fps")
        print(f"   길이: {audio_duration:.2f}초")
        print()
        
        video.write_videofile(
            output_path,
            fps=self.fps,
            codec='libx264',
            audio_codec='aac',
            bitrate='1500k',  # 페이드 효과만 있는 정적 이미지이므로 매우 낮은 비트레이트로 충분
            preset='medium'
        )
        
        print()
        print("=" * 60)
        print("✅ 영상 제작 완료!")
        print("=" * 60)
        print(f"📁 저장 위치: {output_path}")
        print()
        
        # 정리
        audio.close()
        video.close()
        
        return output_path


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='책 리뷰 영상 제작')
    parser.add_argument('--audio', type=str, help='오디오 파일 경로')
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
        max_duration=args.max_duration
    )


if __name__ == "__main__":
    main()

