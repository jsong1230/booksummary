#!/usr/bin/env python3
"""
유튜브 영상에서 자막을 가져와서 각각 따로 저장하는 스크립트

일당백 채널의 유튜브 영상(Part 1, Part 2)에서 자막을 가져와서
각각 별도의 텍스트 파일로 저장합니다.

우선순위:
  1. youtube-transcript-api (쿠키 지원)
  2. yt-dlp 폴백 (IP 차단 시 자동 전환)
"""

import argparse
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional
from http.cookiejar import MozillaCookieJar
import requests

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.file_utils import get_standard_safe_title
from src.utils.logger import setup_logger

# 로거 설정
logger = setup_logger(__name__)

try:
    from youtube_transcript_api import (
        YouTubeTranscriptApi,
        TranscriptsDisabled,
        NoTranscriptFound,
        VideoUnavailable
    )
except ImportError:
    logger.error("❌ youtube-transcript-api 패키지가 설치되지 않았습니다.")
    logger.error("다음 명령어로 설치해주세요: pip install youtube-transcript-api")
    sys.exit(1)


def extract_video_id(url: str) -> Optional[str]:
    """
    유튜브 URL에서 비디오 ID 추출
    
    Args:
        url: 유튜브 URL (다양한 형식 지원)
        
    Returns:
        비디오 ID 또는 None
    """
    import re
    
    # 다양한 유튜브 URL 패턴 지원
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # URL이 아닌 경우 비디오 ID로 간주
    if len(url) == 11 and url.replace('-', '').replace('_', '').isalnum():
        return url
    
    return None


def load_cookies_into_session(cookies_path: Optional[Path] = None) -> Optional[requests.Session]:
    """
    쿠키 파일을 로드하여 requests.Session에 추가
    
    Args:
        cookies_path: 쿠키 파일 경로 (기본값: 스크립트 폴더의 cookies.txt)
        
    Returns:
        쿠키가 로드된 requests.Session 또는 None
    """
    if cookies_path is None:
        # 기본값: 스크립트 폴더의 cookies.txt
        script_dir = Path(__file__).parent
        cookies_path = script_dir / 'cookies.txt'
    
    if not cookies_path.exists():
        logger.debug(f"쿠키 파일을 찾을 수 없습니다: {cookies_path}")
        return None
    
    try:
        # Netscape 쿠키 형식 파일 로드
        cookie_jar = MozillaCookieJar(str(cookies_path))
        cookie_jar.load(ignore_discard=True, ignore_expires=True)
        
        # requests.Session 생성 및 쿠키 추가
        session = requests.Session()
        
        # User-Agent 헤더 추가 (브라우저처럼 보이게)
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # 쿠키를 개별적으로 추가
        for cookie in cookie_jar:
            session.cookies.set(
                name=cookie.name,
                value=cookie.value,
                domain=cookie.domain,
                path=cookie.path,
                secure=cookie.secure
            )
        
        logger.info(f"🍪 쿠키 파일을 로드했습니다: {cookies_path} ({len(cookie_jar)}개 쿠키)")
        return session
    except Exception as e:
        logger.warning(f"⚠️ 쿠키 파일 로드 실패: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return None


def fetch_transcript_ytdlp(video_id: str, cookies_path: Optional[Path] = None) -> Optional[str]:
    """
    yt-dlp를 사용하여 자막 가져오기 (IP 차단 폴백)

    Args:
        video_id: 유튜브 비디오 ID
        cookies_path: 쿠키 파일 경로

    Returns:
        자막 텍스트 또는 None
    """
    logger.info(f"🔄 yt-dlp 폴백 시도: {video_id}")

    script_dir = Path(__file__).parent
    default_cookies = script_dir / 'cookies.txt'
    cookie_file = cookies_path if cookies_path and Path(cookies_path).exists() else (
        default_cookies if default_cookies.exists() else None
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        out_template = str(Path(tmpdir) / 'sub')
        cmd = ['yt-dlp', '--write-auto-sub', '--skip-download', '--sub-lang', 'ko',
               '-o', out_template,
               f'https://www.youtube.com/watch?v={video_id}']

        if cookie_file:
            cmd += ['--cookies', str(cookie_file)]
            logger.info(f"   🍪 쿠키 파일 사용: {cookie_file}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                logger.warning(f"   ⚠️ yt-dlp 실패: {result.stderr[-300:]}")
                return None

            # VTT 파일 찾기
            vtt_files = list(Path(tmpdir).glob('*.vtt'))
            if not vtt_files:
                logger.warning("   ⚠️ yt-dlp: VTT 파일을 찾을 수 없습니다.")
                return None

            vtt_path = vtt_files[0]
            with open(vtt_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # VTT → 텍스트 변환 (타임스탬프·중복 제거)
            lines = content.split('\n')
            text_lines = []
            prev = ''
            for line in lines:
                line = line.strip()
                if re.match(r'\d{2}:\d{2}:\d{2}', line):
                    continue
                if line.startswith(('WEBVTT', 'Kind:', 'Language:')):
                    continue
                line = re.sub(r'<[^>]+>', '', line)
                if not line or line == prev:
                    continue
                text_lines.append(line)
                prev = line

            text = '\n'.join(text_lines)
            logger.info(f"   ✅ yt-dlp 성공: {len(text)}자")
            return text

        except subprocess.TimeoutExpired:
            logger.warning("   ⚠️ yt-dlp 타임아웃")
            return None
        except FileNotFoundError:
            logger.warning("   ⚠️ yt-dlp가 설치되지 않았습니다.")
            return None
        except Exception as e:
            logger.warning(f"   ⚠️ yt-dlp 오류: {e}")
            return None


def fetch_transcript(video_id: str, languages: list = ['ko', 'en'], max_retries: int = 3, cookies_path: Optional[str] = None) -> Optional[list]:
    """
    유튜브 영상에서 자막 가져오기 (재시도 로직 포함, 쿠키 지원)
    
    Args:
        video_id: 유튜브 비디오 ID
        languages: 우선순위 언어 리스트 (기본값: ['ko', 'en'])
        max_retries: 최대 재시도 횟수 (기본값: 3)
        cookies_path: 쿠키 파일 경로 (선택사항)
        
    Returns:
        자막 리스트 또는 None
    """
    # 쿠키 파일 로드
    http_session = load_cookies_into_session(Path(cookies_path) if cookies_path else None)
    
    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1:
                wait_time = attempt * 5  # 5초, 10초, 15초 대기
                logger.info(f"⏳ {wait_time}초 대기 후 재시도 중... (시도 {attempt}/{max_retries})")
                time.sleep(wait_time)
            
            logger.info(f"📹 비디오 ID {video_id}에서 자막 가져오는 중... (시도 {attempt}/{max_retries})")
            
            # YouTubeTranscriptApi 인스턴스 생성 (쿠키가 있으면 http_client로 전달)
            if http_session:
                yt_api = YouTubeTranscriptApi(http_client=http_session)
            else:
                yt_api = YouTubeTranscriptApi()
            
            # 자동으로 사용 가능한 자막 찾기
            transcript_list = yt_api.list(video_id)
            
            # 우선순위에 따라 자막 찾기
            transcript = None
            for lang in languages:
                try:
                    transcript = transcript_list.find_transcript([lang])
                    logger.info(f"✅ {lang} 자막을 찾았습니다.")
                    break
                except:
                    continue
            
            # 자동 번역 시도 (한국어가 없으면 영어 자막을 한국어로 번역)
            if transcript is None:
                try:
                    # 먼저 영어 자막을 찾고 한국어로 번역
                    en_transcript = transcript_list.find_transcript(['en'])
                    transcript = en_transcript.translate('ko')
                    logger.info("✅ 영어 자막을 한국어로 번역했습니다.")
                except:
                    pass
            
            # 영어 자막 시도
            if transcript is None:
                try:
                    transcript = transcript_list.find_transcript(['en'])
                    logger.info("✅ 영어 자막을 찾았습니다.")
                except:
                    pass
            
            # 사용 가능한 자막 중 첫 번째 자막 사용
            if transcript is None:
                try:
                    transcript = transcript_list.find_manually_created_transcript(['ko', 'en'])
                    logger.info("✅ 수동 생성 자막을 찾았습니다.")
                except:
                    try:
                        transcript = transcript_list.find_generated_transcript(['ko', 'en'])
                        logger.info("✅ 자동 생성 자막을 찾았습니다.")
                    except:
                        pass
            
            if transcript is None:
                logger.error(f"❌ 사용 가능한 자막을 찾을 수 없습니다.")
                return None
            
            # 자막 데이터 가져오기
            transcript_data = transcript.fetch()
            logger.info(f"✅ 총 {len(transcript_data)}개의 자막 세그먼트를 가져왔습니다.")
            
            return transcript_data
            
        except TranscriptsDisabled:
            logger.error(f"❌ 이 영상은 자막이 비활성화되어 있습니다.")
            return None
        except NoTranscriptFound:
            logger.error(f"❌ 이 영상에서 자막을 찾을 수 없습니다.")
            return None
        except VideoUnavailable:
            logger.error(f"❌ 이 영상은 사용할 수 없거나 삭제되었습니다.")
            return None
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            logger.debug(f"에러 타입: {error_type}, 메시지: {error_msg}")
            
            if "IP" in error_msg or "blocked" in error_msg.lower() or "blocking" in error_msg.lower() or "RequestBlocked" in error_type:
                if attempt < max_retries:
                    logger.warning(f"⚠️ IP 차단으로 인한 오류 발생. 재시도 예정... (에러: {error_type})")
                    continue
                else:
                    logger.error(f"❌ IP 차단으로 인해 자막을 가져올 수 없습니다. (최대 재시도 횟수 도달)")
                    logger.error(f"   에러 타입: {error_type}")
                    logger.error(f"   에러 메시지: {error_msg}")
                    logger.error(f"💡 해결 방법:")
                    logger.error(f"   1. 잠시 후 다시 시도해주세요.")
                    logger.error(f"   2. VPN을 사용하거나 다른 네트워크에서 시도해주세요.")
                    logger.error(f"   3. YouTube에서 직접 자막을 다운로드하세요.")
                    if http_session:
                        logger.error(f"   4. 쿠키 파일이 있지만 여전히 차단되었습니다. 쿠키를 다시 다운로드해보세요.")
                    return None
            else:
                logger.error(f"❌ 자막을 가져오는 중 오류 발생: {error_type}: {error_msg}")
                if attempt < max_retries:
                    continue
                else:
                    import traceback
                    logger.debug(traceback.format_exc())
                    return None
    
    return None


def format_transcript(transcript_data: list) -> str:
    """
    자막 데이터를 텍스트로 포맷팅
    
    Args:
        transcript_data: 자막 데이터 리스트 (FetchedTranscriptSnippet 객체 리스트)
        
    Returns:
        포맷팅된 텍스트
    """
    text_lines = []
    for entry in transcript_data:
        # FetchedTranscriptSnippet 객체는 text 속성을 가짐
        if hasattr(entry, 'text'):
            text = entry.text.strip()
        elif isinstance(entry, dict):
            text = entry.get('text', '').strip()
        else:
            text = str(entry).strip()
        
        if text:
            text_lines.append(text)
    
    return ' '.join(text_lines)


def save_transcript(
    transcript_text: str,
    book_title: Optional[str],
    video_id: str,
    part_number: int,
    output_dir: Path
) -> Path:
    """
    자막을 파일로 저장
    
    Args:
        transcript_text: 자막 텍스트
        book_title: 책 제목 (선택사항)
        video_id: 비디오 ID (제목이 없을 때 사용)
        part_number: 파트 번호 (1, 2, 3, ...)
        output_dir: 출력 디렉토리
        
    Returns:
        저장된 파일 경로
    """
    # 출력 디렉토리 생성
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 파일명 생성
    if book_title:
        # 안전한 파일명 생성
        safe_title = get_standard_safe_title(book_title)
        if part_number == 1:
            filename = f"{safe_title}_part1_author.txt"
        elif part_number == 2:
            filename = f"{safe_title}_part2_novel.txt"
        else:
            filename = f"{safe_title}_part{part_number}.txt"
    else:
        # 제목이 없으면 비디오 ID 사용
        if part_number == 1:
            filename = f"{video_id}_part1_author.txt"
        elif part_number == 2:
            filename = f"{video_id}_part2_novel.txt"
        else:
            filename = f"{video_id}_part{part_number}.txt"
    
    output_file = output_dir / filename
    
    # 파일 저장
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(transcript_text)
        logger.info(f"✅ 자막이 저장되었습니다: {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"❌ 파일 저장 중 오류 발생: {e}")
        raise


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='유튜브 영상(Part 1, Part 2)에서 자막을 가져와서 각각 따로 저장하는 스크립트',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python scripts/fetch_separate_scripts.py \\
    --url1 "https://www.youtube.com/watch?v=VIDEO_ID_1" \\
    --url2 "https://www.youtube.com/watch?v=VIDEO_ID_2" \\
    --title "노인과 바다"
  
쿠키 사용 (IP 차단 우회):
  python scripts/fetch_separate_scripts.py \\
    --url1 "https://www.youtube.com/watch?v=VIDEO_ID_1" \\
    --url2 "https://www.youtube.com/watch?v=VIDEO_ID_2" \\
    --title "노인과 바다" \\
    --cookies "scripts/cookies.txt"
  
쿠키 파일 준비:
  1. 크롬 확장프로그램 "Get cookies.txt LOCALLY" 설치
  2. YouTube에 로그인한 상태에서 쿠키를 cookies.txt로 다운로드
  3. 스크립트 폴더(scripts/)에 cookies.txt 저장
        """
    )
    
    parser.add_argument(
        '--url1',
        type=str,
        default=None,
        help='Part 1 유튜브 URL 또는 비디오 ID (--urls 사용 시 선택사항)'
    )
    
    parser.add_argument(
        '--url2',
        type=str,
        default=None,
        help='Part 2 유튜브 URL 또는 비디오 ID (--urls 사용 시 선택사항)'
    )
    
    parser.add_argument(
        '--urls',
        type=str,
        nargs='+',
        default=None,
        help='여러 유튜브 URL 또는 비디오 ID (공백으로 구분, 예: --urls URL1 URL2 URL3)'
    )
    
    parser.add_argument(
        '--title',
        type=str,
        default=None,
        help='책 제목 (파일명 생성에 사용, 없으면 비디오 ID 사용)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/source',
        help='출력 디렉토리 (기본값: data/source)'
    )
    
    parser.add_argument(
        '--cookies',
        type=str,
        default=None,
        help='쿠키 파일 경로 (기본값: scripts/cookies.txt, IP 차단 우회용)'
    )
    
    args = parser.parse_args()
    
    # URL 리스트 구성
    urls = []
    if args.urls:
        urls = args.urls
    elif args.url1 and args.url2:
        urls = [args.url1, args.url2]
    else:
        logger.error("❌ --urls 또는 --url1과 --url2를 제공해주세요.")
        sys.exit(1)
    
    # 비디오 ID 추출
    video_ids = []
    for i, url in enumerate(urls, 1):
        video_id = extract_video_id(url)
        if not video_id:
            logger.error(f"❌ Part {i} URL에서 비디오 ID를 추출할 수 없습니다: {url}")
            sys.exit(1)
        video_ids.append(video_id)
    
    if args.title:
        logger.info(f"📖 책 제목: {args.title}")
    else:
        logger.info("📖 책 제목: (없음 - 비디오 ID 사용)")
    for i, video_id in enumerate(video_ids, 1):
        logger.info(f"📹 Part {i} 비디오 ID: {video_id}")
    logger.info("")
    
    # 각 파트별로 자막 가져오기
    transcripts = []
    transcript_texts = []

    for i, video_id in enumerate(video_ids, 1):
        logger.info("=" * 60)
        logger.info(f"Part {i} 자막 가져오는 중...")
        logger.info("=" * 60)

        # Part 간 rate limiting (첫 번째 파트 이후 딜레이)
        if i > 1:
            delay = 3
            logger.info(f"⏳ Rate limiting: {delay}초 대기 중...")
            time.sleep(delay)

        transcript_text = None

        # 1차: youtube-transcript-api 시도
        transcript = fetch_transcript(video_id, cookies_path=args.cookies)
        if transcript:
            transcript_text = format_transcript(transcript)

        # 2차: yt-dlp 폴백 (IP 차단 시 자동 전환)
        if not transcript_text:
            logger.info(f"🔄 youtube-transcript-api 실패 → yt-dlp 폴백 시도...")
            transcript_text = fetch_transcript_ytdlp(
                video_id,
                cookies_path=Path(args.cookies) if args.cookies else None
            )

        if not transcript_text:
            logger.error(f"❌ Part {i} 자막을 가져올 수 없습니다. (youtube-transcript-api, yt-dlp 모두 실패)")
            sys.exit(1)

        logger.info(f"✅ Part {i} 자막 길이: {len(transcript_text)} 문자")
        logger.info("")

        transcripts.append(None)  # compat
        transcript_texts.append(transcript_text)
    
    # 각각 따로 저장
    logger.info("=" * 60)
    logger.info("자막 저장 중...")
    logger.info("=" * 60)
    output_dir = Path(args.output_dir)
    
    output_files = []
    for i, (transcript_text, video_id) in enumerate(zip(transcript_texts, video_ids), 1):
        text = transcript_text if isinstance(transcript_text, str) else format_transcript(transcript_text)
        output_file = save_transcript(text, args.title, video_id, i, output_dir)
        output_files.append(output_file)
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ NotebookLM용 소스 파일 생성 완료")
    logger.info("=" * 60)
    for i, (output_file, transcript_text) in enumerate(zip(output_files, transcript_texts), 1):
        logger.info(f"📄 Part {i} 파일: {output_file}")
        logger.info(f"📊 Part {i} 길이: {len(transcript_text)} 문자")


if __name__ == '__main__':
    main()

