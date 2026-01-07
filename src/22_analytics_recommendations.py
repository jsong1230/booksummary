"""
YouTube Analytics 기반 채널 개선 제안 스크립트

Analytics 데이터를 분석하여 채널 성과를 평가하고
구체적인 개선 제안을 생성합니다.

분석 항목:
- 채널 전체 성과 분석
- 영상별 성과 분석 (조회수, 좋아요, 댓글, 시청 시간)
- 태그/제목 최적화 제안
- 업로드 빈도 및 일정 분석
- 콘텐츠 전략 제안
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("youtube_analytics", Path(__file__).parent / "15_youtube_analytics.py")
    youtube_analytics_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(youtube_analytics_module)
    YouTubeAnalytics = youtube_analytics_module.YouTubeAnalytics
    ANALYTICS_AVAILABLE = True
except Exception as e:
    ANALYTICS_AVAILABLE = False
    print(f"⚠️ YouTube Analytics 모듈 로드 실패: {e}")

from utils.logger import get_logger

load_dotenv()


class AnalyticsRecommendations:
    """Analytics 기반 개선 제안 클래스"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.analytics = None
        if ANALYTICS_AVAILABLE:
            try:
                self.analytics = YouTubeAnalytics()
            except Exception as e:
                self.logger.warning(f"YouTube Analytics 초기화 실패: {e}")
    
    def analyze_channel_performance(
        self,
        days: int = 30,
        min_views: int = 100
    ) -> Dict:
        """
        채널 성과 분석
        
        Args:
            days: 분석 기간 (일)
            min_views: 최소 조회수 (이하 영상은 제외)
        
        Returns:
            분석 결과 딕셔너리
        """
        if not self.analytics:
            self.logger.error("Analytics API를 사용할 수 없습니다.")
            return {}
        
        self.logger.info(f"📊 채널 성과 분석 시작 (최근 {days}일)")
        
        # 채널 메트릭 수집
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        channel_metrics = self.analytics.get_channel_metrics(
            start_date=start_date,
            end_date=end_date
        )
        
        # 영상 목록 및 메트릭 수집
        videos = self.analytics.get_channel_videos(max_results=100)
        
        # 최근 N일 내 업로드된 영상만 필터링
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_videos = []
        for video in videos:
            published_at = datetime.fromisoformat(video['published_at'].replace('Z', '+00:00'))
            if published_at.replace(tzinfo=None) >= cutoff_date:
                recent_videos.append(video)
        
        self.logger.info(f"✅ 최근 {days}일 내 업로드된 영상: {len(recent_videos)}개")
        
        # 영상별 상세 메트릭 수집
        video_metrics_list = []
        for video in recent_videos:
            if video['views'] < min_views:
                continue
            
            metrics = self.analytics.get_video_metrics(
                video_id=video['video_id'],
                start_date=start_date,
                end_date=end_date
            )
            
            if metrics:
                video_metrics_list.append({
                    **video,
                    'metrics': metrics
                })
        
        # 분석 결과 구성
        analysis = {
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'days': days
            },
            'channel_metrics': channel_metrics,
            'video_count': len(recent_videos),
            'video_metrics': video_metrics_list,
            'analysis_date': datetime.now().isoformat()
        }
        
        return analysis
    
    def calculate_engagement_rate(self, video: Dict) -> float:
        """참여율 계산 (좋아요 + 댓글) / 조회수 * 100"""
        views = video.get('views', 0)
        likes = video.get('likes', 0)
        comments = video.get('comments', 0)
        
        if views == 0:
            return 0.0
        
        engagement = (likes + comments) / views * 100
        return round(engagement, 2)
    
    def calculate_retention_score(self, video: Dict) -> Optional[float]:
        """시청 유지율 점수 계산"""
        metrics = video.get('metrics', {})
        if not metrics:
            return None
        
        # averageViewDuration을 초 단위로 변환 (ISO 8601 형식)
        avg_duration_str = metrics.get('rows', [{}])[0] if metrics.get('rows') else {}
        # 실제로는 다른 방식으로 파싱해야 할 수 있음
        
        return None  # TODO: 시청 시간 데이터 파싱 구현
    
    def generate_recommendations(self, analysis: Dict) -> List[Dict]:
        """
        분석 결과를 바탕으로 개선 제안 생성
        
        Returns:
            제안 리스트 (우선순위별)
        """
        recommendations = []
        
        if not analysis or not analysis.get('video_metrics'):
            recommendations.append({
                'priority': 'high',
                'category': 'data',
                'title': '데이터 수집 필요',
                'description': 'Analytics 데이터를 수집할 수 없습니다. 먼저 데이터를 수집해주세요.',
                'action': 'python src/15_youtube_analytics.py --videos'
            })
            return recommendations
        
        videos = analysis['video_metrics']
        if not videos:
            recommendations.append({
                'priority': 'medium',
                'category': 'content',
                'title': '콘텐츠 부족',
                'description': f"최근 {analysis['period']['days']}일 내 업로드된 영상이 없습니다.",
                'action': '정기적인 업로드 일정을 수립하세요.'
            })
            return recommendations
        
        # 1. 조회수 분석
        views_list = [v.get('views', 0) for v in videos]
        avg_views = sum(views_list) / len(views_list) if views_list else 0
        max_views = max(views_list) if views_list else 0
        min_views = min(views_list) if views_list else 0
        
        low_performing = [v for v in videos if v.get('views', 0) < avg_views * 0.5]
        high_performing = [v for v in videos if v.get('views', 0) > avg_views * 1.5]
        
        if low_performing:
            recommendations.append({
                'priority': 'high',
                'category': 'performance',
                'title': f'저성과 영상 {len(low_performing)}개 발견',
                'description': f'평균 조회수({avg_views:.0f})의 50% 미만인 영상이 {len(low_performing)}개 있습니다.',
                'action': f'저성과 영상의 제목, 썸네일, 태그를 분석하여 개선하세요.',
                'videos': [{'title': v.get('title', 'N/A'), 'views': v.get('views', 0), 'url': v.get('url', '')} for v in low_performing[:5]]
            })
        
        if high_performing:
            recommendations.append({
                'priority': 'medium',
                'category': 'strategy',
                'title': f'고성과 영상 {len(high_performing)}개 발견',
                'description': f'평균 조회수({avg_views:.0f})의 150% 이상인 영상이 {len(high_performing)}개 있습니다.',
                'action': '고성과 영상의 공통점(제목, 태그, 업로드 시간 등)을 분석하여 다른 영상에도 적용하세요.',
                'videos': [{'title': v.get('title', 'N/A'), 'views': v.get('views', 0), 'url': v.get('url', '')} for v in high_performing[:5]]
            })
        
        # 2. 참여율 분석
        engagement_rates = []
        for video in videos:
            rate = self.calculate_engagement_rate(video)
            engagement_rates.append((video, rate))
        
        engagement_rates.sort(key=lambda x: x[1], reverse=True)
        avg_engagement = sum(rate for _, rate in engagement_rates) / len(engagement_rates) if engagement_rates else 0
        
        low_engagement = [v for v, rate in engagement_rates if rate < avg_engagement * 0.7]
        
        if low_engagement:
            recommendations.append({
                'priority': 'high',
                'category': 'engagement',
                'title': f'낮은 참여율 영상 {len(low_engagement)}개',
                'description': f'평균 참여율({avg_engagement:.2f}%)보다 낮은 영상이 {len(low_engagement)}개 있습니다.',
                'action': '좋아요/댓글을 유도하는 콘텐츠나 CTA를 추가하세요.',
                'videos': [{'title': v.get('title', 'N/A'), 'engagement': self.calculate_engagement_rate(v), 'url': v.get('url', '')} for v in low_engagement[:5]]
            })
        
        # 3. 업로드 빈도 분석
        upload_dates = []
        for video in videos:
            published_at = video.get('published_at', '')
            if published_at:
                try:
                    date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    upload_dates.append(date.replace(tzinfo=None))
                except:
                    pass
        
        if len(upload_dates) > 1:
            upload_dates.sort()
            intervals = []
            for i in range(1, len(upload_dates)):
                interval = (upload_dates[i] - upload_dates[i-1]).days
                intervals.append(interval)
            
            avg_interval = sum(intervals) / len(intervals) if intervals else 0
            
            if avg_interval > 7:
                recommendations.append({
                    'priority': 'medium',
                    'category': 'schedule',
                    'title': '업로드 빈도 개선 필요',
                    'description': f'평균 업로드 간격이 {avg_interval:.1f}일입니다. 정기적인 업로드가 알고리즘에 유리합니다.',
                    'action': '주 1-2회 정기 업로드 일정을 수립하세요. (python src/19_upload_schedule.py)'
                })
            elif avg_interval < 2:
                recommendations.append({
                    'priority': 'low',
                    'category': 'schedule',
                    'title': '업로드 빈도 적절',
                    'description': f'평균 업로드 간격이 {avg_interval:.1f}일로 적절합니다.',
                    'action': '현재 업로드 빈도를 유지하세요.'
                })
        
        # 4. 조회수 분포 분석
        if len(views_list) >= 5:
            views_sorted = sorted(views_list, reverse=True)
            top_20_percent = views_sorted[:max(1, len(views_sorted) // 5)]
            bottom_20_percent = views_sorted[-max(1, len(views_sorted) // 5):]
            
            top_avg = sum(top_20_percent) / len(top_20_percent) if top_20_percent else 0
            bottom_avg = sum(bottom_20_percent) / len(bottom_20_percent) if bottom_20_percent else 0
            
            if top_avg > 0 and bottom_avg > 0:
                ratio = top_avg / bottom_avg
                if ratio > 5:
                    recommendations.append({
                        'priority': 'medium',
                        'category': 'consistency',
                        'title': '조회수 편차가 큼',
                        'description': f'상위 20% 영상의 평균 조회수가 하위 20%의 {ratio:.1f}배입니다.',
                        'action': '모든 영상의 품질을 일관되게 유지하고, 저성과 영상의 개선점을 찾아보세요.'
                    })
        
        # 5. 콘텐츠 전략 제안
        if high_performing:
            recommendations.append({
                'priority': 'medium',
                'category': 'strategy',
                'title': '고성과 콘텐츠 확장',
                'description': f'고성과 영상 {len(high_performing)}개를 기반으로 시리즈나 관련 콘텐츠를 제작하세요.',
                'action': '고성과 영상의 주제, 형식, 스타일을 분석하여 유사한 콘텐츠를 더 제작하세요.'
            })
        
        return recommendations
    
    def generate_report(
        self,
        analysis: Dict,
        recommendations: List[Dict],
        output_path: str = "output/analytics_recommendations.md"
    ) -> str:
        """분석 리포트 및 제안 생성"""
        report_lines = []
        report_lines.append("# 📊 YouTube Analytics 기반 채널 개선 제안")
        report_lines.append("")
        report_lines.append(f"**생성 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # 분석 기간
        period = analysis.get('period', {})
        report_lines.append(f"**분석 기간**: {period.get('start_date', 'N/A')} ~ {period.get('end_date', 'N/A')} ({period.get('days', 0)}일)")
        report_lines.append("")
        
        # 채널 요약
        report_lines.append("## 📈 채널 요약")
        report_lines.append("")
        report_lines.append(f"- **분석 영상 수**: {analysis.get('video_count', 0)}개")
        report_lines.append("")
        
        # 영상별 성과
        videos = analysis.get('video_metrics', [])
        if videos:
            report_lines.append("## 🎬 영상별 성과")
            report_lines.append("")
            report_lines.append("| 제목 | 조회수 | 좋아요 | 댓글 | 참여율 |")
            report_lines.append("|------|--------|--------|------|--------|")
            
            # 조회수 순으로 정렬
            videos_sorted = sorted(videos, key=lambda v: v.get('views', 0), reverse=True)
            
            for video in videos_sorted[:20]:  # 상위 20개만 표시
                title = video.get('title', 'N/A')[:50]  # 제목 길이 제한
                views = video.get('views', 0)
                likes = video.get('likes', 0)
                comments = video.get('comments', 0)
                engagement = self.calculate_engagement_rate(video)
                
                report_lines.append(f"| {title} | {views:,} | {likes:,} | {comments:,} | {engagement:.2f}% |")
            
            report_lines.append("")
        
        # 개선 제안
        report_lines.append("## 💡 개선 제안")
        report_lines.append("")
        
        # 우선순위별로 정렬
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        recommendations_sorted = sorted(
            recommendations,
            key=lambda r: (priority_order.get(r.get('priority', 'low'), 2), r.get('title', ''))
        )
        
        for i, rec in enumerate(recommendations_sorted, 1):
            priority = rec.get('priority', 'medium')
            priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(priority, '🟡')
            category = rec.get('category', 'general')
            
            report_lines.append(f"### {i}. {priority_emoji} {rec.get('title', 'N/A')}")
            report_lines.append("")
            report_lines.append(f"**카테고리**: {category}")
            report_lines.append("")
            report_lines.append(f"**설명**: {rec.get('description', 'N/A')}")
            report_lines.append("")
            report_lines.append(f"**액션**: {rec.get('action', 'N/A')}")
            report_lines.append("")
            
            # 관련 영상이 있으면 표시
            videos_list = rec.get('videos', [])
            if videos_list:
                report_lines.append("**관련 영상**:")
                report_lines.append("")
                for vid in videos_list:
                    title = vid.get('title', 'N/A')
                    url = vid.get('url', '')
                    views = vid.get('views', 0)
                    engagement = vid.get('engagement', '')
                    
                    if url:
                        report_lines.append(f"- [{title}]({url}) - 조회수: {views:,}" + (f", 참여율: {engagement}%" if engagement else ""))
                    else:
                        report_lines.append(f"- {title} - 조회수: {views:,}" + (f", 참여율: {engagement}%" if engagement else ""))
                report_lines.append("")
        
        # 리포트 저장
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        self.logger.info(f"✅ 리포트 생성 완료: {output_file}")
        return str(output_file)


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YouTube Analytics 기반 채널 개선 제안')
    parser.add_argument('--days', type=int, default=30, help='분석 기간 (일, 기본값: 30)')
    parser.add_argument('--min-views', type=int, default=100, help='최소 조회수 (이하 영상 제외, 기본값: 100)')
    parser.add_argument('--output', type=str, default='output/analytics_recommendations.md', help='리포트 출력 파일 경로')
    
    args = parser.parse_args()
    
    try:
        recommender = AnalyticsRecommendations()
        
        if not recommender.analytics:
            print("❌ YouTube Analytics API를 사용할 수 없습니다.")
            print("💡 다음을 확인해주세요:")
            print("   1. .env 파일에 YouTube API 자격증명이 설정되어 있는지")
            print("   2. YouTube Analytics API 스코프가 포함된 refresh token인지")
            print("   3. python src/15_youtube_analytics.py --videos 로 데이터 수집이 가능한지")
            return
        
        # 분석 실행
        print(f"📊 채널 성과 분석 시작 (최근 {args.days}일)...")
        analysis = recommender.analyze_channel_performance(
            days=args.days,
            min_views=args.min_views
        )
        
        if not analysis:
            print("❌ 분석 데이터를 수집할 수 없습니다.")
            return
        
        # 제안 생성
        print("💡 개선 제안 생성 중...")
        recommendations = recommender.generate_recommendations(analysis)
        
        # 리포트 생성
        print("📝 리포트 생성 중...")
        report_path = recommender.generate_report(analysis, recommendations, args.output)
        
        print("")
        print("=" * 60)
        print("✅ 분석 및 제안 생성 완료")
        print("=" * 60)
        print(f"📄 리포트 파일: {report_path}")
        print(f"💡 제안 수: {len(recommendations)}개")
        print("")
        print("주요 제안:")
        for i, rec in enumerate(recommendations[:5], 1):
            priority = rec.get('priority', 'medium')
            priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(priority, '🟡')
            print(f"  {i}. {priority_emoji} {rec.get('title', 'N/A')}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()








