"""
로깅 시스템 테스트 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import setup_logger, get_logger

def test_logging():
    """로깅 시스템 테스트"""
    print("=" * 60)
    print("로깅 시스템 테스트")
    print("=" * 60)
    print()
    
    # 로거 생성
    logger = setup_logger('test_logging', log_level='DEBUG')
    
    # 각 레벨별 로그 테스트
    logger.debug("🔍 DEBUG 레벨 로그: 디버깅 정보")
    logger.info("ℹ️ INFO 레벨 로그: 일반 정보")
    logger.warning("⚠️ WARNING 레벨 로그: 경고 메시지")
    logger.error("❌ ERROR 레벨 로그: 오류 메시지")
    logger.critical("🚨 CRITICAL 레벨 로그: 심각한 오류")
    
    print()
    print("=" * 60)
    print("로그 파일 확인:")
    print("=" * 60)
    print(f"  - logs/test_logging.log (일반 로그)")
    print(f"  - logs/test_logging_error.log (에러 로그)")
    print()
    
    # 다른 모듈에서 로거 가져오기 테스트
    logger2 = get_logger('test_module')
    logger2.info("다른 모듈에서 로거 가져오기 테스트")
    
    print("✅ 로깅 시스템 테스트 완료!")

if __name__ == "__main__":
    test_logging()

