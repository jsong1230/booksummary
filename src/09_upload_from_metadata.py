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
    
    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list,
        privacy_status: str = "private",
        thumbnail_path: Optional[str] = None
    ) -> Optional[Dict]:
        """영상 업로드"""
        if not os.path.exists(video_path):
            print(f"❌ 영상 파일을 찾을 수 없습니다: {video_path}")
            return None
        
        video_file = Path(video_path)
        file_size = video_file.stat().st_size
        
        print(f"📤 업로드 중: {title}")
        print(f"   파일 크기: {file_size / (1024*1024):.2f} MB")
        
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
    
    def update_video_metadata(
        self,
        video_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[list] = None,
        category_id: str = '22'
    ) -> bool:
        """이미 업로드된 영상의 메타데이터 업데이트"""
        try:
            # 현재 영상 정보 가져오기
            video_response = self.youtube.videos().list(
                part='snippet,status',
                id=video_id
            ).execute()
            
            if not video_response.get('items'):
                print(f"❌ 영상을 찾을 수 없습니다: {video_id}")
                return False
            
            video = video_response['items'][0]
            snippet = video['snippet']
            
            # 업데이트할 정보 준비
            updated_snippet = {
                'title': title if title else snippet.get('title', ''),
                'description': description if description else snippet.get('description', ''),
                'tags': tags if tags else snippet.get('tags', []),
                'categoryId': category_id
            }
            
            # 기존 정보 유지 (채널 ID 등)
            updated_snippet['channelId'] = snippet.get('channelId')
            updated_snippet['defaultLanguage'] = snippet.get('defaultLanguage', 'ko')
            updated_snippet['defaultAudioLanguage'] = snippet.get('defaultAudioLanguage', 'ko')
            
            # 업데이트 요청
            update_request = self.youtube.videos().update(
                part='snippet',
                body={
                    'id': video_id,
                    'snippet': updated_snippet
                }
            )
            
            response = update_request.execute()
            print(f"✅ 영상 메타데이터 업데이트 완료: {response['snippet']['title']}")
            return True
            
        except HttpError as e:
            error_status = e.resp.status if hasattr(e.resp, 'status') else None
            print(f"❌ YouTube API 오류: {e}")
            if error_status == 403:
                print("   권한이 없습니다. OAuth2 스코프를 확인하세요.")
            elif error_status == 401:
                print("   인증이 만료되었습니다. 토큰을 갱신하세요.")
            return False
        except Exception as e:
            print(f"❌ 업데이트 실패: {e}")
            import traceback
            print(f"   상세 오류:\n{traceback.format_exc()}")
            return False
    
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
            book_title = path_obj.stem.replace('_review_ko', '').replace('_review_en', '').replace('_review', '')
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
                title_normalized = title.replace(' ', '').replace('_', '')
                uploaded_book_normalized = uploaded_book.replace(' ', '').replace('_', '')
                
                if (title == uploaded_book or 
                    uploaded_book_normalized in title_normalized or 
                    title_normalized in uploaded_book_normalized or
                    title_normalized == uploaded_book_normalized):
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
    """history 파일에 업로드 기록 추가"""
    history_file = Path("history")
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
            book_title = path_obj.stem.replace('_review_ko', '').replace('_review_en', '').replace('_review', '')
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
    uploaded_videos = load_uploaded_videos()
    print(f"📋 이미 업로드된 영상: {len(uploaded_videos)}개 (중복 체크용)\n")
    
    # 업로드 설정
    privacy = args.privacy
    
    if not args.auto:
        try:
            user_input = input(f"공개 설정 (private/unlisted/public, 기본값: {privacy}): ").strip().lower()
            if user_input in ['private', 'unlisted', 'public']:
                privacy = user_input
        except (EOFError, KeyboardInterrupt):
            print(f"   기본값 사용: {privacy}")
    
    print(f"📤 공개 설정: {privacy}")
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
            book_title = video_path.stem.replace('_review_ko', '').replace('_review_en', '').replace('_review', '')
            video_dir = video_path.parent
            
            # 언어 감지
            detected_lang = lang
            if not detected_lang:
                if '_ko' in video_path.stem or 'review_ko' in video_path.stem:
                    detected_lang = 'ko'
                elif '_en' in video_path.stem or 'review_en' in video_path.stem:
                    detected_lang = 'en'
                else:
                    detected_lang = 'ko'  # 기본값
            
            # 1순위: 생성된 썸네일 파일 찾기 (책제목_thumbnail_ko.jpg 형식)
            lang_suffix = "_ko" if detected_lang == "ko" else "_en"
            thumbnail_path = video_dir / f"{book_title}_thumbnail{lang_suffix}.jpg"
            
            if thumbnail_path.exists():
                thumbnail = str(thumbnail_path)
                print(f"   📸 썸네일: {thumbnail_path.name} (생성된 썸네일)")
            else:
                # 2순위: 영상 파일명 기반 썸네일
                thumbnail_path2 = video_dir / f"{video_path.stem}_thumbnail{lang_suffix}.jpg"
                if thumbnail_path2.exists():
                    thumbnail = str(thumbnail_path2)
                    print(f"   📸 썸네일: {thumbnail_path2.name}")
                else:
                    # 3순위: 언어 구분 없는 썸네일
                    thumbnail_path_alt = video_dir / f"{book_title}_thumbnail.jpg"
                    if thumbnail_path_alt.exists():
                        thumbnail = str(thumbnail_path_alt)
                        print(f"   📸 썸네일: {thumbnail_path_alt.name}")
                    else:
                        # 4순위: 무드 이미지 사용 (기존 방식)
                        mood_images = sorted((Path("assets/images") / book_title).glob("mood_*.jpg"))
                        if mood_images:
                            thumbnail = str(mood_images[0])
                            print(f"   📸 썸네일: {mood_images[0].name} (무드 이미지)")
                        else:
                            print(f"   ⚠️ 썸네일을 찾을 수 없습니다.")
        
        print()
        
        # 업로드
        result = uploader.upload_video(
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

