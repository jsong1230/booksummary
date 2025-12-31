"""
YouTube Analytics 대시보드 생성

HTML 기반 대시보드로 채널 및 영상 메트릭을 시각화합니다.
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from dotenv import load_dotenv

import importlib.util

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "src"))

from utils.logger import get_logger

load_dotenv()


class DashboardGenerator:
    """대시보드 생성 클래스"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # YouTube Analytics 모듈 로드
        spec = importlib.util.spec_from_file_location(
            "youtube_analytics",
            project_root / "src" / "15_youtube_analytics.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        self.analytics = module.YouTubeAnalytics()
    
    def generate_dashboard(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        output_path: str = "output/dashboard.html"
    ) -> Optional[str]:
        """
        HTML 대시보드 생성
        
        Args:
            start_date: 시작 날짜 (YYYY-MM-DD 형식, 기본값: 30일 전)
            end_date: 종료 날짜 (YYYY-MM-DD 형식, 기본값: 오늘)
            output_path: 대시보드 출력 경로
        
        Returns:
            생성된 대시보드 파일 경로
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        self.logger.info(f"📊 대시보드 생성 중 ({start_date} ~ {end_date})")
        
        # 채널 정보 가져오기
        channel_id = self.analytics.get_channel_id()
        channel_info = None
        if channel_id:
            try:
                channel_response = self.analytics.youtube.channels().list(
                    part='snippet,statistics',
                    id=channel_id
                ).execute()
                if channel_response.get('items'):
                    channel_info = channel_response['items'][0]
            except Exception as e:
                self.logger.warning(f"채널 정보 가져오기 실패: {e}")
        
        # 채널 메트릭 수집 (Analytics API 사용 가능한 경우)
        channel_metrics = None
        if self.analytics.youtube_analytics:
            channel_metrics = self.analytics.get_channel_metrics(start_date, end_date)
        
        # 영상 목록 수집 (YouTube API에서 직접 가져오기)
        videos = []
        try:
            videos = self.analytics.get_channel_videos(max_results=100)
            self.logger.info(f"✅ YouTube API에서 {len(videos)}개 영상 정보 수집")
        except Exception as e:
            self.logger.warning(f"YouTube API에서 영상 목록 가져오기 실패: {e}")
            # 실패 시 업로드 로그에서 가져오기 시도
            videos = self._get_videos_from_upload_log()
        
        # YouTube API로 최신 통계 업데이트 시도 (이미 가져온 경우 스킵)
        if videos and not all(v.get('views', 0) > 0 for v in videos):
            try:
                video_ids = [v.get('video_id') for v in videos if v.get('video_id')]
                if video_ids:
                    # videos().list()는 업로드 스코프로도 작동할 수 있음
                    video_response = self.analytics.youtube.videos().list(
                        part='statistics,snippet',
                        id=','.join(video_ids[:50])  # 최대 50개씩
                    ).execute()
                    
                    # 통계 업데이트
                    stats_map = {}
                    for item in video_response.get('items', []):
                        stats_map[item['id']] = {
                            'views': int(item['statistics'].get('viewCount', 0)),
                            'likes': int(item['statistics'].get('likeCount', 0)),
                            'comments': int(item['statistics'].get('commentCount', 0)),
                            'published_at': item['snippet'].get('publishedAt', '')
                        }
                    
                    # 비디오 정보 업데이트
                    for video in videos:
                        video_id = video.get('video_id')
                        if video_id and video_id in stats_map:
                            video.update(stats_map[video_id])
            except Exception as e:
                self.logger.warning(f"최신 통계 업데이트 실패 (업로드 로그 데이터 사용): {e}")
        
        # 영상별 Analytics 메트릭 수집 (가능한 경우)
        video_analytics = {}
        if self.analytics.youtube_analytics and videos:
            for video in videos[:20]:  # 최대 20개만 (시간 절약)
                video_id = video.get('video_id')
                if video_id:
                    metrics = self.analytics.get_video_metrics(
                        video_id=video_id,
                        start_date=start_date,
                        end_date=end_date
                    )
                    if metrics:
                        video_analytics[video_id] = metrics
        
        # 대시보드 HTML 생성
        html = self._generate_html_dashboard(
            start_date=start_date,
            end_date=end_date,
            channel_id=channel_id,
            channel_info=channel_info,
            channel_metrics=channel_metrics,
            videos=videos,
            video_analytics=video_analytics
        )
        
        # 파일 저장
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.logger.info(f"💾 대시보드 저장: {output_file}")
        return str(output_file)
    
    def _get_videos_from_upload_log(self) -> List[Dict]:
        """업로드 로그에서 영상 정보 가져오기"""
        videos = []
        
        # JSON 로그에서 로드
        log_file = Path("output/upload_log.json")
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    upload_history = json.load(f)
                    for entry in upload_history:
                        video_id = entry.get('video_id', '')
                        if video_id:
                            videos.append({
                                'video_id': video_id,
                                'title': entry.get('title', 'N/A'),
                                'published_at': entry.get('uploaded_at', entry.get('published_at', '')),
                                'views': int(entry.get('views', 0)),
                                'likes': int(entry.get('likes', 0)),
                                'comments': int(entry.get('comments', 0)),
                                'url': f"https://www.youtube.com/watch?v={video_id}"
                            })
            except Exception as e:
                self.logger.warning(f"업로드 로그 JSON 읽기 실패: {e}")
        
        # CSV 로그에서도 로드
        csv_file = Path("output/upload_log.csv")
        if csv_file.exists():
            try:
                import csv as csv_module
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv_module.DictReader(f)
                    for row in reader:
                        video_id = row.get('video_id', '')
                        if video_id and not any(v.get('video_id') == video_id for v in videos):
                            videos.append({
                                'video_id': video_id,
                                'title': row.get('title', 'N/A'),
                                'published_at': row.get('uploaded_at', row.get('published_at', '')),
                                'views': int(row.get('views', 0) or 0),
                                'likes': int(row.get('likes', 0) or 0),
                                'comments': int(row.get('comments', 0) or 0),
                                'url': f"https://www.youtube.com/watch?v={video_id}"
                            })
            except Exception as e:
                self.logger.warning(f"업로드 로그 CSV 읽기 실패: {e}")
        
        if videos:
            self.logger.info(f"✅ 업로드 로그에서 {len(videos)}개 영상 정보 로드")
        else:
            self.logger.warning("업로드 로그에서 영상 정보를 찾을 수 없습니다.")
            self.logger.warning("   YouTube API의 youtube.readonly 스코프가 필요합니다.")
            self.logger.warning("   scripts/get_youtube_refresh_token.py를 실행하여 새 토큰을 생성하세요.")
        
        return videos
    
    def _generate_html_dashboard(
        self,
        start_date: str,
        end_date: str,
        channel_id: Optional[str],
        channel_info: Optional[Dict],
        channel_metrics: Optional[Dict],
        videos: List[Dict],
        video_analytics: Dict[str, Dict]
    ) -> str:
        """HTML 대시보드 생성"""
        
        # 채널 통계 계산
        total_views = sum(v.get('views', 0) for v in videos)
        total_likes = sum(v.get('likes', 0) for v in videos)
        total_comments = sum(v.get('comments', 0) for v in videos)
        avg_views = total_views / len(videos) if videos else 0
        
        # 조회수 상위 10개 영상
        top_videos = sorted(videos, key=lambda x: x.get('views', 0), reverse=True)[:10]
        
        # 최근 업로드 영상 (최대 10개)
        recent_videos = sorted(videos, key=lambda x: x.get('published_at', ''), reverse=True)[:10]
        
        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Analytics 대시보드</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        
        .header h1 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        
        .header .meta {{
            color: #666;
            font-size: 1.1em;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .stat-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-card h3 {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .stat-card .value {{
            color: #333;
            font-size: 2.5em;
            font-weight: bold;
        }}
        
        .stat-card .label {{
            color: #999;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        
        .section {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
        .section h2 {{
            color: #333;
            margin-bottom: 20px;
            font-size: 1.8em;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .video-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        .video-table th {{
            background: #f8f9fa;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #333;
            border-bottom: 2px solid #dee2e6;
        }}
        
        .video-table td {{
            padding: 15px;
            border-bottom: 1px solid #dee2e6;
        }}
        
        .video-table tr:hover {{
            background: #f8f9fa;
        }}
        
        .video-title {{
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }}
        
        .video-title:hover {{
            text-decoration: underline;
        }}
        
        .number {{
            text-align: right;
            font-family: 'Courier New', monospace;
        }}
        
        .chart-container {{
            position: relative;
            height: 400px;
            margin-top: 20px;
        }}
        
        .footer {{
            text-align: center;
            color: white;
            padding: 20px;
            margin-top: 20px;
        }}
        
        .badge {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
        }}
        
        .badge-success {{
            background: #28a745;
            color: white;
        }}
        
        .badge-warning {{
            background: #ffc107;
            color: #333;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 YouTube Analytics 대시보드</h1>
            <div class="meta">
                <strong>기간:</strong> {start_date} ~ {end_date}<br>
                <strong>생성 일시:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                {f'<strong>채널 ID:</strong> {channel_id}' if channel_id else ''}
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>총 영상 수</h3>
                <div class="value">{len(videos)}</div>
                <div class="label">개</div>
            </div>
            <div class="stat-card">
                <h3>총 조회수</h3>
                <div class="value">{total_views:,}</div>
                <div class="label">회</div>
            </div>
            <div class="stat-card">
                <h3>총 좋아요</h3>
                <div class="value">{total_likes:,}</div>
                <div class="label">개</div>
            </div>
            <div class="stat-card">
                <h3>총 댓글 수</h3>
                <div class="value">{total_comments:,}</div>
                <div class="label">개</div>
            </div>
            <div class="stat-card">
                <h3>평균 조회수</h3>
                <div class="value">{avg_views:,.0f}</div>
                <div class="label">회/영상</div>
            </div>
            {f'''
            <div class="stat-card">
                <h3>채널 구독자</h3>
                <div class="value">{channel_info.get("statistics", {}).get("subscriberCount", "N/A") if channel_info else "N/A"}</div>
                <div class="label">명</div>
            </div>
            ''' if channel_info else ''}
        </div>
        
        <div class="section">
            <h2>🔥 조회수 상위 10개 영상</h2>
            <table class="video-table">
                <thead>
                    <tr>
                        <th>순위</th>
                        <th>제목</th>
                        <th class="number">조회수</th>
                        <th class="number">좋아요</th>
                        <th class="number">댓글</th>
                        <th>링크</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        for i, video in enumerate(top_videos, 1):
            title = video.get('title', 'N/A')
            views = video.get('views', 0)
            likes = video.get('likes', 0)
            comments = video.get('comments', 0)
            url = video.get('url', '#')
            
            html += f"""
                    <tr>
                        <td>{i}</td>
                        <td><a href="{url}" target="_blank" class="video-title">{title[:60]}{'...' if len(title) > 60 else ''}</a></td>
                        <td class="number">{views:,}</td>
                        <td class="number">{likes:,}</td>
                        <td class="number">{comments:,}</td>
                        <td><a href="{url}" target="_blank">보기</a></td>
                    </tr>
"""
        
        html += """
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>📈 조회수 분포 차트</h2>
            <div class="chart-container">
                <canvas id="viewsChart"></canvas>
            </div>
        </div>
        
        <div class="section">
            <h2>📅 최근 업로드 영상</h2>
            <table class="video-table">
                <thead>
                    <tr>
                        <th>제목</th>
                        <th>업로드일</th>
                        <th class="number">조회수</th>
                        <th class="number">좋아요</th>
                        <th>링크</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        for video in recent_videos:
            title = video.get('title', 'N/A')
            published_at = video.get('published_at', '')
            if published_at:
                try:
                    pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    published_str = pub_date.strftime('%Y-%m-%d')
                except:
                    published_str = published_at[:10]
            else:
                published_str = 'N/A'
            views = video.get('views', 0)
            likes = video.get('likes', 0)
            url = video.get('url', '#')
            
            html += f"""
                    <tr>
                        <td><a href="{url}" target="_blank" class="video-title">{title[:60]}{'...' if len(title) > 60 else ''}</a></td>
                        <td>{published_str}</td>
                        <td class="number">{views:,}</td>
                        <td class="number">{likes:,}</td>
                        <td><a href="{url}" target="_blank">보기</a></td>
                    </tr>
"""
        
        # 차트 데이터 준비
        chart_labels = [v.get('title', 'N/A')[:30] + '...' if len(v.get('title', '')) > 30 else v.get('title', 'N/A') for v in top_videos]
        chart_views = [v.get('views', 0) for v in top_videos]
        
        html += f"""
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>이 대시보드는 YouTube Data API를 통해 자동으로 생성되었습니다.</p>
            <p>Analytics API 스코프가 필요한 경우 scripts/get_youtube_refresh_token.py를 실행하세요.</p>
        </div>
    </div>
    
    <script>
        // 조회수 차트
        const ctx = document.getElementById('viewsChart').getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(chart_labels, ensure_ascii=False)},
                datasets: [{{
                    label: '조회수',
                    data: {json.dumps(chart_views)},
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: false
                    }},
                    title: {{
                        display: true,
                        text: '조회수 상위 10개 영상'
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            callback: function(value) {{
                                return value.toLocaleString() + '회';
                            }}
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
        
        return html


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YouTube Analytics 대시보드 생성')
    parser.add_argument('--start-date', type=str, help='시작 날짜 (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='종료 날짜 (YYYY-MM-DD)')
    parser.add_argument('--output', type=str, default='output/dashboard.html', help='대시보드 출력 파일 경로')
    parser.add_argument('--open', action='store_true', help='생성 후 브라우저에서 자동 열기')
    
    args = parser.parse_args()
    
    try:
        generator = DashboardGenerator()
        dashboard_path = generator.generate_dashboard(
            start_date=args.start_date,
            end_date=args.end_date,
            output_path=args.output
        )
        
        if dashboard_path:
            print(f"✅ 대시보드 생성 완료: {dashboard_path}")
            
            if args.open:
                import webbrowser
                webbrowser.open(f"file://{Path(dashboard_path).absolute()}")
                print(f"🌐 브라우저에서 열기: {dashboard_path}")
        else:
            print("❌ 대시보드 생성 실패")
            return 1
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        print(traceback.format_exc())
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    exit(main())

