#!/usr/bin/env python3
"""
YouTube 영상 정보 추출 스크립트

YouTube URL에서 영상 ID를 추출하고 YouTube Data API를 사용하여
영상의 상세 정보를 가져옵니다.

사용법:
    python src/23_get_youtube_video_info.py --url "https://www.youtube.com/watch?v=VIDEO_ID"
    python src/23_get_youtube_video_info.py --url "URL1" --url "URL2"
    python src/23_get_youtube_video_info.py --urls-file urls.txt
"""

import os
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

try:
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False
    print("⚠️ googleapiclient이 설치되지 않았습니다. pip install google-api-python-client을 실행하세요.")

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
    TRANSCRIPT_API_AVAILABLE = True
except ImportError:
    TRANSCRIPT_API_AVAILABLE = False
    print("⚠️ youtube-transcript-api가 설치되지 않았습니다. pip install youtube-transcript-api을 실행하세요.")

load_dotenv()


def extract_video_id(url: str) -> Optional[str]:
    """YouTube URL에서 video ID 추출"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # URL 파싱 시도
    try:
        parsed = urlparse(url)
        if parsed.hostname in ['youtube.com', 'www.youtube.com', 'youtu.be', 'm.youtube.com']:
            if parsed.path == '/watch':
                params = parse_qs(parsed.query)
                if 'v' in params:
                    return params['v'][0]
            elif parsed.path.startswith('/'):
                # youtu.be/VIDEO_ID 형식
                video_id = parsed.path.lstrip('/')
                if len(video_id) == 11:
                    return video_id
    except Exception:
        pass
    
    return None


class YouTubeVideoInfoExtractor:
    """YouTube 영상 정보 추출 클래스"""
    
    def __init__(self):
        """초기화 및 인증"""
        if not YOUTUBE_API_AVAILABLE:
            raise ImportError("googleapiclient이 설치되지 않았습니다.")
        
        # 환경 변수에서 API 키 또는 OAuth 자격증명 가져오기
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        self.client_id = os.getenv("YOUTUBE_CLIENT_ID")
        self.client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
        self.refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
        
        self.youtube = None
        self._authenticate()
    
    def _authenticate(self):
        """YouTube API 인증"""
        try:
            # API 키가 있으면 API 키 사용 (읽기 전용)
            if self.api_key:
                self.youtube = build('youtube', 'v3', developerKey=self.api_key)
                print("✅ YouTube API 인증 성공 (API Key)")
                return
            
            # OAuth 자격증명이 있으면 OAuth 사용
            if self.client_id and self.client_secret and self.refresh_token:
                credentials = Credentials(
                    token=None,
                    refresh_token=self.refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    scopes=['https://www.googleapis.com/auth/youtube.readonly']
                )
                credentials.refresh(Request())
                self.youtube = build('youtube', 'v3', credentials=credentials)
                print("✅ YouTube API 인증 성공 (OAuth)")
                return
            
            raise ValueError("YouTube API 자격증명이 설정되지 않았습니다. .env 파일에 YOUTUBE_API_KEY 또는 OAuth 자격증명을 추가하세요.")
        
        except Exception as e:
            print(f"❌ 인증 실패: {e}")
            raise
    
    def get_video_info(self, video_id: str) -> Optional[Dict]:
        """영상 ID로 영상 정보 가져오기"""
        try:
            # 영상 상세 정보 가져오기
            response = self.youtube.videos().list(
                part='id,snippet,statistics,contentDetails,status',
                id=video_id
            ).execute()
            
            if not response.get('items'):
                print(f"⚠️ 영상을 찾을 수 없습니다: {video_id}")
                return None
            
            item = response['items'][0]
            snippet = item['snippet']
            statistics = item.get('statistics', {})
            content_details = item.get('contentDetails', {})
            status = item.get('status', {})
            
            # 영상 길이 파싱 (PT15M30S 형식)
            duration_str = content_details.get('duration', 'PT0S')
            duration_seconds = self._parse_duration(duration_str)
            
            video_info = {
                'video_id': video_id,
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'channel_id': snippet.get('channelId', ''),
                'channel_title': snippet.get('channelTitle', ''),
                'published_at': snippet.get('publishedAt', ''),
                'tags': snippet.get('tags', []),
                'category_id': snippet.get('categoryId', ''),
                'default_language': snippet.get('defaultLanguage', ''),
                'default_audio_language': snippet.get('defaultAudioLanguage', ''),
                'thumbnail': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                'duration_seconds': duration_seconds,
                'duration_formatted': self._format_duration(duration_seconds),
                'view_count': int(statistics.get('viewCount', 0)),
                'like_count': int(statistics.get('likeCount', 0)),
                'comment_count': int(statistics.get('commentCount', 0)),
                'favorite_count': int(statistics.get('favoriteCount', 0)),
                'privacy_status': status.get('privacyStatus', ''),
                'made_for_kids': status.get('madeForKids', False),
                'upload_status': status.get('uploadStatus', ''),
            }
            
            return video_info
        
        except Exception as e:
            print(f"❌ 영상 정보 가져오기 실패 ({video_id}): {e}")
            return None
    
    def get_captions_list(self, video_id: str) -> List[Dict]:
        """영상의 자막 목록 가져오기 (youtube-transcript-api 사용)"""
        if not TRANSCRIPT_API_AVAILABLE:
            print("   ⚠️ youtube-transcript-api가 설치되지 않았습니다.")
            return []
        
        try:
            yt_api = YouTubeTranscriptApi()
            transcript_list = yt_api.list(video_id)
            captions = []
            
            for transcript in transcript_list:
                captions.append({
                    'language': transcript.language,
                    'language_code': transcript.language_code,
                    'is_generated': transcript.is_generated,
                    'is_translatable': transcript.is_translatable,
                })
            
            return captions
        
        except TranscriptsDisabled:
            print(f"   ⚠️ 이 영상은 자막이 비활성화되어 있습니다: {video_id}")
            return []
        except NoTranscriptFound:
            print(f"   ⚠️ 자막을 찾을 수 없습니다: {video_id}")
            return []
        except VideoUnavailable:
            print(f"   ⚠️ 영상을 사용할 수 없습니다: {video_id}")
            return []
        except Exception as e:
            print(f"   ⚠️ 자막 목록 가져오기 실패 ({video_id}): {e}")
            return []
    
    def download_caption(self, video_id: str, language: str = 'ko', output_dir: str = 'output/captions', format: str = 'txt') -> Optional[str]:
        """자막 다운로드 (youtube-transcript-api 사용)"""
        if not TRANSCRIPT_API_AVAILABLE:
            print("   ⚠️ youtube-transcript-api가 설치되지 않았습니다.")
            return None
        
        try:
            yt_api = YouTubeTranscriptApi()
            
            # 자막 가져오기
            transcript_list = yt_api.list(video_id)
            
            # 지정된 언어로 자막 찾기
            transcript = None
            transcript_lang_code = language
            
            try:
                transcript = transcript_list.find_transcript([language])
                transcript_lang_code = transcript.language_code
            except:
                # 지정된 언어가 없으면 자동 번역 시도
                try:
                    # 영어 자막을 찾아서 번역
                    en_transcript = transcript_list.find_transcript(['en'])
                    transcript = en_transcript.translate(language)
                    transcript_lang_code = language
                    print(f"   ℹ️ 영어 자막을 {language}로 번역했습니다.")
                except:
                    # 영어도 없으면 첫 번째 사용 가능한 자막 사용
                    try:
                        transcript = transcript_list.find_generated_transcript([language])
                        transcript_lang_code = transcript.language_code
                    except:
                        pass
            
            if not transcript:
                print(f"   ⚠️ {language} 자막을 찾을 수 없습니다.")
                return None
            
            # 자막 데이터 가져오기
            transcript_data = transcript.fetch()
            
            # transcript_data가 리스트인지 확인
            if not isinstance(transcript_data, list):
                # 객체인 경우 리스트로 변환 시도
                try:
                    transcript_data = list(transcript_data)
                except:
                    print(f"   ⚠️ 자막 데이터 형식이 올바르지 않습니다.")
                    return None
            
            # 출력 디렉토리 생성
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 파일명 생성
            safe_video_id = re.sub(r'[^\w\s-]', '', video_id).strip()
            if format == 'srt':
                filename = f"{safe_video_id}_{transcript_lang_code}.srt"
                filepath = output_path / filename
                
                # SRT 형식으로 변환
                srt_content = self._convert_to_srt(transcript_data)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(srt_content)
            else:
                # TXT 형식 (기본값)
                filename = f"{safe_video_id}_{transcript_lang_code}.txt"
                filepath = output_path / filename
                
                # 텍스트만 추출 (각 항목이 dict인지 확인)
                text_lines = []
                for item in transcript_data:
                    if isinstance(item, dict):
                        text_lines.append(item.get('text', ''))
                    else:
                        # 객체인 경우 속성으로 접근 시도
                        try:
                            text_lines.append(getattr(item, 'text', ''))
                        except:
                            pass
                
                text_content = '\n'.join(text_lines)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(text_content)
            
            print(f"   💾 자막 저장: {filepath} ({len(transcript_data)}개 세그먼트)")
            return str(filepath)
        
        except TranscriptsDisabled:
            print(f"   ⚠️ 이 영상은 자막이 비활성화되어 있습니다: {video_id}")
            return None
        except NoTranscriptFound:
            print(f"   ⚠️ 자막을 찾을 수 없습니다: {video_id}")
            return None
        except VideoUnavailable:
            print(f"   ⚠️ 영상을 사용할 수 없습니다: {video_id}")
            return None
        except Exception as e:
            print(f"   ⚠️ 자막 다운로드 실패 ({video_id}): {e}")
            return None
    
    def _convert_to_srt(self, transcript_data: List) -> str:
        """자막 데이터를 SRT 형식으로 변환"""
        srt_lines = []
        for i, item in enumerate(transcript_data, 1):
            # dict인지 확인
            if isinstance(item, dict):
                start = item.get('start', 0)
                duration = item.get('duration', 0)
                text = item.get('text', '')
            else:
                # 객체인 경우 속성으로 접근
                try:
                    start = getattr(item, 'start', 0)
                    duration = getattr(item, 'duration', 0)
                    text = getattr(item, 'text', '')
                except:
                    continue
            
            end = start + duration
            
            # 시간 형식 변환 (초 -> HH:MM:SS,mmm)
            start_time = self._seconds_to_srt_time(start)
            end_time = self._seconds_to_srt_time(end)
            
            srt_lines.append(f"{i}")
            srt_lines.append(f"{start_time} --> {end_time}")
            srt_lines.append(text)
            srt_lines.append("")
        
        return '\n'.join(srt_lines)
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """초를 SRT 시간 형식 (HH:MM:SS,mmm)으로 변환"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def download_video_captions(self, video_id: str, language: str = None, output_dir: str = 'output/captions', format: str = 'txt') -> List[str]:
        """영상의 자막 다운로드 (언어 지정 가능)"""
        if not TRANSCRIPT_API_AVAILABLE:
            print("   ⚠️ youtube-transcript-api가 설치되지 않았습니다.")
            return []
        
        downloaded_files = []
        
        if language:
            # 특정 언어만 다운로드
            print(f"   📝 자막 다운로드 중: {language}")
            filepath = self.download_caption(video_id, language, output_dir, format)
            if filepath:
                downloaded_files.append(filepath)
        else:
            # 모든 사용 가능한 자막 다운로드
            captions_list = self.get_captions_list(video_id)
            if not captions_list:
                print(f"   ⚠️ 자막을 찾을 수 없습니다: {video_id}")
                return []
            
            for caption_info in captions_list:
                caption_lang = caption_info['language_code']
                print(f"   📝 자막 다운로드 중: {caption_lang}")
                filepath = self.download_caption(video_id, caption_lang, output_dir, format)
                if filepath:
                    downloaded_files.append(filepath)
        
        return downloaded_files
    
    def _parse_duration(self, duration_str: str) -> int:
        """ISO 8601 duration 형식 (PT15M30S)을 초로 변환"""
        # PT15M30S 형식 파싱
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)
        
        if not match:
            return 0
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds
    
    def _format_duration(self, seconds: int) -> str:
        """초를 HH:MM:SS 형식으로 변환"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def get_videos_from_urls(self, urls: List[str], download_captions: bool = False, caption_language: str = None, caption_output_dir: str = 'output/captions', caption_format: str = 'txt') -> List[Dict]:
        """여러 URL에서 영상 정보 가져오기"""
        video_infos = []
        seen_ids = set()
        
        for url in urls:
            video_id = extract_video_id(url)
            if not video_id:
                print(f"⚠️ URL에서 video ID를 추출할 수 없습니다: {url}")
                continue
            
            if video_id in seen_ids:
                print(f"⏭️ 중복된 영상 ID: {video_id}")
                continue
            
            seen_ids.add(video_id)
            print(f"📹 영상 정보 가져오는 중: {video_id}")
            
            video_info = self.get_video_info(video_id)
            if video_info:
                video_infos.append(video_info)
                print(f"   ✅ {video_info['title'][:60]}...")
                
                # 자막 다운로드
                if download_captions:
                    self.download_video_captions(video_id, caption_language, caption_output_dir, caption_format)
            else:
                print(f"   ❌ 영상 정보를 가져올 수 없습니다: {video_id}")
        
        return video_infos


def save_results(video_infos: List[Dict], output_file: Optional[str] = None):
    """결과를 JSON 파일로 저장"""
    if not output_file:
        output_file = "output/youtube_video_info.json"
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(video_infos, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 결과 저장: {output_path}")
    print(f"   총 {len(video_infos)}개 영상 정보")


def print_summary(video_infos: List[Dict]):
    """결과 요약 출력"""
    print("\n" + "="*60)
    print("📊 영상 정보 요약")
    print("="*60)
    
    for i, info in enumerate(video_infos, 1):
        print(f"\n[{i}] {info['title']}")
        print(f"   URL: {info['url']}")
        print(f"   채널: {info['channel_title']}")
        print(f"   길이: {info['duration_formatted']}")
        print(f"   조회수: {info['view_count']:,}")
        print(f"   좋아요: {info['like_count']:,}")
        print(f"   댓글: {info['comment_count']:,}")
        print(f"   공개 상태: {info['privacy_status']}")
        print(f"   업로드 날짜: {info['published_at']}")


def main():
    parser = argparse.ArgumentParser(
        description="YouTube 영상 정보 추출",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  # 단일 URL
  python src/23_get_youtube_video_info.py --url "https://www.youtube.com/watch?v=VIDEO_ID"
  
  # 여러 URL
  python src/23_get_youtube_video_info.py --url "URL1" --url "URL2"
  
  # 파일에서 URL 읽기
  python src/23_get_youtube_video_info.py --urls-file urls.txt
        """
    )
    
    parser.add_argument(
        '--url',
        action='append',
        dest='urls',
        help='YouTube URL (여러 번 사용 가능)'
    )
    
    parser.add_argument(
        '--urls-file',
        type=str,
        help='URL 목록이 있는 파일 경로 (한 줄에 하나씩)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='output/youtube_video_info.json',
        help='출력 JSON 파일 경로 (기본값: output/youtube_video_info.json)'
    )
    
    parser.add_argument(
        '--no-summary',
        action='store_true',
        help='요약 출력 생략'
    )
    
    parser.add_argument(
        '--download-captions',
        action='store_true',
        help='자막 다운로드'
    )
    
    parser.add_argument(
        '--caption-language',
        type=str,
        default=None,
        help='다운로드할 자막 언어 코드 (예: ko, en). 지정하지 않으면 모든 자막 다운로드'
    )
    
    parser.add_argument(
        '--caption-output-dir',
        type=str,
        default='output/captions',
        help='자막 저장 디렉토리 (기본값: output/captions)'
    )
    
    parser.add_argument(
        '--caption-format',
        type=str,
        choices=['txt', 'srt'],
        default='txt',
        help='자막 파일 형식 (기본값: txt)'
    )
    
    args = parser.parse_args()
    
    # URL 수집
    urls = []
    
    if args.urls:
        urls.extend(args.urls)
    
    if args.urls_file:
        urls_path = Path(args.urls_file)
        if urls_path.exists():
            with open(urls_path, 'r', encoding='utf-8') as f:
                file_urls = [line.strip() for line in f if line.strip()]
                urls.extend(file_urls)
            print(f"📄 파일에서 {len(file_urls)}개 URL 읽기: {args.urls_file}")
        else:
            print(f"❌ 파일을 찾을 수 없습니다: {args.urls_file}")
            return
    
    if not urls:
        print("❌ URL이 제공되지 않았습니다. --url 또는 --urls-file 옵션을 사용하세요.")
        return
    
    print(f"🔍 총 {len(urls)}개 URL 처리 중...\n")
    
    # 영상 정보 추출
    try:
        extractor = YouTubeVideoInfoExtractor()
        video_infos = extractor.get_videos_from_urls(
            urls,
            download_captions=args.download_captions,
            caption_language=args.caption_language,
            caption_output_dir=args.caption_output_dir,
            caption_format=args.caption_format
        )
        
        if not video_infos:
            print("\n❌ 영상 정보를 가져올 수 없습니다.")
            return
        
        # 결과 저장
        save_results(video_infos, args.output)
        
        # 요약 출력
        if not args.no_summary:
            print_summary(video_infos)
        
        print("\n✅ 완료!")
    
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

