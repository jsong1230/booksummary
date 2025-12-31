"""
최적 업로드 시간대 분석 스크립트

업로드 로그와 YouTube Analytics 데이터를 결합하여
최적의 업로드 시간대를 분석합니다.

분석 항목:
- 요일별 업로드 성과
- 시간대별 업로드 성과
- 업로드 후 24시간/48시간 조회수 성장률
- 최적 업로드 시간대 추천
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


class OptimalUploadTimeAnalyzer:
    """최적 업로드 시간대 분석 클래스"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.analytics = None
        if ANALYTICS_AVAILABLE:
            try:
                self.analytics = YouTubeAnalytics()
            except Exception as e:
                self.logger.warning(f"YouTube Analytics 초기화 실패: {e}")
    
    def load_upload_log(self, log_path: str = "output/upload_log.json") -> List[Dict]:
        """업로드 로그 로드"""
        log_file = Path(log_path)
        if not log_file.exists():
            self.logger.warning(f"업로드 로그 파일을 찾을 수 없습니다: {log_path}")
            self.logger.info("💡 업로드 로그 파일이 없습니다. 다음 방법으로 생성할 수 있습니다:")
            self.logger.info("   1. YouTube에 영상을 업로드하면 자동으로 생성됩니다:")
            self.logger.info("      python src/09_upload_from_metadata.py --privacy private --auto")
            self.logger.info("   2. 또는 기존 업로드 로그 파일이 다른 위치에 있는 경우:")
            self.logger.info("      python src/18_analyze_optimal_upload_time.py --upload-log <경로>")
            return []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 리스트 형식인지 딕셔너리 형식인지 확인
            if isinstance(data, list):
                uploads = data
            elif isinstance(data, dict) and 'uploads' in data:
                uploads = data['uploads']
            else:
                uploads = []
            
            self.logger.info(f"✅ 업로드 로그 로드 완료: {len(uploads)}개 영상")
            return uploads
        except Exception as e:
            self.logger.error(f"업로드 로그 로드 실패: {e}")
            return []
    
    def parse_upload_time(self, upload_entry: Dict) -> Optional[Tuple[datetime, str, int]]:
        """
        업로드 시간 파싱
        
        Returns:
            (datetime, video_id, weekday) 튜플
            weekday: 0=월요일, 6=일요일
        """
        # 여러 필드에서 업로드 시간 찾기
        upload_time_str = (
            upload_entry.get('uploaded_at') or
            upload_entry.get('published_at') or
            upload_entry.get('publishedAt') or
            upload_entry.get('timestamp')
        )
        
        if not upload_time_str:
            return None
        
        try:
            # ISO 형식 파싱
            if 'T' in upload_time_str:
                upload_time = datetime.fromisoformat(upload_time_str.replace('Z', '+00:00'))
            else:
                upload_time = datetime.strptime(upload_time_str, '%Y-%m-%d %H:%M:%S')
            
            # 로컬 시간대로 변환 (UTC가 아닌 경우)
            if upload_time.tzinfo is None:
                # 타임존 정보가 없으면 그대로 사용
                pass
            
            weekday = upload_time.weekday()  # 0=월요일, 6=일요일
            video_id = upload_entry.get('video_id') or upload_entry.get('id', '')
            
            return (upload_time, video_id, weekday)
        except Exception as e:
            self.logger.warning(f"업로드 시간 파싱 실패: {upload_time_str}, {e}")
            return None
    
    def get_video_early_metrics(
        self,
        video_id: str,
        upload_time: datetime,
        hours: int = 24
    ) -> Optional[Dict]:
        """
        영상 업로드 후 초기 메트릭 가져오기
        
        Args:
            video_id: 영상 ID
            upload_time: 업로드 시간
            hours: 분석할 시간 (기본값: 24시간)
        
        Returns:
            메트릭 딕셔너리 (views, likes, comments 등)
        """
        if not self.analytics:
            return None
        
        try:
            start_date = upload_time.strftime('%Y-%m-%d')
            end_time = upload_time + timedelta(hours=hours)
            end_date = end_time.strftime('%Y-%m-%d')
            
            metrics = self.analytics.get_video_metrics(
                video_id=video_id,
                start_date=start_date,
                end_date=end_date
            )
            
            return metrics
        except Exception as e:
            self.logger.warning(f"영상 메트릭 가져오기 실패 ({video_id}): {e}")
            return None
    
    def analyze_by_weekday(self, uploads: List[Dict]) -> Dict:
        """요일별 업로드 성과 분석"""
        weekday_stats = defaultdict(lambda: {
            'count': 0,
            'total_views_24h': 0,
            'total_views_48h': 0,
            'total_likes_24h': 0,
            'avg_views_24h': 0,
            'avg_views_48h': 0,
            'avg_likes_24h': 0,
            'videos': []
        })
        
        weekday_names = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
        
        for upload in uploads:
            parsed = self.parse_upload_time(upload)
            if not parsed:
                continue
            
            upload_time, video_id, weekday = parsed
            
            # 초기 메트릭 가져오기
            metrics_24h = self.get_video_early_metrics(video_id, upload_time, hours=24)
            metrics_48h = self.get_video_early_metrics(video_id, upload_time, hours=48)
            
            stats = weekday_stats[weekday]
            stats['count'] += 1
            stats['videos'].append({
                'video_id': video_id,
                'title': upload.get('title', 'N/A'),
                'upload_time': upload_time.isoformat()
            })
            
            if metrics_24h:
                views_24h = metrics_24h.get('views', 0)
                likes_24h = metrics_24h.get('likes', 0)
                stats['total_views_24h'] += views_24h
                stats['total_likes_24h'] += likes_24h
            
            if metrics_48h:
                views_48h = metrics_48h.get('views', 0)
                stats['total_views_48h'] += views_48h
        
        # 평균 계산
        for weekday, stats in weekday_stats.items():
            if stats['count'] > 0:
                stats['avg_views_24h'] = stats['total_views_24h'] / stats['count']
                stats['avg_views_48h'] = stats['total_views_48h'] / stats['count']
                stats['avg_likes_24h'] = stats['total_likes_24h'] / stats['count']
                stats['weekday_name'] = weekday_names[weekday]
        
        return dict(weekday_stats)
    
    def analyze_by_hour(self, uploads: List[Dict]) -> Dict:
        """시간대별 업로드 성과 분석"""
        hour_stats = defaultdict(lambda: {
            'count': 0,
            'total_views_24h': 0,
            'total_views_48h': 0,
            'total_likes_24h': 0,
            'avg_views_24h': 0,
            'avg_views_48h': 0,
            'avg_likes_24h': 0,
            'videos': []
        })
        
        for upload in uploads:
            parsed = self.parse_upload_time(upload)
            if not parsed:
                continue
            
            upload_time, video_id, weekday = parsed
            hour = upload_time.hour
            
            # 초기 메트릭 가져오기
            metrics_24h = self.get_video_early_metrics(video_id, upload_time, hours=24)
            metrics_48h = self.get_video_early_metrics(video_id, upload_time, hours=48)
            
            stats = hour_stats[hour]
            stats['count'] += 1
            stats['videos'].append({
                'video_id': video_id,
                'title': upload.get('title', 'N/A'),
                'upload_time': upload_time.isoformat()
            })
            
            if metrics_24h:
                views_24h = metrics_24h.get('views', 0)
                likes_24h = metrics_24h.get('likes', 0)
                stats['total_views_24h'] += views_24h
                stats['total_likes_24h'] += likes_24h
            
            if metrics_48h:
                views_48h = metrics_48h.get('views', 0)
                stats['total_views_48h'] += views_48h
        
        # 평균 계산
        for hour, stats in hour_stats.items():
            if stats['count'] > 0:
                stats['avg_views_24h'] = stats['total_views_24h'] / stats['count']
                stats['avg_views_48h'] = stats['total_views_48h'] / stats['count']
                stats['avg_likes_24h'] = stats['total_likes_24h'] / stats['count']
        
        return dict(hour_stats)
    
    def generate_report(
        self,
        weekday_stats: Dict,
        hour_stats: Dict,
        output_path: str = "output/optimal_upload_time_analysis.md"
    ) -> str:
        """분석 리포트 생성"""
        report_lines = []
        report_lines.append("# 최적 업로드 시간대 분석 리포트")
        report_lines.append("")
        report_lines.append(f"**생성 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # 요일별 분석
        report_lines.append("## 📅 요일별 업로드 성과")
        report_lines.append("")
        report_lines.append("| 요일 | 업로드 수 | 평균 조회수 (24h) | 평균 조회수 (48h) | 평균 좋아요 (24h) |")
        report_lines.append("|------|----------|------------------|------------------|------------------|")
        
        sorted_weekdays = sorted(weekday_stats.items(), key=lambda x: x[1]['avg_views_24h'], reverse=True)
        for weekday, stats in sorted_weekdays:
            if stats['count'] > 0:
                report_lines.append(
                    f"| {stats['weekday_name']} | {stats['count']}개 | "
                    f"{stats['avg_views_24h']:.1f} | {stats['avg_views_48h']:.1f} | "
                    f"{stats['avg_likes_24h']:.1f} |"
                )
        
        report_lines.append("")
        
        # 시간대별 분석
        report_lines.append("## ⏰ 시간대별 업로드 성과")
        report_lines.append("")
        report_lines.append("| 시간 | 업로드 수 | 평균 조회수 (24h) | 평균 조회수 (48h) | 평균 좋아요 (24h) |")
        report_lines.append("|------|----------|------------------|------------------|------------------|")
        
        sorted_hours = sorted(hour_stats.items(), key=lambda x: x[1]['avg_views_24h'], reverse=True)
        for hour, stats in sorted_hours:
            if stats['count'] > 0:
                report_lines.append(
                    f"| {hour:02d}:00 | {stats['count']}개 | "
                    f"{stats['avg_views_24h']:.1f} | {stats['avg_views_48h']:.1f} | "
                    f"{stats['avg_likes_24h']:.1f} |"
                )
        
        report_lines.append("")
        
        # 최적 업로드 시간 추천
        report_lines.append("## 🎯 최적 업로드 시간 추천")
        report_lines.append("")
        
        if sorted_weekdays:
            best_weekday = sorted_weekdays[0]
            report_lines.append(f"### 최적 업로드 요일: **{best_weekday[1]['weekday_name']}**")
            report_lines.append(f"- 평균 조회수 (24h): {best_weekday[1]['avg_views_24h']:.1f}")
            report_lines.append(f"- 평균 조회수 (48h): {best_weekday[1]['avg_views_48h']:.1f}")
            report_lines.append("")
        
        if sorted_hours:
            best_hour = sorted_hours[0]
            report_lines.append(f"### 최적 업로드 시간: **{best_hour[0]:02d}:00**")
            report_lines.append(f"- 평균 조회수 (24h): {best_hour[1]['avg_views_24h']:.1f}")
            report_lines.append(f"- 평균 조회수 (48h): {best_hour[1]['avg_views_48h']:.1f}")
            report_lines.append("")
        
        # 상위 3개 시간대 추천
        report_lines.append("### 추천 업로드 시간대 (상위 3개)")
        report_lines.append("")
        for i, (hour, stats) in enumerate(sorted_hours[:3], 1):
            if stats['count'] > 0:
                report_lines.append(f"{i}. **{hour:02d}:00** - 평균 조회수 (24h): {stats['avg_views_24h']:.1f}")
        report_lines.append("")
        
        report_lines.append("---")
        report_lines.append("")
        report_lines.append("**참고**: 이 분석은 업로드 후 24시간/48시간 내 초기 성과를 기준으로 합니다.")
        report_lines.append("실제 최적 시간대는 채널의 타겟 시청자층과 콘텐츠 특성에 따라 달라질 수 있습니다.")
        
        # 리포트 저장
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        self.logger.info(f"✅ 분석 리포트 생성 완료: {output_path}")
        return output_path


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='최적 업로드 시간대 분석')
    parser.add_argument('--upload-log', type=str, default='output/upload_log.json', help='업로드 로그 파일 경로')
    parser.add_argument('--output', type=str, default='output/optimal_upload_time_analysis.md', help='출력 리포트 파일 경로')
    
    args = parser.parse_args()
    
    analyzer = OptimalUploadTimeAnalyzer()
    
    # 업로드 로그 로드
    uploads = analyzer.load_upload_log(args.upload_log)
    
    if not uploads:
        print("❌ 분석할 업로드 데이터가 없습니다.")
        return
    
    print(f"📊 {len(uploads)}개 영상 분석 시작...")
    
    # 요일별 분석
    print("📅 요일별 성과 분석 중...")
    weekday_stats = analyzer.analyze_by_weekday(uploads)
    
    # 시간대별 분석
    print("⏰ 시간대별 성과 분석 중...")
    hour_stats = analyzer.analyze_by_hour(uploads)
    
    # 리포트 생성
    print("📝 리포트 생성 중...")
    report_path = analyzer.generate_report(weekday_stats, hour_stats, args.output)
    
    print(f"✅ 분석 완료: {report_path}")


if __name__ == "__main__":
    main()

