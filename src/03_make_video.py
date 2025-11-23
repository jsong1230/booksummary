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
    from moviepy import ImageClip, AudioFileClip, CompositeVideoClip, TextClip, ColorClip, concatenate_videoclips
    from moviepy.video.fx import FadeIn, FadeOut, CrossFadeIn, CrossFadeOut
    MOVIEPY_AVAILABLE = True
except ImportError as e:
    MOVIEPY_AVAILABLE = False
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
        print(f"🎵 오디오 로드 중: {audio_path}")
        audio = AudioFileClip(audio_path)
        print(f"   길이: {audio.duration:.2f}초")
        return audio
    
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
        Ken Burns 효과가 적용된 이미지 클립 생성 (간단한 버전)
        
        Args:
            image_path: 이미지 경로
            duration: 클립 길이 (초)
            effect_type: 효과 타입 ("zoom_in", "zoom_out", "static")
            start_scale: 시작 스케일
            end_scale: 끝 스케일
            pan_direction: 패닝 방향 (현재 미구현)
        """
        # 이미지 로드
        clip = ImageClip(image_path, duration=duration)
        
        # 해상도에 맞게 리사이즈
        try:
            clip = clip.resized(newsize=self.resolution)
        except:
            # 대체 방법
            from PIL import Image
            import numpy as np
            img = Image.open(image_path)
            img = img.resize(self.resolution, Image.Resampling.LANCZOS)
            clip = ImageClip(np.array(img), duration=duration)
        
        return clip
    
    def create_image_sequence(
        self,
        image_paths: List[str],
        total_duration: float,
        fade_duration: float = 1.0
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
        duration_per_image = total_duration / num_images
        
        clips = []
        effect_types = ["zoom_in", "zoom_out", "pan"]
        pan_directions = ["left", "right", "up", "down"]
        
        for i, image_path in enumerate(image_paths):
            # 랜덤 효과 선택
            effect_type = random.choice(effect_types)
            pan_direction = random.choice(pan_directions) if effect_type == "pan" else None
            
            # Ken Burns 효과 적용
            clip = self.create_image_clip_with_ken_burns(
                image_path=image_path,
                duration=duration_per_image,
                effect_type=effect_type,
                start_scale=1.0,
                end_scale=1.15 + random.uniform(0, 0.1),
                pan_direction=pan_direction
            )
            
            # 페이드 효과 추가
            if i == 0:
                # 첫 번째: 페이드인
                clip = clip.with_effects([FadeIn(fade_duration)])
            elif i == len(image_paths) - 1:
                # 마지막: 페이드아웃
                clip = clip.with_effects([FadeOut(fade_duration)])
            else:
                # 중간: 크로스페이드
                clip = clip.with_effects([CrossFadeIn(fade_duration)])
            
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
        language: str = "ko"
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
        print()
        
        # 2. 이미지 경로 수집
        image_dir_path = Path(image_dir)
        cover_path = image_dir_path / "cover.jpg"
        mood_images = sorted(image_dir_path.glob("mood_*.jpg"))
        
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
            raise ValueError(f"이미지를 찾을 수 없습니다: {image_dir}")
        
        print(f"\n총 {len(image_paths)}개의 이미지 사용")
        print()
        
        # 3. 이미지 시퀀스 생성
        print("🖼️ 이미지 시퀀스 생성 중...")
        image_clips = self.create_image_sequence(
            image_paths=image_paths,
            total_duration=audio_duration,
            fade_duration=1.0
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
            bitrate='8000k',
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
        safe_title = "".join(c for c in args.book_title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')
        args.image_dir = f"assets/images/{safe_title}"
        print(f"🖼️ 이미지 디렉토리: {args.image_dir}")
    
    if args.output is None:
        safe_title = "".join(c for c in args.book_title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')
        args.output = f"output/{safe_title}_review.mp4"
        print(f"📁 출력 파일: {args.output}")
    
    print()
    
    # 영상 제작
    maker = VideoMaker(resolution=(1920, 1080), fps=30)
    maker.create_video(
        audio_path=args.audio,
        image_dir=args.image_dir,
        output_path=args.output,
        add_subtitles_flag=args.subtitles,
        language=args.language
    )


if __name__ == "__main__":
    main()

