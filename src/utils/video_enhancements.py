#!/usr/bin/env python3
"""
영상 시각화 개선 유틸리티

정지 화면 문제를 해결하기 위한 시각적 요소 추가:
1. 동적 자막 (Kinetic Typography)
2. 관련 푸티지(Footage)
3. 파형(Waveform)
"""

from typing import Optional, List, Dict
from pathlib import Path
import numpy as np


def extract_keywords_from_text(text: str, language: str = "ko", max_keywords: int = 10) -> List[str]:
    """
    텍스트에서 핵심 키워드 추출
    
    Args:
        text: 텍스트
        language: 언어 ('ko' 또는 'en')
        max_keywords: 최대 키워드 개수
        
    Returns:
        키워드 리스트
    """
    import re
    
    # 마크다운 제거
    text_clean = re.sub(r'\[.*?\]', '', text)  # [HOOK], [SUMMARY] 등 제거
    text_clean = re.sub(r'#+', '', text_clean)  # 헤더 제거
    text_clean = re.sub(r'\*\*', '', text_clean)  # 볼드 제거
    
    # 간단한 키워드 추출 (실제로는 더 정교한 NLP가 필요할 수 있음)
    if language == "ko":
        # 한글 키워드 추출 (명사 위주)
        # 2-5글자 한글 단어 (너무 짧거나 긴 단어 제외)
        pattern = r'[가-힣]{2,5}'
        keywords = re.findall(pattern, text_clean)
        
        # 불용어 제거
        stopwords = {'것은', '것을', '것이', '것을', '것도', '것만', '것으로', '것이다', 
                    '그것', '이것', '저것', '그리고', '또한', '또는', '그러나', '하지만',
                    '때문', '위해', '통해', '대해', '관해', '대한', '있는', '없는',
                    '하는', '되는', '있는', '없는', '같은', '다른', '모든', '각각'}
        keywords = [kw for kw in keywords if kw not in stopwords]
    else:
        # 영어 키워드 추출 (대문자로 시작하는 단어 또는 중요한 단어)
        words = re.findall(r'\b[A-Z][a-z]+\b|\b[a-z]{4,}\b', text_clean)
        keywords = [w for w in words if len(w) >= 4]
        
        # 불용어 제거
        stopwords = {'this', 'that', 'with', 'from', 'have', 'been', 'will', 'would',
                    'could', 'should', 'about', 'their', 'there', 'these', 'those',
                    'which', 'where', 'when', 'what', 'they', 'them', 'then', 'than'}
        keywords = [kw.lower() for kw in keywords if kw.lower() not in stopwords]
    
    # 빈도수 기반으로 정렬
    from collections import Counter
    keyword_counts = Counter(keywords)
    
    # 가장 빈도가 높은 키워드 선택 (최소 2회 이상 등장)
    top_keywords = [word for word, count in keyword_counts.most_common(max_keywords * 2) 
                   if count >= 2][:max_keywords]
    
    return top_keywords


def find_keyword_timings_in_audio(
    keywords: List[str],
    audio_path: str,
    language: str = "ko"
) -> List[Dict]:
    """
    오디오에서 키워드가 언급되는 시간 찾기 (Whisper 활용)
    
    Args:
        keywords: 키워드 리스트
        audio_path: 오디오 파일 경로
        language: 언어
        
    Returns:
        키워드 타이밍 리스트 [{"keyword": str, "start": float, "end": float}, ...]
    """
    try:
        import whisper
    except ImportError:
        return []
    
    try:
        # Whisper로 오디오 분석
        model = whisper.load_model("base")
        result = model.transcribe(
            audio_path,
            language=language,
            word_timestamps=True
        )
        
        if not result or "segments" not in result:
            return []
        
        keyword_timings = []
        
        # 각 키워드가 언급되는 시간 찾기
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            for segment in result.get("segments", []):
                if "words" in segment:
                    for word_info in segment["words"]:
                        word_text = word_info["word"].strip().lower()
                        # 키워드가 단어에 포함되어 있는지 확인
                        if keyword_lower in word_text or word_text in keyword_lower:
                            keyword_timings.append({
                                "keyword": keyword,
                                "start": word_info["start"],
                                "end": word_info["end"]
                            })
                            break  # 첫 번째 매칭만 사용
                    if any(t["keyword"] == keyword for t in keyword_timings):
                        break  # 이미 찾았으면 다음 키워드로
        
        return keyword_timings
        
    except Exception as e:
        print(f"⚠️ 키워드 타이밍 분석 실패: {e}")
        return []


def create_kinetic_typography_clip(
    keyword: str,
    start_time: float,
    duration: float = 2.0,
    resolution: tuple = (1920, 1080),
    font_size: int = 150,  # 더 큼직하게
    language: str = "ko",
    effect: str = "pop"  # 'pop', 'fade', 'slide'
):
    """
    동적 자막(Kinetic Typography) 클립 생성
    
    핵심 키워드가 나올 때마다 화면에 텍스트가 큼직하게 박히는 효과
    
    Args:
        keyword: 키워드 텍스트
        start_time: 시작 시간 (초)
        duration: 지속 시간 (초)
        resolution: 해상도
        font_size: 폰트 크기 (기본값: 150, 더 큼직하게)
        language: 언어
        effect: 효과 타입 ('pop', 'fade', 'slide')
        
    Returns:
        TextClip 또는 None (MoviePy가 없는 경우)
    """
    try:
        from moviepy.editor import TextClip
        
        # 키워드 텍스트 클립 생성 (더 큼직하고 눈에 띄게)
        text_clip = TextClip(
            keyword,
            fontsize=font_size,
            color='white',
            font='Arial-Bold' if language == "en" else 'NanumGothic-Bold',
            stroke_color='black',
            stroke_width=6,  # 더 두꺼운 테두리
            method='caption',
            size=(resolution[0] * 0.8, None)  # 화면 너비의 80% 사용
        )
        
        # 효과에 따라 다른 애니메이션 적용
        if effect == "pop":
            # 팝 효과: 크기가 커졌다 작아지는 효과
            try:
                from moviepy.video.fx.all import resize
                # 시작 시 크게, 중간에 정상 크기, 끝에 작게
                def make_frame(t):
                    if t < duration * 0.2:
                        scale = 1.0 + (t / (duration * 0.2)) * 0.3  # 1.0 -> 1.3
                    elif t < duration * 0.8:
                        scale = 1.3 - ((t - duration * 0.2) / (duration * 0.6)) * 0.1  # 1.3 -> 1.2
                    else:
                        scale = 1.2 - ((t - duration * 0.8) / (duration * 0.2)) * 0.2  # 1.2 -> 1.0
                    return resize(text_clip, scale).get_frame(t)
                # 실제로는 CompositeVideoClip으로 처리해야 함
            except:
                pass
        
        # 화면 중앙에 배치
        text_clip = text_clip.set_position('center').set_duration(duration).set_start(start_time)
        
        # 페이드 인/아웃 효과
        try:
            from moviepy.video.fx.all import fadein, fadeout
            fade_duration = min(0.4, duration / 4)  # 더 부드러운 페이드
            text_clip = text_clip.fx(fadein, fade_duration).fx(fadeout, fade_duration)
        except:
            pass
        
        return text_clip
        
    except ImportError:
        return None
    except Exception as e:
        print(f"⚠️ 동적 자막 생성 실패: {e}")
        return None


def create_waveform_visualization(
    audio_path: str,
    duration: float,
    resolution: tuple = (1920, 1080),
    position: str = "bottom",
    height: int = 100,
    color: str = "cyan"
):
    """
    오디오 파형 시각화 생성
    
    Args:
        audio_path: 오디오 파일 경로
        duration: 길이 (초)
        resolution: 해상도
        position: 위치 ('bottom', 'top', 'center')
        height: 파형 높이 (픽셀)
        color: 파형 색상
        
    Returns:
        VideoClip 또는 None
    """
    try:
        from moviepy.editor import AudioFileClip, VideoClip, ColorClip, CompositeVideoClip
        import numpy as np
        from PIL import Image, ImageDraw
        
        # 오디오 로드
        audio = AudioFileClip(audio_path)
        audio_fps = audio.fps  # 오디오 샘플레이트 저장
        fps = 30  # 비디오 프레임레이트
        
        # 오디오를 numpy array로 변환 (한 번만 로드)
        try:
            audio_array = audio.to_soundarray(fps=audio_fps)
            # 스테레오인 경우 모노로 변환
            if len(audio_array.shape) > 1:
                audio_array = audio_array.mean(axis=1)
        except Exception as e:
            print(f"⚠️ 오디오 배열 변환 실패, 더미 데이터 사용: {e}")
            # 폴백: 간단한 더미 데이터
            audio_array = np.random.rand(int(audio_fps * duration)) * 0.1
        
        # 오디오 리소스 정리
        audio.close()
        
        # 파형을 그리는 함수
        def make_waveform_frame(t):
            """특정 시간의 파형 프레임 생성"""
            try:
                # 해당 시간의 오디오 샘플 인덱스 계산
                sample_idx = int(t * audio_fps)
                if sample_idx >= len(audio_array):
                    sample_idx = len(audio_array) - 1
                
                # 파형 이미지 생성
                img = Image.new('RGBA', (resolution[0], height), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                
                # 샘플을 시각화할 바 개수
                num_bars = 60
                bar_width = resolution[0] // num_bars
                
                # 주변 샘플을 분석하여 파형 생성 (시간에 따라 변화)
                window_size = max(100, len(audio_array) // num_bars)
                
                for i in range(num_bars):
                    # 각 바에 해당하는 샘플 범위 (시간에 따라 스크롤)
                    # 실시간 파형 효과: 현재 시간 기준으로 샘플 선택
                    time_offset = int(t * 10) % window_size  # 스크롤 효과
                    start_idx = max(0, sample_idx - window_size // 2 + (i - num_bars // 2) * window_size // num_bars + time_offset)
                    end_idx = min(len(audio_array), start_idx + window_size // num_bars)
                    
                    if start_idx < len(audio_array) and end_idx > start_idx:
                        chunk = audio_array[start_idx:end_idx]
                        amplitude = np.abs(chunk).mean() if len(chunk) > 0 else 0.0
                    else:
                        amplitude = 0.0
                    
                    # 진폭을 높이로 변환 (0~height)
                    bar_height = int(amplitude * height * 3)  # 증폭
                    bar_height = min(bar_height, height)
                    
                    # 바 그리기 (중앙 기준, 대칭)
                    x1 = i * bar_width
                    x2 = (i + 1) * bar_width
                    center_y = height // 2
                    y1 = center_y - bar_height // 2
                    y2 = center_y + bar_height // 2
                    
                    # 색상 설정
                    if color == "cyan":
                        fill_color = (0, 255, 255, 180)  # 시안색, 반투명
                    elif color == "white":
                        fill_color = (255, 255, 255, 180)
                    else:
                        fill_color = (255, 255, 255, 180)
                    
                    if bar_height > 2:  # 최소 높이 이상일 때만 그리기
                        draw.rectangle([x1, y1, x2, y2], fill=fill_color)
                
                # PIL Image를 numpy array로 변환
                img_array = np.array(img)
                return img_array
                
            except Exception as e:
                # 오류 시 빈 프레임 반환
                return np.zeros((height, resolution[0], 4), dtype=np.uint8)
        
        # VideoClip 생성
        waveform_clip = VideoClip(make_waveform_frame, duration=duration)
        waveform_clip = waveform_clip.set_fps(fps)
        
        # 위치 설정
        if position == "bottom":
            y_pos = resolution[1] - height - 20  # 하단에서 20px 위
        elif position == "top":
            y_pos = 20  # 상단에서 20px 아래
        else:  # center
            y_pos = (resolution[1] - height) // 2
        
        waveform_clip = waveform_clip.set_position(('center', y_pos))
        
        return waveform_clip
        
    except ImportError as e:
        print(f"⚠️ 파형 시각화에 필요한 라이브러리가 없습니다: {e}")
        return None
    except Exception as e:
        print(f"⚠️ 파형 시각화 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


def search_pexels_video(keyword: str, language: str = "ko", max_results: int = 5, api_key: Optional[str] = None) -> List[Dict]:
    """
    Pexels에서 관련 푸티지 검색
    
    Args:
        keyword: 검색 키워드
        language: 언어
        max_results: 최대 결과 개수
        api_key: Pexels API 키 (없으면 환경 변수에서 가져옴)
        
    Returns:
        비디오 정보 리스트 [{"url": str, "duration": float, "path": str}, ...]
    """
    import os
    from pathlib import Path
    
    # API 키 가져오기
    if not api_key:
        api_key = os.getenv("PEXELS_API_KEY")
    
    if not api_key:
        print("⚠️ Pexels API 키가 없습니다. 환경 변수 PEXELS_API_KEY를 설정하세요.")
        return []
    
    try:
        import requests
        
        # Pexels API로 비디오 검색
        url = "https://api.pexels.com/videos/search"
        headers = {
            "Authorization": api_key
        }
        params = {
            "query": keyword,
            "per_page": max_results,
            "orientation": "landscape"  # 가로 영상만
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        videos = []
        
        for video_info in data.get("videos", [])[:max_results]:
            # 가장 높은 품질의 비디오 파일 찾기
            video_files = video_info.get("video_files", [])
            if not video_files:
                continue
            
            # HD 이상 품질 우선 선택
            best_video = None
            for vf in video_files:
                if vf.get("quality") in ["hd", "sd"]:
                    if not best_video or vf.get("width", 0) > best_video.get("width", 0):
                        best_video = vf
            
            if not best_video:
                best_video = video_files[0]  # 폴백
            
            videos.append({
                "url": best_video.get("link"),
                "duration": video_info.get("duration", 0),
                "width": best_video.get("width"),
                "height": best_video.get("height"),
                "id": video_info.get("id")
            })
        
        return videos
        
    except ImportError:
        print("⚠️ requests 라이브러리가 필요합니다. pip install requests")
        return []
    except Exception as e:
        print(f"⚠️ Pexels 비디오 검색 실패: {e}")
        return []


def download_pexels_video(video_url: str, output_path: Path, timeout: int = 60) -> bool:
    """
    Pexels 비디오 다운로드
    
    Args:
        video_url: 비디오 URL
        output_path: 저장 경로
        timeout: 타임아웃 (초)
        
    Returns:
        성공 여부
    """
    try:
        import requests
        
        response = requests.get(video_url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True
        
    except Exception as e:
        print(f"⚠️ 비디오 다운로드 실패: {e}")
        return False


def enhance_video_with_visuals(
    video_clip,
    audio_path: Optional[str] = None,
    text: Optional[str] = None,
    language: str = "ko",
    enable_kinetic_typography: bool = True,
    enable_waveform: bool = True,
    enable_footage: bool = False
):
    """
    영상에 시각적 요소 추가
    
    Args:
        video_clip: 원본 비디오 클립
        audio_path: 오디오 파일 경로 (파형 생성용, 동적 자막 타이밍 분석용)
        text: 텍스트 (동적 자막용)
        language: 언어
        enable_kinetic_typography: 동적 자막 활성화
        enable_waveform: 파형 활성화
        enable_footage: 푸티지 활성화
        
    Returns:
        향상된 비디오 클립
    """
    from moviepy.editor import CompositeVideoClip
    
    enhanced_clips = [video_clip]
    
    # 동적 자막 추가 (개선: Whisper를 활용한 정확한 타이밍)
    if enable_kinetic_typography and text and audio_path:
        try:
            keywords = extract_keywords_from_text(text, language, max_keywords=8)
            
            if keywords:
                # Whisper를 사용하여 키워드가 실제로 언급되는 시간 찾기
                keyword_timings = find_keyword_timings_in_audio(
                    keywords=keywords[:5],  # 상위 5개만 사용
                    audio_path=audio_path,
                    language=language
                )
                
                if keyword_timings:
                    # 실제 타이밍을 사용하여 동적 자막 생성
                    for timing_info in keyword_timings[:4]:  # 최대 4개만 사용
                        kinetic_clip = create_kinetic_typography_clip(
                            keyword=timing_info["keyword"],
                            start_time=timing_info["start"],
                            duration=2.5,  # 키워드 언급 후 2.5초 표시
                            language=language,
                            effect="pop"  # 팝 효과 사용
                        )
                        if kinetic_clip:
                            enhanced_clips.append(kinetic_clip)
                else:
                    # Whisper 타이밍을 찾지 못한 경우 폴백: 균등 분배
                    video_duration = video_clip.duration
                    keyword_interval = video_duration / (len(keywords) + 1)
                    
                    for i, keyword in enumerate(keywords[:3]):  # 처음 3개만 사용
                        start_time = keyword_interval * (i + 1)
                        kinetic_clip = create_kinetic_typography_clip(
                            keyword=keyword,
                            start_time=start_time,
                            duration=2.0,
                            language=language
                        )
                        if kinetic_clip:
                            enhanced_clips.append(kinetic_clip)
        except Exception as e:
            print(f"⚠️ 동적 자막 추가 실패: {e}")
            import traceback
            traceback.print_exc()
    
    # 파형 추가 (화면 하단에 표시)
    if enable_waveform and audio_path:
        try:
            waveform_clip = create_waveform_visualization(
                audio_path=audio_path,
                duration=video_clip.duration,
                resolution=video_clip.size if hasattr(video_clip, 'size') else (1920, 1080),
                position="bottom",
                height=80,  # 파형 높이
                color="cyan"  # 시안색 파형
            )
            if waveform_clip:
                enhanced_clips.append(waveform_clip)
        except Exception as e:
            print(f"⚠️ 파형 추가 실패: {e}")
            import traceback
            traceback.print_exc()
    
    # 푸티지 추가 (관련 비디오 클립 삽입)
    if enable_footage and text and audio_path:
        try:
            from moviepy.editor import VideoFileClip
            from pathlib import Path
            import tempfile
            
            # 텍스트에서 검색 키워드 추출
            search_keywords = extract_keywords_from_text(text, language, max_keywords=3)
            
            if search_keywords:
                # 첫 번째 키워드로 Pexels 검색
                keyword = search_keywords[0]
                pexels_videos = search_pexels_video(keyword, language, max_results=3)
                
                if pexels_videos:
                    # 임시 디렉토리에 비디오 다운로드
                    temp_dir = Path(tempfile.gettempdir()) / "pexels_videos"
                    temp_dir.mkdir(parents=True, exist_ok=True)
                    
                    # 첫 번째 비디오 다운로드 및 삽입
                    video_info = pexels_videos[0]
                    video_path = temp_dir / f"pexels_{video_info['id']}.mp4"
                    
                    if download_pexels_video(video_info["url"], video_path):
                        # 비디오 클립 로드 및 리사이즈
                        footage_clip = VideoFileClip(str(video_path))
                        
                        # 영상 길이에 맞춰 자르기 (너무 길면)
                        if footage_clip.duration > video_clip.duration * 0.3:
                            footage_clip = footage_clip.subclip(0, video_clip.duration * 0.3)
                        
                        # 해상도 맞추기
                        if hasattr(video_clip, 'size'):
                            footage_clip = footage_clip.resize(video_clip.size)
                        
                        # 영상 중간에 삽입 (예: 30% 지점)
                        insert_time = video_clip.duration * 0.3
                        footage_clip = footage_clip.set_start(insert_time)
                        
                        enhanced_clips.append(footage_clip)
        except Exception as e:
            print(f"⚠️ 푸티지 추가 실패: {e}")
            import traceback
            traceback.print_exc()
    
    if len(enhanced_clips) > 1:
        try:
            return CompositeVideoClip(enhanced_clips)
        except Exception as e:
            print(f"⚠️ 시각적 요소 합성 실패: {e}")
            import traceback
            traceback.print_exc()
            return video_clip
    
    return video_clip
