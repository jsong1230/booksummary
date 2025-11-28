"""
유튜브 채널에 업로드된 책들의 정보를 ildangbaek_books.csv에 업데이트하는 스크립트
"""

import os
import csv
import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
from dotenv import load_dotenv

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']


class YouTubeChannelUpdater:
    """유튜브 채널에서 업로드된 책 정보를 CSV에 업데이트하는 클래스"""
    
    # 책 제목 별칭 매핑 (비디오 제목에 나오는 이름 -> CSV에 등록된 이름)
    BOOK_ALIASES = {
        '노르웨이의 숲': '상실의 시대',
        'norwegian wood': '상실의 시대',
        'the age of loss': '상실의 시대',
    }
    
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
    
    def get_my_channel_id(self) -> Optional[str]:
        """현재 인증된 사용자의 채널 ID 가져오기"""
        try:
            response = self.youtube.channels().list(
                part='id',
                mine=True
            ).execute()
            
            if response.get('items'):
                channel_id = response['items'][0]['id']
                print(f"✅ 채널 ID: {channel_id}")
                return channel_id
            return None
        except Exception as e:
            print(f"❌ 채널 ID 가져오기 실패: {e}")
            return None
    
    def get_channel_videos(self, channel_id: str, max_results: int = 50) -> List[Dict]:
        """채널의 모든 비디오 가져오기"""
        videos = []
        next_page_token = None
        
        print(f"📹 채널의 비디오 목록 가져오는 중...")
        
        while len(videos) < max_results:
            try:
                # 채널의 업로드 플레이리스트 ID 가져오기
                if not hasattr(self, '_upload_playlist_id'):
                    channel_response = self.youtube.channels().list(
                        part='contentDetails',
                        id=channel_id
                    ).execute()
                    
                    if not channel_response.get('items'):
                        print("❌ 채널을 찾을 수 없습니다.")
                        break
                    
                    self._upload_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
                
                # 플레이리스트에서 비디오 가져오기
                request_params = {
                    'part': 'snippet,contentDetails',
                    'playlistId': self._upload_playlist_id,
                    'maxResults': min(50, max_results - len(videos))
                }
                
                if next_page_token:
                    request_params['pageToken'] = next_page_token
                
                response = self.youtube.playlistItems().list(**request_params).execute()
                
                for item in response.get('items', []):
                    video_info = {
                        'video_id': item['contentDetails']['videoId'],
                        'title': item['snippet']['title'],
                        'published_at': item['snippet']['publishedAt'],
                        'description': item['snippet'].get('description', ''),
                        'url': f"https://www.youtube.com/watch?v={item['contentDetails']['videoId']}"
                    }
                    videos.append(video_info)
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                
                print(f"   진행 중... {len(videos)}개 비디오 수집됨")
                
            except HttpError as e:
                print(f"❌ 비디오 목록 가져오기 실패: {e}")
                break
            except Exception as e:
                print(f"❌ 오류 발생: {e}")
                break
        
        print(f"✅ 총 {len(videos)}개의 비디오를 찾았습니다.\n")
        return videos
    
    def is_shorts_video(self, video_title: str, video_description: str = '') -> bool:
        """비디오가 Shorts인지 확인"""
        text = f"{video_title} {video_description}".lower()
        shorts_keywords = ['#shorts', 'shorts', '#short']
        return any(keyword in text for keyword in shorts_keywords)
    
    def is_book_review_video(self, video_title: str, video_description: str = '') -> bool:
        """비디오가 책 리뷰인지 확인"""
        # Shorts 비디오는 제외
        if self.is_shorts_video(video_title, video_description):
            return False
        
        text = f"{video_title} {video_description}".lower()
        # 책 리뷰 관련 키워드 확인
        review_keywords = [
            '책 리뷰', 'book review', '리뷰', 'review',
            '[한국어]', '[korean]', '[english]', '[영어]'
        ]
        return any(keyword in text for keyword in review_keywords)
    
    def extract_book_title_from_video_title(self, video_title: str) -> Optional[str]:
        """비디오 제목에서 책 제목 추출"""
        # 책 리뷰가 아닌 비디오는 제외
        if not self.is_book_review_video(video_title):
            return None
        
        # 일반적인 패턴들 (더 엄격하게)
        patterns = [
            r'\[한국어\]\s*(.+?)\s*책\s*리뷰',  # "[한국어] 책 제목 책 리뷰"
            r'\[Korean\]\s*(.+?)\s*Book\s*Review',  # "[Korean] Book Title Book Review"
            r'\[English\]\s*(.+?)\s*Book\s*Review',  # "[English] Book Title Book Review"
            r'\[영어\]\s*(.+?)\s*책\s*리뷰',  # "[영어] 책 제목 책 리뷰"
            r'^(.+?)\s*책\s*리뷰',  # "책 제목 책 리뷰"
            r'^(.+?)\s*Book\s*Review',  # "Book Title Book Review"
            r'^(.+?)\s*\|\s*책\s*리뷰',  # "책 제목 | 책 리뷰"
            r'^(.+?)\s*\|\s*Book\s*Review',  # "Book Title | Book Review"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, video_title, re.IGNORECASE)
            if match:
                book_title = match.group(1).strip()
                # 불필요한 문자 제거
                book_title = re.sub(r'\s+', ' ', book_title)
                # 괄호 내용 제거 (예: [Korean], [한국어] 등)
                book_title = re.sub(r'\[.*?\]', '', book_title).strip()
                if book_title and len(book_title) > 1:  # 최소 2글자 이상
                    return book_title
        
        return None
    
    def normalize_title(self, title: str) -> str:
        """제목 정규화 (비교를 위해)"""
        # 공백, 언더스코어, 특수문자 제거
        normalized = re.sub(r'[\s_\-|]', '', title.lower())
        # 괄호와 내용 제거
        normalized = re.sub(r'\([^)]*\)', '', normalized)
        normalized = re.sub(r'\[[^\]]*\]', '', normalized)
        return normalized
    
    def _check_alias_match(self, title1: str, title2: str) -> bool:
        """별칭 매칭 확인"""
        title1_lower = title1.lower()
        title2_lower = title2.lower()
        
        for alias, real_title in self.BOOK_ALIASES.items():
            alias_lower = alias.lower()
            real_lower = real_title.lower()
            
            # title1이 별칭이고 title2가 실제 제목인 경우
            if alias_lower in title1_lower and real_lower in title2_lower:
                return True
            # title2가 별칭이고 title1이 실제 제목인 경우
            if alias_lower in title2_lower and real_lower in title1_lower:
                return True
        
        return False
    
    def match_book_to_video(self, book_title: str, video_title: str, video_description: str = '') -> bool:
        """책 제목과 비디오 제목/설명이 매칭되는지 확인"""
        # 책 리뷰 비디오가 아니면 매칭하지 않음
        if not self.is_book_review_video(video_title, video_description):
            return False
        
        # 정규화된 제목 비교
        book_normalized = self.normalize_title(book_title)
        video_text = f"{video_title} {video_description}"
        video_normalized = self.normalize_title(video_text)
        
        # 너무 짧은 제목은 제외 (1-2글자는 제외)
        if len(book_normalized) < 3:
            return False
        
        # 정확히 일치하거나 포함 관계 확인
        if book_normalized in video_normalized or video_normalized in book_normalized:
            return True
        
        # 부분 일치 확인 (최소 3글자 이상)
        if len(book_normalized) >= 3:
            # 책 제목의 주요 단어들이 비디오 제목에 포함되는지 확인
            book_words = [w for w in book_normalized.split() if len(w) >= 2]
            if book_words:
                matched_words = sum(1 for word in book_words if word in video_normalized)
                # 70% 이상 일치하면 매칭으로 간주 (더 엄격하게)
                if matched_words >= len(book_words) * 0.7:
                    return True
        
        return False
    
    def load_books_csv(self, csv_path: str) -> List[Dict]:
        """CSV 파일 로드"""
        books = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                books.append(row)
        return books, fieldnames
    
    def update_csv(self, csv_path: str, videos: List[Dict], dry_run: bool = False) -> Dict:
        """CSV 파일 업데이트"""
        print(f"📚 CSV 파일 읽는 중: {csv_path}")
        books, fieldnames = self.load_books_csv(csv_path)
        
        print(f"   총 {len(books)}개의 책 정보를 찾았습니다.\n")
        
        # 업데이트 통계
        stats = {
            'matched': [],
            'updated': [],
            'already_uploaded': [],
            'not_found': []
        }
        
        # 각 비디오에 대해 매칭되는 책 찾기
        print("🔍 비디오와 책 매칭 중...\n")
        
        for video in videos:
            video_title = video['title']
            video_description = video.get('description', '')
            published_at = video['published_at']
            video_url = video['url']
            
            # Shorts 비디오는 건너뛰기
            if self.is_shorts_video(video_title, video_description):
                continue
            
            # 책 리뷰 비디오가 아니면 건너뛰기
            if not self.is_book_review_video(video_title, video_description):
                stats['not_found'].append({
                    'video': video_title,
                    'url': video_url,
                    'extracted_title': None,
                    'reason': 'not_book_review'
                })
                continue
            
            # 비디오 제목에서 책 제목 추출 시도
            extracted_title = self.extract_book_title_from_video_title(video_title)
            
            # 별칭 매핑 확인 (추출된 제목이 별칭이면 실제 제목으로 변환)
            original_extracted = extracted_title
            if extracted_title:
                extracted_lower = extracted_title.lower()
                for alias, real_title in self.BOOK_ALIASES.items():
                    alias_lower = alias.lower()
                    # 별칭이 추출된 제목에 포함되어 있거나, 추출된 제목이 별칭에 포함되어 있으면
                    if alias_lower in extracted_lower or extracted_lower in alias_lower:
                        extracted_title = real_title
                        print(f"      🔄 별칭 매핑: '{original_extracted}' -> '{real_title}'")
                        break
            
            matched_book = None
            for book in books:
                book_title = book.get('title', '').strip()
                if not book_title:
                    continue
                
                # 별칭 매핑이 적용된 경우, 실제 제목과만 비교
                if extracted_title and original_extracted != extracted_title:
                    # 별칭이 적용된 경우, 실제 제목과 정확히 일치하는지 확인
                    if self.normalize_title(extracted_title) == self.normalize_title(book_title):
                        matched_book = book
                        break
                # 추출된 제목과 비교
                elif extracted_title:
                    if self.normalize_title(extracted_title) == self.normalize_title(book_title):
                        matched_book = book
                        break
                    # 별칭 매핑도 확인
                    if self._check_alias_match(extracted_title, book_title):
                        matched_book = book
                        break
                
                # 직접 매칭 시도
                if self.match_book_to_video(book_title, video_title, video_description):
                    matched_book = book
                    break
            
            if matched_book:
                book_title = matched_book.get('title', '')
                current_status = matched_book.get('status', '')
                current_uploaded = matched_book.get('youtube_uploaded', '')
                
                # 업로드 날짜 추출 (YYYY-MM-DD 형식)
                upload_date = published_at[:10] if published_at else datetime.now().strftime('%Y-%m-%d')
                
                if current_status == 'uploaded' and current_uploaded:
                    stats['already_uploaded'].append({
                        'book': book_title,
                        'video': video_title,
                        'url': video_url,
                        'current_date': current_uploaded,
                        'new_date': upload_date
                    })
                    print(f"   ⏭️ {book_title}")
                    print(f"      이미 업로드됨: {current_uploaded}")
                    print(f"      비디오: {video_title[:50]}...")
                else:
                    stats['matched'].append({
                        'book': book_title,
                        'video': video_title,
                        'url': video_url,
                        'date': upload_date
                    })
                    
                    if not dry_run:
                        matched_book['status'] = 'uploaded'
                        matched_book['youtube_uploaded'] = upload_date
                        if not matched_book.get('video_created'):
                            matched_book['video_created'] = upload_date
                    
                    stats['updated'].append({
                        'book': book_title,
                        'video': video_title,
                        'url': video_url,
                        'date': upload_date
                    })
                    
                    print(f"   ✅ {book_title}")
                    print(f"      업로드 날짜: {upload_date}")
                    print(f"      비디오: {video_title[:50]}...")
                    print(f"      URL: {video_url}")
            else:
                stats['not_found'].append({
                    'video': video_title,
                    'url': video_url,
                    'extracted_title': extracted_title
                })
                print(f"   ❓ 매칭 실패: {video_title[:50]}...")
                if extracted_title:
                    print(f"      추출된 제목: {extracted_title}")
            
            print()
        
        # CSV 파일 저장
        if not dry_run and stats['updated']:
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                if fieldnames:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(books)
            print(f"💾 CSV 파일 업데이트 완료: {csv_path}\n")
        
        return stats


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='유튜브 채널에서 업로드된 책 정보를 CSV에 업데이트')
    parser.add_argument('--csv', type=str, default='data/ildangbaek_books.csv', help='CSV 파일 경로')
    parser.add_argument('--max-videos', type=int, default=100, help='최대 가져올 비디오 수')
    parser.add_argument('--dry-run', action='store_true', help='실제로 업데이트하지 않고 미리보기만')
    
    args = parser.parse_args()
    
    if not GOOGLE_API_AVAILABLE:
        print("❌ google-api-python-client가 필요합니다.")
        return
    
    print("=" * 60)
    print("📺 유튜브 채널에서 책 정보 업데이트")
    print("=" * 60)
    print()
    
    if args.dry_run:
        print("🔍 DRY RUN 모드: 실제로 업데이트하지 않습니다.\n")
    
    try:
        updater = YouTubeChannelUpdater()
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        return
    
    # 채널 ID 가져오기
    channel_id = updater.get_my_channel_id()
    if not channel_id:
        print("❌ 채널 ID를 가져올 수 없습니다.")
        return
    
    print()
    
    # 채널의 비디오 가져오기
    videos = updater.get_channel_videos(channel_id, max_results=args.max_videos)
    
    if not videos:
        print("❌ 비디오를 찾을 수 없습니다.")
        return
    
    # CSV 파일 확인
    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"❌ CSV 파일을 찾을 수 없습니다: {csv_path}")
        return
    
    # CSV 업데이트
    stats = updater.update_csv(str(csv_path), videos, dry_run=args.dry_run)
    
    # 결과 요약
    print("=" * 60)
    print("📊 업데이트 결과 요약")
    print("=" * 60)
    print(f"✅ 새로 업데이트된 책: {len(stats['updated'])}개")
    print(f"⏭️ 이미 업로드된 책: {len(stats['already_uploaded'])}개")
    print(f"❓ 매칭 실패한 비디오: {len(stats['not_found'])}개")
    print()
    
    if stats['updated']:
        print("📝 업데이트된 책 목록:")
        for item in stats['updated']:
            print(f"   • {item['book']} ({item['date']})")
            print(f"     {item['url']}")
        print()
    
    if stats['not_found']:
        print("❓ 매칭 실패한 비디오:")
        for item in stats['not_found'][:10]:  # 최대 10개만 표시
            print(f"   • {item['video'][:60]}...")
            if item['extracted_title']:
                print(f"     추출된 제목: {item['extracted_title']}")
        if len(stats['not_found']) > 10:
            print(f"   ... 외 {len(stats['not_found']) - 10}개")
        print()
    
    if args.dry_run:
        print("💡 실제로 업데이트하려면 --dry-run 옵션을 제거하세요.")
    else:
        print("✅ 완료!")


if __name__ == "__main__":
    main()

