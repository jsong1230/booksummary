"""
YouTube Analytics API를 사용하여 채널 및 영상 메트릭 수집

YouTube Analytics API v2를 사용하여 다음 메트릭을 수집합니다:
- 조회수 (views)
- 좋아요 (likes)
- 댓글 수 (comments)
- 구독자 수 (subscribers)
- 시청 시간 (watchTime)
- 평균 시청 시간 (averageViewDuration)
"""

import os
import json
import csv
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from dotenv import load_dotenv

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

from utils.logger import get_logger

load_dotenv()

# YouTube Analytics API 스코프
SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/yt-analytics.readonly'
]


class YouTubeAnalytics:
    """YouTube Analytics API 클래스"""
    
    def __init__(self):
        if not GOOGLE_API_AVAILABLE:
            raise ImportError("google-api-python-client가 필요합니다.")
        
        self.logger = get_logger(__name__)
        self.client_id = os.getenv("YOUTUBE_CLIENT_ID")
        self.client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
        self.refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
        self.channel_id = os.getenv("YOUTUBE_CHANNEL_ID")
        
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            raise ValueError("YouTube API 자격증명이 설정되지 않았습니다.")
        
        self.youtube = None
        self.youtube_analytics = None
        self._authenticate()
    
    def _authenticate(self):
        """OAuth2 인증"""
        try:
            # 새로운 refresh token은 모든 필요한 스코프를 포함하고 있을 것으로 가정
            # 먼저 전체 스코프로 시도
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
                
                # YouTube Data API v3
                self.youtube = build('youtube', 'v3', credentials=credentials)
                
                # YouTube Analytics API v2
                self.youtube_analytics = build('youtubeAnalytics', 'v2', credentials=credentials)
                
                self.logger.info("✅ YouTube Data API 및 Analytics API 인증 성공")
            except Exception as full_scope_error:
                # 전체 스코프 실패 시, 개별 스코프로 시도
                self.logger.warning(f"전체 스코프 인증 실패, 개별 스코프로 재시도: {full_scope_error}")
                
                # YouTube Data API용 (readonly 또는 upload 스코프)
                data_api_scopes = [
                    'https://www.googleapis.com/auth/youtube.readonly',
                    'https://www.googleapis.com/auth/youtube.upload'
                ]
                
                for scope in data_api_scopes:
                    try:
                        credentials = Credentials(
                            token=None,
                            refresh_token=self.refresh_token,
                            token_uri="https://oauth2.googleapis.com/token",
                            client_id=self.client_id,
                            client_secret=self.client_secret,
                            scopes=[scope]
                        )
                        credentials.refresh(Request())
                        self.youtube = build('youtube', 'v3', credentials=credentials)
                        self.logger.info(f"✅ YouTube Data API 인증 성공 ({scope})")
                        break
                    except Exception:
                        continue
                else:
                    self.logger.error("❌ YouTube Data API 인증 실패")
                    raise
                
                # Analytics API 시도
                try:
                    analytics_credentials = Credentials(
                        token=None,
                        refresh_token=self.refresh_token,
                        token_uri="https://oauth2.googleapis.com/token",
                        client_id=self.client_id,
                        client_secret=self.client_secret,
                        scopes=SCOPES
                    )
                    analytics_credentials.refresh(Request())
                    self.youtube_analytics = build('youtubeAnalytics', 'v2', credentials=analytics_credentials)
                    self.logger.info("✅ YouTube Analytics API 인증 성공")
                except Exception as analytics_error:
                    self.logger.warning(f"⚠️ YouTube Analytics API 인증 실패: {analytics_error}")
                    self.logger.warning("   Analytics 스코프가 포함된 refresh token이 필요합니다.")
                    self.youtube_analytics = None
                
        except Exception as e:
            self.logger.error(f"❌ 인증 실패: {e}")
            raise
    
    def get_channel_id(self) -> Optional[str]:
        """채널 ID 가져오기"""
        if self.channel_id:
            return self.channel_id
        
        try:
            response = self.youtube.channels().list(
                part='id',
                mine=True
            ).execute()
            
            if response.get('items'):
                channel_id = response['items'][0]['id']
                self.logger.info(f"✅ 채널 ID: {channel_id}")
                return channel_id
            return None
        except Exception as e:
            self.logger.error(f"❌ 채널 ID 가져오기 실패: {e}")
            return None
    
    def get_channel_metrics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        metrics: List[str] = None
    ) -> Optional[Dict]:
        """
        채널 전체 메트릭 가져오기
        
        Args:
            start_date: 시작 날짜 (YYYY-MM-DD 형식, 기본값: 30일 전)
            end_date: 종료 날짜 (YYYY-MM-DD 형식, 기본값: 오늘)
            metrics: 수집할 메트릭 리스트 (기본값: views, likes, comments, subscribers)
        
        Returns:
            메트릭 데이터 딕셔너리
        """
        channel_id = self.get_channel_id()
        if not channel_id:
            self.logger.error("채널 ID를 가져올 수 없습니다.")
            return None
        
        # 기본값 설정
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        if metrics is None:
            # subscribers는 채널 레벨 메트릭이 아니므로 제외
            metrics = ['views', 'likes', 'comments', 'estimatedMinutesWatched', 'averageViewDuration']
        
        if not self.youtube_analytics:
            self.logger.error("YouTube Analytics API가 사용할 수 없습니다. Analytics 스코프가 필요합니다.")
            return None
        
        try:
            response = self.youtube_analytics.reports().query(
                ids=f'channel=={channel_id}',
                startDate=start_date,
                endDate=end_date,
                metrics=','.join(metrics)
            ).execute()
            
            self.logger.info(f"✅ 채널 메트릭 수집 완료 ({start_date} ~ {end_date})")
            return response
        except HttpError as e:
            self.logger.error(f"❌ 채널 메트릭 수집 실패: {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ 예상치 못한 오류: {e}")
            return None
    
    def get_video_metrics(
        self,
        video_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        metrics: List[str] = None
    ) -> Optional[Dict]:
        """
        특정 영상의 메트릭 가져오기
        
        Args:
            video_id: YouTube 영상 ID
            start_date: 시작 날짜 (YYYY-MM-DD 형식, 기본값: 영상 업로드 날짜)
            end_date: 종료 날짜 (YYYY-MM-DD 형식, 기본값: 오늘)
            metrics: 수집할 메트릭 리스트
        
        Returns:
            메트릭 데이터 딕셔너리
        """
        channel_id = self.get_channel_id()
        if not channel_id:
            self.logger.error("채널 ID를 가져올 수 없습니다.")
            return None
        
        # 기본값 설정
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if start_date is None:
            # 영상 업로드 날짜 가져오기
            try:
                video_response = self.youtube.videos().list(
                    part='snippet',
                    id=video_id
                ).execute()
                
                if video_response.get('items'):
                    published_at = video_response['items'][0]['snippet']['publishedAt']
                    start_date = published_at[:10]  # YYYY-MM-DD 형식으로 변환
                else:
                    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            except Exception as e:
                self.logger.warning(f"영상 업로드 날짜를 가져올 수 없습니다: {e}")
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        if metrics is None:
            metrics = ['views', 'likes', 'comments', 'estimatedMinutesWatched', 'averageViewDuration']
        
        if not self.youtube_analytics:
            self.logger.error("YouTube Analytics API가 사용할 수 없습니다. Analytics 스코프가 필요합니다.")
            return None
        
        try:
            response = self.youtube_analytics.reports().query(
                ids=f'channel=={channel_id}',
                filters=f'video=={video_id}',
                startDate=start_date,
                endDate=end_date,
                metrics=','.join(metrics)
            ).execute()
            
            self.logger.info(f"✅ 영상 메트릭 수집 완료 (video_id: {video_id})")
            return response
        except HttpError as e:
            self.logger.error(f"❌ 영상 메트릭 수집 실패: {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ 예상치 못한 오류: {e}")
            return None
    
    def get_channel_videos(self, max_results: int = 50) -> List[Dict]:
        """
        채널의 모든 영상 목록 가져오기
        
        Args:
            max_results: 최대 결과 수
        
        Returns:
            영상 정보 리스트
        """
        channel_id = self.get_channel_id()
        if not channel_id:
            self.logger.error("채널 ID를 가져올 수 없습니다.")
            return []
        
        try:
            videos = []
            next_page_token = None
            
            # 채널의 업로드 플레이리스트 ID 가져오기
            channel_response = self.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            ).execute()
            
            if not channel_response.get('items'):
                self.logger.error("채널을 찾을 수 없습니다.")
                return []
            
            upload_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # 플레이리스트에서 영상 목록 가져오기
            while len(videos) < max_results:
                request_params = {
                    'part': 'contentDetails',
                    'playlistId': upload_playlist_id,
                    'maxResults': min(50, max_results - len(videos))
                }
                
                if next_page_token:
                    request_params['pageToken'] = next_page_token
                
                playlist_response = self.youtube.playlistItems().list(**request_params).execute()
                
                # 영상 ID 목록 수집
                video_ids = []
                for item in playlist_response.get('items', []):
                    video_id = item['contentDetails']['videoId']
                    video_ids.append(video_id)
                
                if not video_ids:
                    break
                
                # 영상 상세 정보 일괄 가져오기
                video_response = self.youtube.videos().list(
                    part='id,snippet,statistics',
                    id=','.join(video_ids)
                ).execute()
                
                for video_info in video_response.get('items', []):
                    video_id = video_info['id']
                    videos.append({
                        'video_id': video_id,
                        'title': video_info['snippet']['title'],
                        'published_at': video_info['snippet']['publishedAt'],
                        'views': int(video_info['statistics'].get('viewCount', 0)),
                        'likes': int(video_info['statistics'].get('likeCount', 0)),
                        'comments': int(video_info['statistics'].get('commentCount', 0)),
                        'url': f"https://www.youtube.com/watch?v={video_id}"
                    })
                
                next_page_token = playlist_response.get('nextPageToken')
                if not next_page_token:
                    break
            
            self.logger.info(f"✅ 채널 영상 목록 수집 완료 ({len(videos)}개)")
            return videos
        except Exception as e:
            self.logger.error(f"❌ 채널 영상 목록 수집 실패: {e}")
            return []
    
    def collect_all_video_metrics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """
        채널의 모든 영상에 대한 메트릭 수집
        
        Args:
            start_date: 시작 날짜 (YYYY-MM-DD 형식)
            end_date: 종료 날짜 (YYYY-MM-DD 형식)
        
        Returns:
            영상별 메트릭 데이터 리스트
        """
        videos = self.get_channel_videos()
        all_metrics = []
        
        for video in videos:
            video_id = video['video_id']
            self.logger.info(f"영상 메트릭 수집 중: {video['title']}")
            
            metrics = self.get_video_metrics(
                video_id=video_id,
                start_date=start_date,
                end_date=end_date
            )
            
            if metrics:
                # 메트릭 데이터와 영상 정보 결합
                video_metrics = {
                    **video,
                    'analytics': metrics
                }
                all_metrics.append(video_metrics)
        
        self.logger.info(f"✅ 전체 영상 메트릭 수집 완료 ({len(all_metrics)}개)")
        return all_metrics
    
    def save_metrics_to_json(self, metrics: Dict, output_path: str = "output/youtube_metrics.json"):
        """메트릭 데이터를 JSON 파일로 저장"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2, default=str)
        
        self.logger.info(f"💾 메트릭 데이터 저장: {output_file}")
    
    def save_video_metrics_to_csv(
        self,
        video_metrics: List[Dict],
        output_path: str = "output/youtube_video_metrics.csv"
    ):
        """영상 메트릭 데이터를 CSV 파일로 저장"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # CSV 데이터 준비
        rows = []
        for video in video_metrics:
            row = {
                'video_id': video.get('video_id', ''),
                'title': video.get('title', ''),
                'published_at': video.get('published_at', ''),
                'url': video.get('url', ''),
                'views': video.get('views', 0),
                'likes': video.get('likes', 0),
                'comments': video.get('comments', 0)
            }
            
            # Analytics 데이터 추가
            analytics = video.get('analytics', {})
            if analytics and 'rows' in analytics:
                for metric_row in analytics['rows']:
                    # 메트릭 이름과 값 매핑
                    column_headers = analytics.get('columnHeaders', [])
                    for i, header in enumerate(column_headers):
                        metric_name = header.get('name', '')
                        if i < len(metric_row):
                            row[metric_name] = metric_row[i]
            
            rows.append(row)
        
        # CSV 저장
        if rows:
            fieldnames = set()
            for row in rows:
                fieldnames.update(row.keys())
            
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
                writer.writeheader()
                writer.writerows(rows)
            
            self.logger.info(f"💾 영상 메트릭 CSV 저장: {output_file} ({len(rows)}개 영상)")
    
    def generate_weekly_report(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        output_path: str = "output/weekly_report.md"
    ) -> Optional[str]:
        """
        주간 리포트 생성
        
        Args:
            start_date: 시작 날짜 (YYYY-MM-DD 형식, 기본값: 7일 전)
            end_date: 종료 날짜 (YYYY-MM-DD 형식, 기본값: 오늘)
            output_path: 리포트 출력 경로
        
        Returns:
            생성된 리포트 파일 경로
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        self.logger.info(f"📊 주간 리포트 생성 중 ({start_date} ~ {end_date})")
        
        # 채널 메트릭 수집
        channel_metrics = self.get_channel_metrics(start_date, end_date)
        video_metrics = self.collect_all_video_metrics(start_date, end_date)
        
        if not channel_metrics and not video_metrics:
            self.logger.warning("수집된 메트릭이 없습니다.")
            return None
        
        # 리포트 생성
        report = self._format_report(
            title="주간 리포트",
            start_date=start_date,
            end_date=end_date,
            channel_metrics=channel_metrics,
            video_metrics=video_metrics
        )
        
        # 파일 저장
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.info(f"💾 주간 리포트 저장: {output_file}")
        return str(output_file)
    
    def generate_monthly_report(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        output_path: str = "output/monthly_report.md"
    ) -> Optional[str]:
        """
        월간 리포트 생성
        
        Args:
            year: 연도 (기본값: 현재 연도)
            month: 월 (기본값: 현재 월)
            output_path: 리포트 출력 경로
        
        Returns:
            생성된 리포트 파일 경로
        """
        now = datetime.now()
        if year is None:
            year = now.year
        if month is None:
            month = now.month
        
        # 해당 월의 첫날과 마지막날 계산
        start_date = datetime(year, month, 1).strftime('%Y-%m-%d')
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        self.logger.info(f"📊 월간 리포트 생성 중 ({year}년 {month}월)")
        
        # 채널 메트릭 수집
        channel_metrics = self.get_channel_metrics(start_date, end_date_str)
        video_metrics = self.collect_all_video_metrics(start_date, end_date_str)
        
        if not channel_metrics and not video_metrics:
            self.logger.warning("수집된 메트릭이 없습니다.")
            return None
        
        # 리포트 생성
        report = self._format_report(
            title=f"{year}년 {month}월 월간 리포트",
            start_date=start_date,
            end_date=end_date_str,
            channel_metrics=channel_metrics,
            video_metrics=video_metrics
        )
        
        # 파일 저장
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.info(f"💾 월간 리포트 저장: {output_file}")
        return str(output_file)
    
    def _format_report(
        self,
        title: str,
        start_date: str,
        end_date: str,
        channel_metrics: Optional[Dict],
        video_metrics: List[Dict]
    ) -> str:
        """
        리포트 포맷팅
        
        Args:
            title: 리포트 제목
            start_date: 시작 날짜
            end_date: 종료 날짜
            channel_metrics: 채널 메트릭 데이터
            video_metrics: 영상별 메트릭 데이터
        
        Returns:
            포맷팅된 리포트 텍스트 (Markdown)
        """
        report_lines = []
        
        # 헤더
        report_lines.append(f"# {title}")
        report_lines.append("")
        report_lines.append(f"**기간**: {start_date} ~ {end_date}")
        report_lines.append(f"**생성 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        
        # 채널 전체 메트릭
        if channel_metrics:
            report_lines.append("## 📊 채널 전체 메트릭")
            report_lines.append("")
            
            if 'rows' in channel_metrics and channel_metrics['rows']:
                column_headers = channel_metrics.get('columnHeaders', [])
                row_data = channel_metrics['rows'][0]
                
                for i, header in enumerate(column_headers):
                    metric_name = header.get('name', '')
                    metric_value = row_data[i] if i < len(row_data) else 0
                    
                    # 메트릭 이름 한글화
                    metric_name_ko = {
                        'views': '조회수',
                        'likes': '좋아요',
                        'comments': '댓글 수',
                        'subscribers': '구독자 수',
                        'estimatedMinutesWatched': '시청 시간 (분)',
                        'averageViewDuration': '평균 시청 시간 (초)'
                    }.get(metric_name, metric_name)
                    
                    # 값 포맷팅
                    if isinstance(metric_value, (int, float)):
                        if metric_name == 'estimatedMinutesWatched':
                            hours = metric_value / 60
                            report_lines.append(f"- **{metric_name_ko}**: {metric_value:,.0f}분 ({hours:,.1f}시간)")
                        elif metric_name == 'averageViewDuration':
                            minutes = metric_value / 60
                            report_lines.append(f"- **{metric_name_ko}**: {metric_value:,.0f}초 ({minutes:,.1f}분)")
                        else:
                            report_lines.append(f"- **{metric_name_ko}**: {metric_value:,}")
                    else:
                        report_lines.append(f"- **{metric_name_ko}**: {metric_value}")
                
                report_lines.append("")
        
        # 영상별 메트릭
        if video_metrics:
            report_lines.append("## 📹 영상별 메트릭")
            report_lines.append("")
            report_lines.append(f"**총 영상 수**: {len(video_metrics)}개")
            report_lines.append("")
            
            # 조회수 기준 상위 10개 영상
            sorted_videos = sorted(
                video_metrics,
                key=lambda x: x.get('views', 0),
                reverse=True
            )[:10]
            
            report_lines.append("### 🔥 조회수 상위 10개 영상")
            report_lines.append("")
            report_lines.append("| 순위 | 제목 | 조회수 | 좋아요 | 댓글 | URL |")
            report_lines.append("|------|------|--------|--------|------|-----|")
            
            for i, video in enumerate(sorted_videos, 1):
                title = video.get('title', 'N/A')[:50]  # 제목 길이 제한
                views = video.get('views', 0)
                likes = video.get('likes', 0)
                comments = video.get('comments', 0)
                url = video.get('url', '')
                
                report_lines.append(f"| {i} | {title} | {views:,} | {likes:,} | {comments:,} | [링크]({url}) |")
            
            report_lines.append("")
            
            # 통계 요약
            total_views = sum(v.get('views', 0) for v in video_metrics)
            total_likes = sum(v.get('likes', 0) for v in video_metrics)
            total_comments = sum(v.get('comments', 0) for v in video_metrics)
            avg_views = total_views / len(video_metrics) if video_metrics else 0
            
            report_lines.append("### 📈 통계 요약")
            report_lines.append("")
            report_lines.append(f"- **총 조회수**: {total_views:,}")
            report_lines.append(f"- **총 좋아요**: {total_likes:,}")
            report_lines.append(f"- **총 댓글 수**: {total_comments:,}")
            report_lines.append(f"- **평균 조회수**: {avg_views:,.0f}")
            report_lines.append("")
        
        # 푸터
        report_lines.append("---")
        report_lines.append("")
        report_lines.append("*이 리포트는 YouTube Analytics API를 통해 자동으로 생성되었습니다.*")
        
        return "\n".join(report_lines)


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YouTube Analytics 메트릭 수집')
    parser.add_argument('--channel', action='store_true', help='채널 전체 메트릭 수집')
    parser.add_argument('--videos', action='store_true', help='모든 영상 메트릭 수집')
    parser.add_argument('--video-id', type=str, help='특정 영상 ID의 메트릭 수집')
    parser.add_argument('--start-date', type=str, help='시작 날짜 (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='종료 날짜 (YYYY-MM-DD)')
    parser.add_argument('--output-json', type=str, default='output/youtube_metrics.json', help='JSON 출력 파일 경로')
    parser.add_argument('--output-csv', type=str, default='output/youtube_video_metrics.csv', help='CSV 출력 파일 경로')
    parser.add_argument('--weekly-report', action='store_true', help='주간 리포트 생성')
    parser.add_argument('--monthly-report', action='store_true', help='월간 리포트 생성')
    parser.add_argument('--year', type=int, help='월간 리포트용 연도')
    parser.add_argument('--month', type=int, help='월간 리포트용 월')
    parser.add_argument('--report-output', type=str, help='리포트 출력 파일 경로')
    
    args = parser.parse_args()
    
    try:
        analytics = YouTubeAnalytics()
        
        if args.channel:
            # 채널 전체 메트릭
            metrics = analytics.get_channel_metrics(
                start_date=args.start_date,
                end_date=args.end_date
            )
            if metrics:
                analytics.save_metrics_to_json(metrics, args.output_json)
        
        elif args.videos:
            # 모든 영상 메트릭
            video_metrics = analytics.collect_all_video_metrics(
                start_date=args.start_date,
                end_date=args.end_date
            )
            if video_metrics:
                analytics.save_metrics_to_json(video_metrics, args.output_json)
                analytics.save_video_metrics_to_csv(video_metrics, args.output_csv)
        
        elif args.video_id:
            # 특정 영상 메트릭
            metrics = analytics.get_video_metrics(
                video_id=args.video_id,
                start_date=args.start_date,
                end_date=args.end_date
            )
            if metrics:
                analytics.save_metrics_to_json(metrics, args.output_json)
        
        elif args.weekly_report:
            # 주간 리포트 생성
            output_path = args.report_output or "output/weekly_report.md"
            report_path = analytics.generate_weekly_report(
                start_date=args.start_date,
                end_date=args.end_date,
                output_path=output_path
            )
            if report_path:
                print(f"✅ 주간 리포트 생성 완료: {report_path}")
        
        elif args.monthly_report:
            # 월간 리포트 생성
            output_path = args.report_output or "output/monthly_report.md"
            report_path = analytics.generate_monthly_report(
                year=args.year,
                month=args.month,
                output_path=output_path
            )
            if report_path:
                print(f"✅ 월간 리포트 생성 완료: {report_path}")
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

