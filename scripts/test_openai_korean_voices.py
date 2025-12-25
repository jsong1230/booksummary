#!/usr/bin/env python3
"""
OpenAI TTS 한글 음성 옵션 테스트 스크립트
OpenAI TTS의 모든 음성을 한글로 테스트하여 가장 자연스러운 음성을 찾습니다.
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

# 동적 import
import importlib.util
tts_multi_path = Path(__file__).parent.parent / "src" / "09_text_to_speech_multi.py"
spec = importlib.util.spec_from_file_location("text_to_speech_multi", tts_multi_path)
tts_multi_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tts_multi_module)
MultiTTSEngine = tts_multi_module.MultiTTSEngine

# 한글 테스트 텍스트 (자연스러움 평가용)
TEST_TEXT_KO = """
안녕하세요. 오늘은 날씨가 정말 좋네요.
이 책은 인생의 의미에 대해 깊이 있게 다루고 있습니다.
작가는 경험을 통해 얻은 지혜를 독자들과 나누고 싶어 합니다.
한국어 음성 합성의 자연스러움을 평가하기 위한 테스트 문장입니다.
각 문장이 어떻게 발음되는지, 억양이 자연스러운지 확인해보겠습니다.
"""


def test_openai_voice(voice: str, output_dir: Path):
    """OpenAI TTS 음성 테스트"""
    print()
    print("=" * 80)
    print(f"🧪 테스트: OpenAI TTS - {voice.upper()}")
    print("=" * 80)
    
    output_path = output_dir / f"openai_{voice}_ko.mp3"
    
    try:
        start_time = time.time()
        engine = MultiTTSEngine(provider="openai")
        result_path = engine.generate_speech(
            text=TEST_TEXT_KO,
            output_path=str(output_path),
            voice=voice,
            language="ko",
            model="tts-1-hd"  # 고품질 모델 사용
        )
        elapsed_time = time.time() - start_time
        
        file_size = Path(result_path).stat().st_size / 1024  # KB
        
        print()
        print(f"✅ 성공!")
        print(f"   소요 시간: {elapsed_time:.2f}초")
        print(f"   파일 크기: {file_size:.2f} KB")
        print(f"   파일 경로: {result_path}")
        
        return {
            "provider": "openai",
            "voice": voice,
            "success": True,
            "elapsed_time": elapsed_time,
            "file_size_kb": file_size,
            "output_path": str(result_path)
        }
        
    except Exception as e:
        print()
        print(f"❌ 실패: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "provider": "openai",
            "voice": voice,
            "success": False,
            "error": str(e),
            "elapsed_time": None,
            "file_size_kb": None,
            "output_path": None
        }


def main():
    """메인 테스트 함수"""
    print("=" * 80)
    print("🎤 OpenAI TTS 한글 음성 옵션 비교 테스트")
    print("=" * 80)
    print()
    print("목적: OpenAI TTS의 모든 음성 중 한글이 가장 자연스러운 음성 찾기")
    print()
    
    output_dir = Path("test_outputs/openai_korean_voices")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # OpenAI TTS 지원 음성 목록
    # 한글에 적합한 음성들:
    # - nova: 더 따뜻하고 자연스러운 여성 음성 (현재 사용 중, 추천)
    # - shimmer: 부드럽고 명확한 여성 음성
    # - alloy: 중성적이고 균형잡힌 음성
    # - echo: 명확하고 강한 남성 음성
    # - fable: 따뜻하고 친근한 음성
    # - onyx: 깊고 강한 남성 음성
    openai_voices = [
        "nova",      # 현재 사용 중 (추천)
        "shimmer",   # 부드러운 여성 음성
        "alloy",     # 중성적 음성
        "echo",      # 명확한 남성 음성
        "fable",     # 따뜻한 음성
        "onyx",      # 깊은 남성 음성
    ]
    
    results = []
    
    for voice in openai_voices:
        result = test_openai_voice(voice, output_dir)
        results.append(result)
        time.sleep(1)  # API 호출 간격
    
    # 결과 요약
    print("\n" + "=" * 80)
    print("📊 테스트 결과 요약")
    print("=" * 80)
    print()
    
    print("🇰🇷 OpenAI TTS 한글 음성 테스트 결과:")
    print("-" * 80)
    for result in results:
        if result["success"]:
            print(f"✅ {result['voice']:10s} | 시간: {result['elapsed_time']:6.2f}초 | 크기: {result['file_size_kb']:7.2f} KB")
        else:
            print(f"❌ {result['voice']:10s} | 오류: {result.get('error', 'Unknown')[:50]}")
    print()
    
    # 성공률
    total = len(results)
    successful = len([r for r in results if r["success"]])
    print(f"📈 전체 성공률: {successful}/{total} ({successful/total*100:.1f}%)")
    print()
    
    # 결과를 JSON 파일로 저장
    import json
    results_file = output_dir / f"openai_korean_voices_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"📄 상세 결과 저장: {results_file}")
    print()
    print("=" * 80)
    print("✅ 테스트 완료!")
    print("=" * 80)
    print()
    print("💡 다음 단계:")
    print("   1. test_outputs/openai_korean_voices/ 폴더에서 생성된 오디오 파일들을 들어보세요")
    print("   2. 각 음성의 자연스러움, 발음 명확도, 억양을 비교해보세요")
    print("   3. 가장 자연스러운 음성을 선택하여 프로젝트에 적용하세요")
    print()
    print("📌 음성 특징:")
    print("   - nova: 따뜻하고 자연스러운 여성 음성 (현재 사용 중)")
    print("   - shimmer: 부드럽고 명확한 여성 음성")
    print("   - alloy: 중성적이고 균형잡힌 음성")
    print("   - echo: 명확하고 강한 남성 음성")
    print("   - fable: 따뜻하고 친근한 음성")
    print("   - onyx: 깊고 강한 남성 음성")


if __name__ == "__main__":
    main()














