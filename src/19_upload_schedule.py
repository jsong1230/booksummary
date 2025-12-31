"""
정기 업로드 일정 수립 스크립트

최적 업로드 시간대 분석 결과를 기반으로
정기 업로드 일정을 생성하고 관리합니다.

기능:
- 주간 업로드 일정 생성
- 다음 업로드 날짜/시간 추천
- 업로드 일정 캘린더 생성
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger

load_dotenv()


class UploadScheduler:
    """정기 업로드 일정 관리 클래스"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.schedule_file = Path("output/upload_schedule.json")
        self.analysis_file = Path("output/optimal_upload_time_analysis.md")
    
    def load_optimal_time_analysis(self) -> Optional[Dict]:
        """최적 업로드 시간대 분석 결과 로드"""
        if not self.analysis_file.exists():
            self.logger.warning(f"분석 파일을 찾을 수 없습니다: {self.analysis_file}")
            self.logger.info("💡 먼저 최적 업로드 시간대 분석을 실행하세요:")
            self.logger.info("   python src/18_analyze_optimal_upload_time.py")
            return None
        
        # Markdown 파일에서 최적 시간 추출 (간단한 파싱)
        try:
            with open(self.analysis_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 최적 요일 추출
            best_weekday = None
            if "### 최적 업로드 요일:" in content:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if "### 최적 업로드 요일:" in line:
                        # 다음 줄에서 요일 추출
                        if i + 1 < len(lines):
                            weekday_line = lines[i + 1]
                            # "**월요일**" 형식에서 추출
                            if '**' in weekday_line:
                                best_weekday = weekday_line.split('**')[1]
            
            # 최적 시간 추출
            best_hour = None
            if "### 최적 업로드 시간:" in content:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if "### 최적 업로드 시간:" in line:
                        # 다음 줄에서 시간 추출
                        if i + 1 < len(lines):
                            hour_line = lines[i + 1]
                            # "**09:00**" 형식에서 추출
                            if '**' in hour_line:
                                hour_str = hour_line.split('**')[1]
                                try:
                                    best_hour = int(hour_str.split(':')[0])
                                except:
                                    pass
            
            if best_weekday or best_hour:
                return {
                    'best_weekday': best_weekday,
                    'best_hour': best_hour
                }
            else:
                # 기본값 사용
                return {
                    'best_weekday': '화요일',  # 일반적으로 화요일이 좋음
                    'best_hour': 9  # 오전 9시
                }
        except Exception as e:
            self.logger.warning(f"분석 파일 파싱 실패: {e}, 기본값 사용")
            return {
                'best_weekday': '화요일',
                'best_hour': 9
            }
    
    def weekday_name_to_number(self, weekday_name: str) -> int:
        """요일 이름을 숫자로 변환 (0=월요일)"""
        weekday_map = {
            '월요일': 0,
            '화요일': 1,
            '수요일': 2,
            '목요일': 3,
            '금요일': 4,
            '토요일': 5,
            '일요일': 6
        }
        return weekday_map.get(weekday_name, 1)  # 기본값: 화요일
    
    def generate_schedule(
        self,
        weeks: int = 4,
        uploads_per_week: int = 2,
        start_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        정기 업로드 일정 생성
        
        Args:
            weeks: 생성할 주 수 (기본값: 4주)
            uploads_per_week: 주당 업로드 수 (기본값: 2회)
            start_date: 시작 날짜 (기본값: 다음 주)
        
        Returns:
            업로드 일정 리스트
        """
        # 최적 시간대 로드
        optimal = self.load_optimal_time_analysis()
        if not optimal:
            optimal = {'best_weekday': '화요일', 'best_hour': 9}
        
        best_weekday_num = self.weekday_name_to_number(optimal['best_weekday'])
        best_hour = optimal.get('best_hour', 9)
        
        # 시작 날짜 설정
        if start_date is None:
            # 다음 주의 최적 요일로 설정
            today = datetime.now()
            days_ahead = best_weekday_num - today.weekday()
            if days_ahead <= 0:  # 이번 주가 지났으면 다음 주
                days_ahead += 7
            start_date = today + timedelta(days=days_ahead)
            start_date = start_date.replace(hour=best_hour, minute=0, second=0, microsecond=0)
        
        schedule = []
        current_date = start_date
        
        # 주당 업로드 수에 따라 요일 분배
        if uploads_per_week == 1:
            # 주 1회: 최적 요일만
            upload_weekdays = [best_weekday_num]
        elif uploads_per_week == 2:
            # 주 2회: 최적 요일 + 3일 후
            upload_weekdays = [best_weekday_num, (best_weekday_num + 3) % 7]
        elif uploads_per_week == 3:
            # 주 3회: 최적 요일 + 2일 후 + 4일 후
            upload_weekdays = [best_weekday_num, (best_weekday_num + 2) % 7, (best_weekday_num + 4) % 7]
        else:
            # 주 4회 이상: 균등 분배
            upload_weekdays = [
                (best_weekday_num + i * (7 // uploads_per_week)) % 7
                for i in range(uploads_per_week)
            ]
        
        weekday_names = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
        
        for week in range(weeks):
            for weekday_num in sorted(upload_weekdays):
                # 해당 주의 해당 요일 찾기
                days_offset = weekday_num - current_date.weekday()
                if days_offset < 0:
                    days_offset += 7
                
                upload_date = current_date + timedelta(days=days_offset)
                upload_date = upload_date.replace(hour=best_hour, minute=0, second=0, microsecond=0)
                
                schedule.append({
                    'date': upload_date.strftime('%Y-%m-%d'),
                    'time': upload_date.strftime('%H:%M'),
                    'weekday': weekday_names[weekday_num],
                    'week': week + 1,
                    'datetime': upload_date.isoformat()
                })
            
            # 다음 주로 이동
            current_date += timedelta(days=7)
        
        return schedule
    
    def save_schedule(self, schedule: List[Dict]) -> str:
        """업로드 일정 저장"""
        schedule_data = {
            'generated_at': datetime.now().isoformat(),
            'schedule': schedule
        }
        
        self.schedule_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.schedule_file, 'w', encoding='utf-8') as f:
            json.dump(schedule_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"✅ 업로드 일정 저장 완료: {self.schedule_file}")
        return str(self.schedule_file)
    
    def load_schedule(self) -> Optional[List[Dict]]:
        """저장된 업로드 일정 로드"""
        if not self.schedule_file.exists():
            return None
        
        try:
            with open(self.schedule_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('schedule', [])
        except Exception as e:
            self.logger.error(f"일정 로드 실패: {e}")
            return None
    
    def get_next_upload_date(self) -> Optional[Dict]:
        """다음 업로드 날짜/시간 가져오기"""
        schedule = self.load_schedule()
        if not schedule:
            return None
        
        now = datetime.now()
        for item in schedule:
            upload_datetime = datetime.fromisoformat(item['datetime'])
            if upload_datetime > now:
                return item
        
        return None
    
    def generate_calendar_view(self, schedule: List[Dict]) -> str:
        """캘린더 형식의 일정 보기 생성"""
        lines = []
        lines.append("# 📅 정기 업로드 일정")
        lines.append("")
        lines.append(f"**생성 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("## 업로드 일정")
        lines.append("")
        lines.append("| 날짜 | 요일 | 시간 | 주차 |")
        lines.append("|------|------|------|------|")
        
        for item in schedule:
            lines.append(
                f"| {item['date']} | {item['weekday']} | {item['time']} | {item['week']}주차 |"
            )
        
        lines.append("")
        
        # 다음 업로드 날짜
        next_upload = self.get_next_upload_date()
        if next_upload:
            lines.append("## 🎯 다음 업로드")
            lines.append("")
            lines.append(f"- **날짜**: {next_upload['date']} ({next_upload['weekday']})")
            lines.append(f"- **시간**: {next_upload['time']}")
            lines.append(f"- **주차**: {next_upload['week']}주차")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        lines.append("💡 이 일정은 최적 업로드 시간대 분석 결과를 기반으로 생성되었습니다.")
        lines.append("실제 업로드 시에는 콘텐츠 준비 상태와 일정을 고려하여 조정하세요.")
        
        return '\n'.join(lines)
    
    def save_calendar_view(self, schedule: List[Dict], output_path: str = "output/upload_schedule_calendar.md") -> str:
        """캘린더 형식 일정 저장"""
        calendar_content = self.generate_calendar_view(schedule)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(calendar_content)
        
        self.logger.info(f"✅ 캘린더 일정 저장 완료: {output_path}")
        return output_path


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='정기 업로드 일정 수립')
    parser.add_argument('--weeks', type=int, default=4, help='생성할 주 수 (기본값: 4주)')
    parser.add_argument('--uploads-per-week', type=int, default=2, help='주당 업로드 수 (기본값: 2회)')
    parser.add_argument('--start-date', type=str, help='시작 날짜 (YYYY-MM-DD 형식, 기본값: 다음 주 최적 요일)')
    parser.add_argument('--output-json', type=str, default='output/upload_schedule.json', help='JSON 출력 파일 경로')
    parser.add_argument('--output-calendar', type=str, default='output/upload_schedule_calendar.md', help='캘린더 출력 파일 경로')
    parser.add_argument('--show-next', action='store_true', help='다음 업로드 날짜만 표시')
    
    args = parser.parse_args()
    
    scheduler = UploadScheduler()
    
    # 다음 업로드 날짜만 표시
    if args.show_next:
        next_upload = scheduler.get_next_upload_date()
        if next_upload:
            print("🎯 다음 업로드 일정:")
            print(f"   날짜: {next_upload['date']} ({next_upload['weekday']})")
            print(f"   시간: {next_upload['time']}")
            print(f"   주차: {next_upload['week']}주차")
        else:
            print("❌ 다음 업로드 일정이 없습니다.")
            print("💡 일정을 먼저 생성하세요:")
            print("   python src/19_upload_schedule.py --weeks 4 --uploads-per-week 2")
        return
    
    # 시작 날짜 파싱
    start_date = None
    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        except ValueError:
            print(f"❌ 잘못된 날짜 형식: {args.start_date} (YYYY-MM-DD 형식 사용)")
            return
    
    # 일정 생성
    print(f"📅 업로드 일정 생성 중...")
    print(f"   기간: {args.weeks}주")
    print(f"   주당 업로드: {args.uploads_per_week}회")
    
    schedule = scheduler.generate_schedule(
        weeks=args.weeks,
        uploads_per_week=args.uploads_per_week,
        start_date=start_date
    )
    
    if not schedule:
        print("❌ 일정 생성 실패")
        return
    
    print(f"✅ {len(schedule)}개 업로드 일정 생성 완료")
    
    # 저장
    scheduler.schedule_file = Path(args.output_json)
    scheduler.save_schedule(schedule)
    
    # 캘린더 뷰 생성
    scheduler.save_calendar_view(schedule, args.output_calendar)
    
    # 다음 업로드 날짜 표시
    next_upload = scheduler.get_next_upload_date()
    if next_upload:
        print("")
        print("🎯 다음 업로드 일정:")
        print(f"   날짜: {next_upload['date']} ({next_upload['weekday']})")
        print(f"   시간: {next_upload['time']}")
        print(f"   주차: {next_upload['week']}주차")


if __name__ == "__main__":
    main()

