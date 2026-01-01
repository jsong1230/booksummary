#!/usr/bin/env python3
"""
기존 자막 파일들을 사용하여 책 요약을 생성하는 스크립트

data/source 디렉토리에 있는 part1_author.txt와 part2_novel.txt 파일을 읽어서
이를 컨텍스트로 제공하여 요약을 생성합니다.
"""

import argparse
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.file_utils import get_standard_safe_title
from src.utils.logger import setup_logger
import importlib.util

# 08_generate_summary 모듈 로드
spec = importlib.util.spec_from_file_location("generate_summary", project_root / "src" / "08_generate_summary.py")
generate_summary_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_summary_module)
SummaryGenerator = generate_summary_module.SummaryGenerator

# 로거 설정
logger = setup_logger(__name__)

def read_transcripts(safe_title: str) -> str:
    """자막 파일들을 읽어서 합칩니다."""
    source_dir = Path("data/source")
    
    # 여러 파일명 패턴 시도
    part1_patterns = [
        f"{safe_title}_part1_author.txt",
        f"{safe_title}_part1.txt",
        f"part1_author.txt" # 폴더 내 유일한 파일일 경우 등을 고려할 수도 있지만 지금은 명시적 이름만
    ]
    
    part2_patterns = [
        f"{safe_title}_part2_novel.txt",
        f"{safe_title}_part2.txt",
        f"part2_novel.txt"
    ]
    
    part1_path = None
    for p in part1_patterns:
        if (source_dir / p).exists():
            part1_path = source_dir / p
            break
            
    part2_path = None
    for p in part2_patterns:
        if (source_dir / p).exists():
            part2_path = source_dir / p
            break
    
    context_parts = []
    
    if part1_path:
        logger.info(f"📄 Part 1 자막 파일 발견: {part1_path}")
        try:
            with open(part1_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    context_parts.append(f"=== Part 1: 작가와 배경 ===\n{content}")
        except Exception as e:
            logger.error(f"❌ Part 1 파일 읽기 실패: {e}")

    if part2_path:
        logger.info(f"📄 Part 2 자막 파일 발견: {part2_path}")
        try:
            with open(part2_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    context_parts.append(f"=== Part 2: 소설 줄거리 ===\n{content}")
        except Exception as e:
            logger.error(f"❌ Part 2 파일 읽기 실패: {e}")
            
    if not context_parts:
        # 안전한 제목으로 찾지 못한 경우, source 디렉토리 내의 최근 파일들을 찾아볼 수도 있음
        # 하지만 지금은 엄격하게 매칭
        logger.warning(f"⚠️ '{safe_title}'에 해당하는 자막 파일을 data/source/ 에서 찾을 수 없습니다.")
        return None
        
    return "\n\n".join(context_parts)

def main():
    parser = argparse.ArgumentParser(description='자막 기반 책 요약 생성')
    parser.add_argument('--title', type=str, required=True, help='책 제목')
    parser.add_argument('--author', type=str, help='저자 이름')
    parser.add_argument('--language', type=str, default='ko', choices=['ko', 'en'], help='언어 (기본값: ko)')
    
    args = parser.parse_args()
    
    safe_title = get_standard_safe_title(args.title)
    logger.info(f"📚 책 제목: {args.title} (Safe: {safe_title})")
    
    # 자막 읽기
    context_text = read_transcripts(safe_title)
    
    if context_text:
        logger.info(f"✅ 자막 컨텍스트 로드 완료 ({len(context_text)} 문자)")
    else:
        logger.warning("⚠️ 자막 컨텍스트 없이 요약을 생성합니다. (기존 지식 기반)")

    generator = SummaryGenerator()
    
    try:
        summary = generator.generate_summary(
            book_title=args.title,
            author=args.author,
            language=args.language,
            context_text=context_text  # 컨텍스트 전달
        )
        
        output_path = generator.save_summary(
            summary=summary,
            book_title=args.title,
            author=args.author,
            language=args.language
        )
        
        logger.info("=" * 60)
        logger.info("✅ 요약 생성 완료!")
        logger.info(f"📁 저장 위치: {output_path}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ 요약 생성 중 오류 발생: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()
