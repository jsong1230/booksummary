"""
YouTube Analytics API 테스트 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_analytics():
    """Analytics API 테스트"""
    print("=" * 60)
    print("YouTube Analytics API 테스트")
    print("=" * 60)
    print()
    
    try:
        import importlib.util
        
        # utils.logger 로드
        utils_spec = importlib.util.spec_from_file_location(
            "logger",
            project_root / "src" / "utils" / "logger.py"
        )
        utils_module = importlib.util.module_from_spec(utils_spec)
        utils_spec.loader.exec_module(utils_module)
        get_logger = utils_module.get_logger
        logger = get_logger(__name__)
        
        # YouTube Analytics 모듈 로드 (숫자로 시작하는 모듈명은 직접 import 불가)
        spec = importlib.util.spec_from_file_location(
            "youtube_analytics",
            project_root / "src" / "15_youtube_analytics.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        YouTubeAnalytics = module.YouTubeAnalytics
        
        print("📊 YouTube Analytics 인스턴스 생성 중...")
        analytics = YouTubeAnalytics()
        
        print("\n✅ 인증 성공!")
        print()
        
        # 채널 ID 확인
        print("📺 채널 ID 확인 중...")
        channel_id = analytics.get_channel_id()
        if channel_id:
            print(f"✅ 채널 ID: {channel_id}")
        else:
            print("⚠️ 채널 ID를 가져올 수 없습니다.")
        
        print()
        
        # 채널 영상 목록 확인 (최대 5개만)
        print("📹 채널 영상 목록 확인 중 (최대 5개)...")
        videos = analytics.get_channel_videos(max_results=5)
        if videos:
            print(f"✅ 영상 {len(videos)}개 발견")
            for i, video in enumerate(videos, 1):
                print(f"  {i}. {video['title'][:50]}...")
                print(f"     조회수: {video['views']:,}, 좋아요: {video['likes']:,}")
        else:
            print("⚠️ 영상을 찾을 수 없습니다.")
        
        print()
        print("=" * 60)
        print("✅ Analytics API 테스트 완료!")
        print("=" * 60)
        
        return True
        
    except ImportError as e:
        print(f"❌ Import 오류: {e}")
        print("   필요한 패키지가 설치되어 있는지 확인하세요.")
        return False
    except ValueError as e:
        print(f"❌ 설정 오류: {e}")
        print("   .env 파일에 YouTube API 자격증명이 설정되어 있는지 확인하세요.")
        return False
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = test_analytics()
    sys.exit(0 if success else 1)

