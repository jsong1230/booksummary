"""
구조화된 로깅 시스템 유틸리티

이 모듈은 프로젝트 전반에 걸쳐 일관된 로깅을 제공합니다.
- 로그 레벨 관리 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- 파일 로그와 콘솔 로그 분리
- 로그 파일 로테이션 (크기/날짜 기반)
- 환경 변수로 로그 레벨 설정 가능
"""

import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """컬러 로그 포맷터 (콘솔 출력용)"""
    
    # ANSI 색상 코드
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    # 이모지 매핑
    EMOJIS = {
        'DEBUG': '🔍',
        'INFO': 'ℹ️',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🚨'
    }
    
    def format(self, record):
        """로그 레코드 포맷팅"""
        # 이모지 추가
        emoji = self.EMOJIS.get(record.levelname, '')
        record.levelname_emoji = emoji
        
        # 색상 적용 (터미널에서만)
        if sys.stdout.isatty():
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
            record.levelname = f"{color}{record.levelname}{reset}"
        else:
            record.levelname = record.levelname
        
        return super().format(record)


def setup_logger(
    name: str,
    log_level: Optional[str] = None,
    log_dir: Optional[Path] = None,
    console_output: bool = True,
    file_output: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    로거 설정 및 반환
    
    Args:
        name: 로거 이름 (보통 모듈 이름)
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  환경 변수 LOG_LEVEL이 설정되어 있으면 우선 사용
        log_dir: 로그 파일 저장 디렉토리 (기본값: logs/)
        console_output: 콘솔 출력 여부
        file_output: 파일 출력 여부
        max_bytes: 로그 파일 최대 크기 (바이트)
        backup_count: 백업 파일 개수
    
    Returns:
        설정된 Logger 인스턴스
    """
    logger = logging.getLogger(name)
    
    # 이미 핸들러가 설정되어 있으면 기존 로거 반환
    if logger.handlers:
        return logger
    
    # 로그 레벨 결정 (환경 변수 > 파라미터 > 기본값 INFO)
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    level = getattr(logging, log_level, logging.INFO)
    logger.setLevel(level)
    
    # 로그 디렉토리 설정
    if log_dir is None:
        log_dir = Path('logs')
    else:
        log_dir = Path(log_dir)
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 로그 포맷 설정
    # 파일용 포맷 (상세)
    file_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 콘솔용 포맷 (간결)
    console_format = ColoredFormatter(
        '%(levelname_emoji)s %(levelname)-8s | %(name)s | %(message)s'
    )
    
    # 파일 핸들러 설정
    if file_output:
        log_file = log_dir / f"{name}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
        
        # 에러 로그는 별도 파일로 저장
        error_log_file = log_dir / f"{name}_error.log"
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_format)
        logger.addHandler(error_handler)
    
    # 콘솔 핸들러 설정
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    기존 로거 가져오기 또는 새로 생성
    
    Args:
        name: 로거 이름 (None이면 호출한 모듈 이름 사용)
    
    Returns:
        Logger 인스턴스
    """
    if name is None:
        # 호출한 모듈의 이름 사용
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            name = frame.f_back.f_globals.get('__name__', 'root')
        else:
            name = 'root'
    
    logger = logging.getLogger(name)
    
    # 핸들러가 없으면 기본 설정으로 생성
    if not logger.handlers:
        return setup_logger(name)
    
    return logger


# 전역 로거 인스턴스 (간편 사용용)
_default_logger = None

def get_default_logger() -> logging.Logger:
    """기본 로거 인스턴스 반환"""
    global _default_logger
    if _default_logger is None:
        _default_logger = setup_logger('booksummary')
    return _default_logger

