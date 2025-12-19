#!/usr/bin/env python3
"""
TTS 제공자 비교 테스트 스크립트
- OpenAI TTS
- Google Cloud TTS (Neural2)
- Replicate xtts-v2
- Replicate ElevenLabs Multilingual v2
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# 동적 import
import importlib.util
tts_multi_path = Path(__file__).parent.parent / "src" / "09_text_to_speech_multi.py"
spec = importlib.util.spec_from_file_location("text_to_speech_multi", tts_multi_path)
tts_multi_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tts_multi_module)
MultiTTSEngine = tts_multi_module.MultiTTSEngine

# 테스트 텍스트 (한글)
TEST_TEXT_KO = """
안녕하세요. 이것은 TTS 제공자 비교 테스트입니다.
각 제공자의 음질, 자연스러움, 속도를 비교해보겠습니다.
한국어 텍스트를 음성으로 변환하는 능력을 평가합니다.
"""

# 테스트 텍스트 (영어)
TEST_TEXT_EN = """
Hello, this is a TTS provider comparison test.
We will compare the audio quality, naturalness, and speed of each provider.
This evaluates the ability to convert English text to speech.
"""


def test_provider(provider: str, text: str, language: str, output_dir: Path):
    """단일 제공자 테스트"""
    print()
    print("=" * 80)
    print(f"🧪 테스트: {provider.upper()}")
    print("=" * 80)
    
    output_path = output_dir / f"test_{provider}_{language}.mp3"
    
    try:
        start_time = time.time()
        engine = MultiTTSEngine(provider=provider)
        result_path = engine.generate_speech(
            text=text,
            output_path=str(output_path),
            language=language
        )
        elapsed_time = time.time() - start_time
        
        # 파일 크기 확인
        file_size = Path(result_path).stat().st_size / 1024  # KB
        
        print()
        print(f"✅ 성공!")
        print(f"   소요 시간: {elapsed_time:.2f}초")
        print(f"   파일 크기: {file_size:.2f} KB")
        print(f"   파일 경로: {result_path}")
        
        return {
            "provider": provider,
            "language": language,
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
            "provider": provider,
            "language": language,
            "success": False,
            "error": str(e),
            "elapsed_time": None,
            "file_size_kb": None,
            "output_path": None
        }


def main():
    """메인 테스트 함수"""
    print("=" * 80)
    print("🎤 TTS 제공자 비교 테스트")
    print("=" * 80)
    print()
    
    # 출력 디렉토리 생성
    output_dir = Path("test_outputs/tts_comparison")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 테스트할 제공자 목록
    providers = [
        "openai",
        "google",
        "replicate_xtts",
        "replicate_elevenlabs"
    ]
    
    results = []
    
    # 한글 테스트
    print("\n" + "=" * 80)
    print("🇰🇷 한글 테스트")
    print("=" * 80)
    
    for provider in providers:
        result = test_provider(provider, TEST_TEXT_KO, "ko", output_dir)
        results.append(result)
        time.sleep(1)  # API 호출 간격
    
    # 영어 테스트
    print("\n" + "=" * 80)
    print("🇺🇸 영어 테스트")
    print("=" * 80)
    
    for provider in providers:
        result = test_provider(provider, TEST_TEXT_EN, "en", output_dir)
        results.append(result)
        time.sleep(1)  # API 호출 간격
    
    # 결과 요약
    print("\n" + "=" * 80)
    print("📊 테스트 결과 요약")
    print("=" * 80)
    print()
    
    # 한글 결과
    print("🇰🇷 한글 테스트 결과:")
    print("-" * 80)
    ko_results = [r for r in results if r["language"] == "ko"]
    for result in ko_results:
        if result["success"]:
            print(f"✅ {result['provider']:20s} | 시간: {result['elapsed_time']:6.2f}초 | 크기: {result['file_size_kb']:7.2f} KB")
        else:
            print(f"❌ {result['provider']:20s} | 오류: {result.get('error', 'Unknown')}")
    print()
    
    # 영어 결과
    print("🇺🇸 영어 테스트 결과:")
    print("-" * 80)
    en_results = [r for r in results if r["language"] == "en"]
    for result in en_results:
        if result["success"]:
            print(f"✅ {result['provider']:20s} | 시간: {result['elapsed_time']:6.2f}초 | 크기: {result['file_size_kb']:7.2f} KB")
        else:
            print(f"❌ {result['provider']:20s} | 오류: {result.get('error', 'Unknown')}")
    print()
    
    # 성공률 계산
    total = len(results)
    successful = len([r for r in results if r["success"]])
    print(f"📈 전체 성공률: {successful}/{total} ({successful/total*100:.1f}%)")
    print()
    
    # 결과를 JSON 파일로 저장
    import json
    results_file = output_dir / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"📄 상세 결과 저장: {results_file}")
    print()
    print("=" * 80)
    print("✅ 테스트 완료!")
    print("=" * 80)
    print()
    print("💡 다음 단계:")
    print("   1. test_outputs/tts_comparison/ 폴더에서 생성된 오디오 파일들을 들어보세요")
    print("   2. 음질, 자연스러움, 속도를 비교해보세요")
    print("   3. 비용과 API 제한사항을 고려하여 최적의 제공자를 선택하세요")


if __name__ == "__main__":
    main()

