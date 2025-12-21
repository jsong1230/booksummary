"""
메타데이터 파일을 읽어서 YouTube에 업로드하는 스크립트
"""

import os
import json
import csv
from pathlib import Path
from typing import Optional, Dict, Set
from datetime import datetime
from dotenv import load_dotenv

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']


class YouTubeUploader:
    """YouTube 업로더"""
    
    def __init__(self):
        if not GOOGLE_API_AVAILABLE:
            raise ImportError("google-api-python-client가 필요합니다.")
        
        self.client_id = os.getenv("YOUTUBE_CLIENT_ID")
        self.client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
        self.refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
        
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            raise ValueError("YouTube API 자격증명이 설정되지 않았습니다.")
        
        self.youtube = None
        self._authenticate()
    
    def _authenticate(self):
        """OAuth2 인증"""
        try:
            credentials = Credentials(
                token=None,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=SCOPES
            )
            
            credentials.refresh(Request())
            self.youtube = build('youtube', 'v3', credentials=credentials)
            print("✅ YouTube API 인증 성공")
        except Exception as e:
            print(f"❌ 인증 실패: {e}")
            raise
    
    def _validate_and_clean_tags(self, tags: list) -> list:
        """태그 검증 및 정리 (YouTube 규칙 준수)"""
        MAX_TAG_LENGTH = 30  # YouTube 태그 최대 길이
        MAX_TAGS = 500  # YouTube 태그 최대 개수 (실제로는 더 적지만 안전하게)
        
        cleaned_tags = []
        for tag in tags:
            if not tag or not isinstance(tag, str):
                continue
            
            # 공백 제거
            tag = tag.strip()
            
            # 빈 태그 제거
            if not tag:
                continue
            
            # 길이 제한 (30자)
            if len(tag) > MAX_TAG_LENGTH:
                # 너무 긴 태그는 자르거나 건너뛰기
                print(f"   ⚠️ 태그 길이 초과 (30자): '{tag[:50]}...' (건너뜀)")
                continue
            
            # 특수 문자 제거 (YouTube가 허용하지 않는 문자)
            # 허용되는 문자: 알파벳, 숫자, 공백, 하이픈, 언더스코어
            import re
            # 기본적으로는 그대로 사용하되, 문제가 될 수 있는 문자만 체크
            if any(c in tag for c in ['<', '>', '&', '"', "'", '\n', '\r', '\t']):
                # 문제가 되는 문자 제거
                tag = re.sub(r'[<>&"\'\\n\\r\\t]', '', tag)
                if not tag.strip():
                    continue
            
            cleaned_tags.append(tag)
            
            # 최대 개수 제한
            if len(cleaned_tags) >= MAX_TAGS:
                break
        
        return cleaned_tags
    
    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list,
        privacy_status: str = "private",
        thumbnail_path: Optional[str] = None,
        channel_id: Optional[str] = None
    ) -> Optional[Dict]:
        """영상 업로드"""
        if not os.path.exists(video_path):
            print(f"❌ 영상 파일을 찾을 수 없습니다: {video_path}")
            return None
        
        video_file = Path(video_path)
        file_size = video_file.stat().st_size
        
        print(f"📤 업로드 중: {title}")
        print(f"   파일 크기: {file_size / (1024*1024):.2f} MB")
        
        # 태그 검증 및 정리
        original_tag_count = len(tags)
        tags = self._validate_and_clean_tags(tags)
        if len(tags) < original_tag_count:
            print(f"   ⚠️ 태그 정리: {original_tag_count}개 → {len(tags)}개 (30자 초과 태그 제거)")
        print(f"   🏷️ 태그 개수: {len(tags)}개")
        
        # Description 검증 및 수정
        # YouTube description 최대 길이: 5000자
        MAX_DESCRIPTION_LENGTH = 5000
        if len(description) > MAX_DESCRIPTION_LENGTH:
            print(f"   ⚠️ Description이 너무 깁니다 ({len(description)}자). {MAX_DESCRIPTION_LENGTH}자로 자릅니다.")
            description = description[:MAX_DESCRIPTION_LENGTH]
        
        # 특수 문자나 문제가 될 수 있는 문자 제거/치환
        # YouTube API가 문제를 일으킬 수 있는 문자들 처리
        import re
        import unicodedata
        
        # NULL 문자 제거
        description = description.replace('\x00', '')
        
        # 줄바꿈 정규화
        description = description.replace('\r\n', '\n')
        description = description.replace('\r', '\n')
        
        # 특수 선 문자(━)를 일반 하이픈으로 치환
        description = description.replace('━', '-')
        description = description.replace('─', '-')
        description = description.replace('━', '-')
        
        # 유효하지 않은 유니코드 문자 제거 (서로게이트 페어, 제어 문자 등)
        # YouTube API가 거부할 수 있는 문자 제거
        cleaned_chars = []
        for char in description:
            code_point = ord(char)
            # 유효한 유니코드 범위 체크 (서로게이트 페어 제외)
            if code_point < 0xD800 or code_point > 0xDFFF:
                # 제어 문자 제거 (줄바꿈, 탭 제외)
                if code_point < 0x20 and char not in ['\n', '\t']:
                    continue
                # 유효한 유니코드 문자만 포함
                if code_point <= 0x10FFFF:
                    # 이모지 범위 제거 (일부 이모지가 문제를 일으킬 수 있음)
                    # 하지만 기본 이모지는 유지 (0x1F300-0x1F9FF는 이모지 범위)
                    # 문제가 되는 특정 이모지만 제거하거나, 모두 유지
                    cleaned_chars.append(char)
        description = ''.join(cleaned_chars)
        
        # YouTube API가 거부할 수 있는 특정 문자 패턴 제거
        # 연속된 특수 문자 제거
        description = re.sub(r'[━─]{3,}', '---', description)
        
        # description이 너무 길면 자르기 (YouTube 제한: 5000자)
        if len(description) > 4500:
            description = description[:4500] + '...'
        
        # 연속된 줄바꿈 정리
        description = re.sub(r'\n{4,}', '\n\n\n', description)
        
        # 앞뒤 공백 제거
        description = description.strip()
        
        # 빈 description 체크
        if not description or len(description.strip()) == 0:
            print("   ⚠️ Description이 비어있습니다. 기본 설명을 사용합니다.")
            description = "책 리뷰 영상입니다."
        
        # 디버깅: description 길이와 처음 100자 출력
        print(f"   📝 Description 길이: {len(description)}자")
        if len(description) > 0:
            print(f"   📝 Description 처음 100자: {repr(description[:100])}")
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': '22'  # People & Blogs
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False
            }
        }
        
        # 채널 ID가 지정된 경우 snippet에 추가
        if channel_id:
            body['snippet']['channelId'] = channel_id
            print(f"   📺 채널 ID 지정: {channel_id}")
        
        try:
            # 파일 크기 확인 및 경고
            file_size_mb = file_size / (1024 * 1024)
            if file_size_mb > 100:
                print(f"   ⚠️ 큰 파일 크기: {file_size_mb:.2f} MB (업로드에 시간이 걸릴 수 있습니다)")
            
            media = MediaFileUpload(
                video_path,
                chunksize=-1,
                resumable=True,
                mimetype='video/*'
            )
            
            insert_request = self.youtube.videos().insert(
                part=','.join(['snippet', 'status']),
                body=body,
                media_body=media
            )
            
            response = self._resumable_upload(insert_request)
            video_id = response['id']
            
            # 썸네일 업로드 (재시도 포함)
            if thumbnail_path and os.path.exists(thumbnail_path):
                print(f"   📸 썸네일 업로드 중...")
                self.upload_thumbnail(video_id, thumbnail_path)
            
            result = {
                'video_id': video_id,
                'title': title,
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'privacy_status': privacy_status,
                'video_path': video_path,
                'file_size_mb': round(file_size_mb, 2)
            }
            
            print(f"✅ 업로드 완료: {result['url']}")
            return result
            
        except HttpError as e:
            error_status = e.resp.status if hasattr(e.resp, 'status') else None
            error_reason = None
            if hasattr(e, 'content'):
                try:
                    import json
                    error_content = json.loads(e.content.decode())
                    error_reason = error_content.get('error', {}).get('message', '')
                except:
                    pass
            
            print(f"❌ YouTube API 오류: {e}")
            if error_status == 403:
                print("   권한이 없습니다. OAuth2 스코프를 확인하세요.")
            elif error_status == 401:
                print("   인증이 만료되었습니다. 토큰을 갱신하세요.")
            elif error_reason:
                print(f"   상세: {error_reason}")
            return None
            
        except Exception as e:
            print(f"❌ 업로드 실패: {e}")
            import traceback
            print(f"   상세 오류:\n{traceback.format_exc()}")
            return None
    
    def _resumable_upload(self, insert_request):
        """재개 가능한 업로드 (개선된 재시도 로직)"""
        import time
        
        response = None
        retry = 0
        max_retries = 5
        retry_delay = 2  # 초
        
        while response is None:
            try:
                # 진행 상황 표시
                status, response = insert_request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    print(f"   진행 중... {progress}%", end='\r')
                
                if response and 'id' in response:
                    print("   완료!      ")
                    return response
                    
            except HttpError as e:
                error_status = e.resp.status if hasattr(e.resp, 'status') else None
                
                # 재시도 가능한 오류 (서버 오류, 네트워크 오류)
                if error_status in [500, 502, 503, 504] or error_status is None:
                    retry += 1
                    if retry > max_retries:
                        print(f"\n   ❌ 최대 재시도 횟수({max_retries}) 초과")
                        raise
                    
                    wait_time = retry_delay * retry  # 지수 백오프
                    print(f"\n   ⚠️ 서버 오류 발생 (재시도 {retry}/{max_retries})")
                    print(f"   {wait_time}초 후 재시도...")
                    time.sleep(wait_time)
                else:
                    # 재시도 불가능한 오류 (인증 오류, 권한 오류 등)
                    print(f"\n   ❌ 업로드 실패: {e}")
                    if error_status == 403:
                        print("   권한이 없습니다. OAuth2 토큰을 확인하세요.")
                    elif error_status == 401:
                        print("   인증이 만료되었습니다. 토큰을 갱신하세요.")
                    raise
                    
            except Exception as e:
                retry += 1
                if retry > max_retries:
                    print(f"\n   ❌ 최대 재시도 횟수({max_retries}) 초과: {e}")
                    raise
                
                wait_time = retry_delay * retry
                print(f"\n   ⚠️ 오류 발생: {e} (재시도 {retry}/{max_retries})")
                print(f"   {wait_time}초 후 재시도...")
                time.sleep(wait_time)
        
        return response
    
    def upload_thumbnail(self, video_id: str, thumbnail_path: str):
        """썸네일 업로드 (재시도 포함)"""
        import time
        
        max_retries = 3
        retry = 0
        
        while retry < max_retries:
            try:
                self.youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumbnail_path)
                ).execute()
                print("   ✅ 썸네일 업로드 완료")
                return
            except HttpError as e:
                error_status = e.resp.status if hasattr(e.resp, 'status') else None
                if error_status in [500, 502, 503, 504]:
                    retry += 1
                    if retry < max_retries:
                        print(f"   ⚠️ 썸네일 업로드 재시도 중... ({retry}/{max_retries})")
                        time.sleep(2 * retry)
                        continue
                print(f"   ⚠️ 썸네일 업로드 실패: {e}")
                return
            except Exception as e:
                retry += 1
                if retry < max_retries:
                    print(f"   ⚠️ 썸네일 업로드 재시도 중... ({retry}/{max_retries})")
                    time.sleep(2 * retry)
                    continue
                print(f"   ⚠️ 썸네일 업로드 실패: {e}")
                return


def load_metadata(metadata_path: Path) -> Optional[Dict]:
    """메타데이터 파일 로드"""
    if not metadata_path.exists():
        return None
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_metadata_files(output_dir: str = "output") -> list:
    """메타데이터 파일 찾기"""
    output_path = Path(output_dir)
    metadata_files = list(output_path.glob("*.metadata.json"))
    return sorted(metadata_files)


def load_uploaded_videos() -> Set[str]:
    """이미 업로드된 영상 목록 로드 (비디오 ID 기준)"""
    uploaded = set()
    
    # JSON 로그에서 로드
    log_file = Path("output/upload_log.json")
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                upload_history = json.load(f)
                for entry in upload_history:
                    video_id = entry.get('video_id', '')
                    video_path = entry.get('video_path', '')
                    if video_id:
                        uploaded.add(video_id)
                    if video_path:
                        # 파일 경로도 추가 (중복 체크용)
                        uploaded.add(video_path)
        except:
            pass
    
    # CSV 로그에서도 로드
    csv_file = Path("output/upload_log.csv")
    if csv_file.exists():
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    video_id = row.get('video_id', '')
                    video_path = row.get('video_path', '')
                    if video_id:
                        uploaded.add(video_id)
                    if video_path:
                        uploaded.add(video_path)
        except:
            pass
    
    return uploaded


def update_books_csv(uploaded_videos: list):
    """ildangbaek_books.csv에 업로드 정보 업데이트"""
    csv_file = Path("data/ildangbaek_books.csv")
    if not csv_file.exists():
        print(f"⚠️ CSV 파일을 찾을 수 없습니다: {csv_file}")
        return
    
    # 업로드된 영상에서 책 제목 추출
    uploaded_books = set()
    for result in uploaded_videos:
        video_path = result.get('video_path', '')
        if video_path:
            # 파일명에서 책 제목 추출
            path_obj = Path(video_path)
            book_title = path_obj.stem.replace('_review_with_summary_ko', '').replace('_review_with_summary_en', '')
            book_title = book_title.replace('_review_ko', '').replace('_review_en', '').replace('_review', '')
            book_title = book_title.replace('_with_summary', '')
            book_title = book_title.replace('_kr', '').replace('_en', '')
            uploaded_books.add(book_title)
    
    if not uploaded_books:
        return
    
    # CSV 파일 읽기
    rows = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            title = row.get('title', '').strip()
            # 책 제목 매칭 (정확히 일치하거나 부분 일치, 공백/언더스코어 무시)
            matched = False
            for uploaded_book in uploaded_books:
                # 공백과 언더스코어를 제거하여 비교
                title_normalized = title.replace(' ', '').replace('_', '').lower()
                uploaded_book_normalized = uploaded_book.replace(' ', '').replace('_', '').lower()
                
                # 한글/영문 제목 매칭을 위한 추가 로직
                # "Sunrise_on_the_Reaping"과 "선라이즈 온 더 리핑" 매칭
                from utils.translations import translate_book_title, translate_book_title_to_korean
                try:
                    # CSV의 한글 제목을 영문으로 변환하여 비교
                    en_title_from_csv = translate_book_title(title)
                    en_title_normalized = en_title_from_csv.replace(' ', '').replace('_', '').lower()
                    
                    # 업로드된 영문 제목과 비교
                    if (en_title_normalized == uploaded_book_normalized or
                        uploaded_book_normalized in en_title_normalized or
                        en_title_normalized in uploaded_book_normalized):
                        matched = True
                except:
                    pass
                
                # 기본 매칭 로직
                if (title == uploaded_book or 
                    uploaded_book_normalized in title_normalized or 
                    title_normalized in uploaded_book_normalized or
                    title_normalized == uploaded_book_normalized or
                    matched):
                    # 업로드 정보 업데이트
                    upload_time = datetime.now().strftime('%Y-%m-%d')
                    row['youtube_uploaded'] = upload_time
                    row['status'] = 'uploaded'
                    matched = True
                    print(f"   📝 CSV 업데이트: {title} -> uploaded ({upload_time})")
                    break
            rows.append(row)
    
    # CSV 파일 쓰기
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        if fieldnames:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    
    print(f"💾 CSV 파일 업데이트 완료: {csv_file}")


def update_history(uploaded_videos: list):
    """history.md 파일에 업로드 기록 추가"""
    history_file = Path("history.md")
    if not history_file.exists():
        return
    
    upload_time = datetime.now().strftime('%Y-%m-%d')
    
    # 업로드된 영상 정보 수집
    book_titles = []
    video_urls = []
    for result in uploaded_videos:
        video_path = result.get('video_path', '')
        if video_path:
            path_obj = Path(video_path)
            book_title = path_obj.stem.replace('_review_ko', '').replace('_review_en', '').replace('_review', '').replace('_kr', '').replace('_en', '')
            book_titles.append(book_title)
        if result.get('url'):
            video_urls.append(result['url'])
    
    if not book_titles:
        return
    
    # history 파일 읽기
    with open(history_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 새 기록 추가
    new_entry = f"""
## {upload_time}

### YouTube 업로드 완료
- 업로드된 책: {', '.join(set(book_titles))}
- 업로드된 영상 수: {len(uploaded_videos)}개
"""
    for i, result in enumerate(uploaded_videos, 1):
        new_entry += f"- [{i}] {result.get('title', '')}\n"
        new_entry += f"  - URL: {result.get('url', '')}\n"
    
    # 파일 끝에 추가
    with open(history_file, 'a', encoding='utf-8') as f:
        f.write(new_entry)
    
    print(f"💾 History 파일 업데이트 완료: {history_file}")


def save_upload_log(uploaded_videos: list, privacy_status: str):
    """업로드 기록을 파일에 저장 (JSON, CSV, TXT)"""
    upload_time = datetime.now().isoformat()
    
    # JSON 로그 저장
    log_file = Path("output/upload_log.json")
    upload_history = []
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                upload_history = json.load(f)
        except:
            upload_history = []
    
    for result in uploaded_videos:
        log_entry = {
            'upload_time': upload_time,
            'video_id': result.get('video_id', ''),
            'title': result.get('title', ''),
            'url': result.get('url', ''),
            'privacy_status': privacy_status,
            'video_path': result.get('video_path', '')
        }
        upload_history.append(log_entry)
    
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(upload_history, f, ensure_ascii=False, indent=2)
    
    print(f"💾 JSON 로그 저장: {log_file}")
    
    # CSV 로그 저장
    csv_file = Path("output/upload_log.csv")
    file_exists = csv_file.exists()
    
    with open(csv_file, 'a', encoding='utf-8', newline='') as f:
        fieldnames = ['upload_time', 'video_id', 'title', 'url', 'privacy_status', 'video_path']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        for result in uploaded_videos:
            writer.writerow({
                'upload_time': upload_time,
                'video_id': result.get('video_id', ''),
                'title': result.get('title', ''),
                'url': result.get('url', ''),
                'privacy_status': privacy_status,
                'video_path': result.get('video_path', '')
            })
    
    print(f"💾 CSV 로그 저장: {csv_file}")
    
    # 텍스트 로그도 저장 (읽기 쉽게)
    text_log_file = Path("output/upload_log.txt")
    with open(text_log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"업로드 시간: {upload_time}\n")
        f.write(f"{'='*60}\n\n")
        for result in uploaded_videos:
            f.write(f"제목: {result.get('title', '')}\n")
            f.write(f"URL: {result.get('url', '')}\n")
            f.write(f"비디오 ID: {result.get('video_id', '')}\n")
            f.write(f"공개 설정: {privacy_status}\n")
            f.write(f"\n")
    
    print(f"💾 텍스트 로그 저장: {text_log_file}")


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YouTube 업로드 (메타데이터 기반)')
    parser.add_argument('--privacy', type=str, default='private', choices=['private', 'unlisted', 'public'], help='공개 설정 (기본값: private)')
    parser.add_argument('--auto', action='store_true', help='자동 업로드 (확인 없이)')
    parser.add_argument('--channel-id', type=str, help='업로드할 채널 ID (선택사항, 환경 변수 YOUTUBE_CHANNEL_ID로도 설정 가능)')
    parser.add_argument('--force', action='store_true', help='강제 업로드 (중복 체크 무시)')
    
    args = parser.parse_args()
    
    if not GOOGLE_API_AVAILABLE:
        print("❌ google-api-python-client가 필요합니다.")
        return
    
    print("=" * 60)
    print("🚀 YouTube 업로드 (메타데이터 기반)")
    print("=" * 60)
    print()
    
    try:
        uploader = YouTubeUploader()
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        return
    
    # 메타데이터 파일 찾기
    metadata_files = find_metadata_files()
    
    if not metadata_files:
        print("📭 메타데이터 파일을 찾을 수 없습니다.")
        print("   output/ 폴더에 *.metadata.json 파일이 있는지 확인하세요.")
        return
    
    print(f"📹 발견된 메타데이터: {len(metadata_files)}개\n")
    
    # 이미 업로드된 영상 목록 로드
    uploaded_videos = set()
    if not args.force:
        uploaded_videos = load_uploaded_videos()
        print(f"📋 이미 업로드된 영상: {len(uploaded_videos)}개 (중복 체크용)\n")
    else:
        print("⚠️ 강제 업로드 모드: 중복 체크를 건너뜁니다.\n")
    
    # 업로드 설정
    privacy = args.privacy
    
    # 채널 ID 확인 (인자 > 환경 변수 > 기본값)
    default_channel_id = 'UCxOcO_x_yW6sfg_FPUQVqYA'  # book summary 채널
    channel_id = args.channel_id or os.getenv('YOUTUBE_CHANNEL_ID') or default_channel_id
    
    if not args.auto:
        try:
            user_input = input(f"공개 설정 (private/unlisted/public, 기본값: {privacy}): ").strip().lower()
            if user_input in ['private', 'unlisted', 'public']:
                privacy = user_input
        except (EOFError, KeyboardInterrupt):
            print(f"   기본값 사용: {privacy}")
    
    print(f"📤 공개 설정: {privacy}")
    if channel_id:
        print(f"📺 채널 ID: {channel_id}")
    print()
    
    # 영상 업로드
    uploaded = []
    skipped = []
    
    for i, metadata_path in enumerate(metadata_files, 1):
        print(f"[{i}/{len(metadata_files)}] {metadata_path.name}")
        
        # 메타데이터 로드
        metadata = load_metadata(metadata_path)
        if not metadata:
            print("   ⚠️ 메타데이터 로드 실패")
            continue
        
        video_path = Path(metadata['video_path'])
        if not video_path.exists():
            print(f"   ⚠️ 영상 파일을 찾을 수 없습니다: {video_path}")
            continue
        
        # 중복 체크
        video_path_str = str(video_path)
        if video_path_str in uploaded_videos:
            print(f"   ⏭️ 이미 업로드된 영상입니다. 건너뜁니다.")
            skipped.append({
                'video_path': video_path_str,
                'title': metadata.get('title', ''),
                'reason': 'already_uploaded'
            })
            print()
            continue
        
        title = metadata['title']
        description = metadata['description']
        tags = metadata.get('tags', [])
        lang = metadata.get('language', 'ko')
        
        print(f"   📌 제목: {title}")
        print(f"   🌐 언어: {lang.upper()}")
        print()
        
        # 썸네일 찾기 (메타데이터에 저장된 경로 우선)
        thumbnail = metadata.get('thumbnail_path')
        
        if thumbnail and os.path.exists(thumbnail):
            print(f"   📸 썸네일: {Path(thumbnail).name} (메타데이터에서)")
        else:
            # 메타데이터에 없으면 자동으로 찾기
            video_dir = video_path.parent
            video_stem = video_path.stem
            
            # 언어 감지
            detected_lang = lang
            if not detected_lang:
                if '_ko' in video_stem or 'review_ko' in video_stem or '_kr' in video_stem:
                    detected_lang = 'ko'
                elif '_en' in video_stem or 'review_en' in video_stem:
                    detected_lang = 'en'
                else:
                    detected_lang = 'ko'  # 기본값
            
            # 책 제목 추출 (다양한 패턴 시도)
            book_title_variants = []
            # 기본 패턴
            base_title = video_stem.replace('_review_with_summary_ko', '').replace('_review_with_summary_en', '')
            base_title = base_title.replace('_review_ko', '').replace('_review_en', '')
            base_title = base_title.replace('_review', '').replace('_with_summary', '')
            base_title = base_title.replace('_kr', '').replace('_en', '')
            book_title_variants.append(base_title)
            
            # 공백 제거 버전
            book_title_variants.append(base_title.replace('_', '').replace(' ', ''))
            # 공백을 언더스코어로 변환한 버전
            book_title_variants.append(base_title.replace(' ', '_'))
            
            # 메타데이터에서 책 제목 가져와서 한글 제목도 추가
            metadata_book_title = metadata.get('book_title')
            if metadata_book_title:
                from src.utils.file_utils import safe_title
                from src.utils.translations import translate_book_title_to_korean
                # 한글 제목 추가
                korean_title = translate_book_title_to_korean(metadata_book_title)
                if korean_title and korean_title != metadata_book_title:
                    korean_safe_title = safe_title(korean_title)
                    if korean_safe_title not in book_title_variants:
                        book_title_variants.append(korean_safe_title)
                # 원본 제목도 추가 (한글이면)
                if metadata_book_title != base_title:
                    original_safe_title = safe_title(metadata_book_title)
                    if original_safe_title not in book_title_variants:
                        book_title_variants.append(original_safe_title)
            
            # 언어 접미사 패턴
            lang_patterns = []
            if detected_lang == 'ko':
                lang_patterns = ['_ko', '_kr', '_korean', 'korean', 'ko', 'kr']
            else:
                lang_patterns = ['_en', '_english', 'english', 'en']
            
            thumbnail_found = False
            
            # 1순위: 다양한 책 제목 변형으로 썸네일 검색
            for title_variant in book_title_variants:
                for lang_pattern in lang_patterns:
                    # 패턴 1: {책제목}_thumbnail_{lang}.jpg
                    thumbnail_path = video_dir / f"{title_variant}_thumbnail{lang_pattern}.jpg"
                    if thumbnail_path.exists():
                        thumbnail = str(thumbnail_path)
                        print(f"   📸 썸네일: {thumbnail_path.name} (패턴: {title_variant}_thumbnail{lang_pattern})")
                        thumbnail_found = True
                        break
                    
                    # 패턴 2: {책제목}_{lang}_thumbnail.jpg
                    thumbnail_path = video_dir / f"{title_variant}{lang_pattern}_thumbnail.jpg"
                    if thumbnail_path.exists():
                        thumbnail = str(thumbnail_path)
                        print(f"   📸 썸네일: {thumbnail_path.name} (패턴: {title_variant}{lang_pattern}_thumbnail)")
                        thumbnail_found = True
                        break
                
                if thumbnail_found:
                    break
            
            if not thumbnail_found:
                # 2순위: 영상 파일명 기반 썸네일
                for lang_pattern in lang_patterns:
                    thumbnail_path = video_dir / f"{video_stem}_thumbnail{lang_pattern}.jpg"
                    if thumbnail_path.exists():
                        thumbnail = str(thumbnail_path)
                        print(f"   📸 썸네일: {thumbnail_path.name} (영상 파일명 기반)")
                        thumbnail_found = True
                        break
            
            if not thumbnail_found:
                # 3순위: output 폴더의 모든 썸네일 파일 검색 (언어 구분자 포함)
                all_thumbnails = list(video_dir.glob("*thumbnail*.jpg"))
                matching_thumbnails = []
                
                for thumb in all_thumbnails:
                    thumb_name_lower = thumb.name.lower()
                    # 언어 구분자가 포함된 썸네일만 검색
                    if any(pattern in thumb_name_lower for pattern in lang_patterns):
                        # 책 제목과 유사한 이름인지 확인
                        for title_variant in book_title_variants:
                            if title_variant.lower().replace('_', '').replace(' ', '') in thumb_name_lower.replace('_', '').replace(' ', ''):
                                matching_thumbnails.append(thumb)
                                break
                
                if matching_thumbnails:
                    # 가장 최근에 수정된 파일 선택
                    thumbnail = str(sorted(matching_thumbnails, key=lambda x: x.stat().st_mtime, reverse=True)[0])
                    print(f"   📸 썸네일: {Path(thumbnail).name} (유사도 매칭)")
                    thumbnail_found = True
            
            if not thumbnail_found:
                # 4순위: 언어 구분 없는 썸네일
                for title_variant in book_title_variants:
                    thumbnail_path = video_dir / f"{title_variant}_thumbnail.jpg"
                    if thumbnail_path.exists():
                        thumbnail = str(thumbnail_path)
                        print(f"   📸 썸네일: {thumbnail_path.name} (언어 구분 없음)")
                        thumbnail_found = True
                        break
            
            if not thumbnail_found:
                # 5순위: 무드 이미지 사용 (기존 방식)
                book_title_for_assets = book_title_variants[0]  # 첫 번째 변형 사용
                mood_images = sorted((Path("assets/images") / book_title_for_assets).glob("mood_*.jpg"))
                if mood_images:
                    thumbnail = str(mood_images[0])
                    print(f"   📸 썸네일: {mood_images[0].name} (무드 이미지)")
                else:
                    print(f"   ⚠️ 썸네일을 찾을 수 없습니다.")
                    print(f"   💡 썸네일 파일명 패턴 예시:")
                    print(f"      - {book_title_variants[0]}_thumbnail_ko.jpg")
                    print(f"      - {book_title_variants[0]}_thumbnail_en.jpg")
                    print(f"      - {video_stem}_thumbnail_ko.jpg")
        
        print()
        
        # 업로드
        result = uploader.upload_video(
            channel_id=channel_id,
            video_path=str(video_path),
            title=title,
            description=description,
            tags=tags,
            privacy_status=privacy,
            thumbnail_path=thumbnail
        )
        
        if result:
            uploaded.append(result)
            # 업로드된 영상 목록에 추가 (같은 세션에서 중복 방지)
            uploaded_videos.add(video_path_str)
            if result.get('video_id'):
                uploaded_videos.add(result['video_id'])
        
        print()
    
    # 결과 요약
    print("=" * 60)
    print(f"✅ 업로드 완료: {len(uploaded)}/{len(metadata_files)}개")
    if skipped:
        print(f"⏭️ 건너뜀: {len(skipped)}개 (이미 업로드됨)")
    print("=" * 60)
    print()
    
    if uploaded:
        # 업로드 기록 저장
        save_upload_log(uploaded, privacy)
        
        # CSV 파일 업데이트
        update_books_csv(uploaded)
        
        # History 파일 업데이트
        update_history(uploaded)
        
        for result in uploaded:
            print(f"📺 {result['title']}")
            print(f"   URL: {result['url']}")
            print()
    
    if skipped:
        print("⏭️ 건너뛴 영상:")
        for item in skipped:
            print(f"   • {item['title']}")
        print()


if __name__ == "__main__":
    main()

