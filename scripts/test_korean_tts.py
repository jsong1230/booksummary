#!/usr/bin/env python3
"""
한글 TTS 음질 비교 테스트 스크립트
다양한 TTS 제공자의 한글 음성을 비교하여 가장 자연스러운 음성을 찾습니다.
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
"""


def test_korean_voice(provider: str, voice: str = None, output_dir: Path = None):
    """한글 음성 테스트"""
    print()
    print("=" * 80)
    print(f"🧪 테스트: {provider.upper()}")
    if voice:
        print(f"   음성: {voice}")
    print("=" * 80)
    
    output_path = output_dir / f"korean_{provider}_{voice or 'default'}.mp3"
    
    try:
        start_time = time.time()
        engine = MultiTTSEngine(provider=provider)
        result_path = engine.generate_speech(
            text=TEST_TEXT_KO,
            output_path=str(output_path),
            voice=voice,
            language="ko"
        )
        elapsed_time = time.time() - start_time
        
        file_size = Path(result_path).stat().st_size / 1024  # KB
        
        print()
        print(f"✅ 성공!")
        print(f"   소요 시간: {elapsed_time:.2f}초")
        print(f"   파일 크기: {file_size:.2f} KB")
        print(f"   파일 경로: {result_path}")
        
        return {
            "provider": provider,
            "voice": voice or "default",
            "success": True,
            "elapsed_time": elapsed_time,
            "file_size_kb": file_size,
            "output_path": str(result_path)
        }
        
    except Exception as e:
        print()
        print(f"❌ 실패: {e}")
        
        return {
            "provider": provider,
            "voice": voice or "default",
            "success": False,
            "error": str(e),
            "elapsed_time": None,
            "file_size_kb": None,
            "output_path": None
        }


def test_google_korean_voices():
    """Google Cloud TTS의 다양한 한글 음성 테스트"""
    print("\n" + "=" * 80)
    print("🇰🇷 Google Cloud TTS 한글 음성 옵션 테스트")
    print("=" * 80)
    
    # Google Cloud TTS Neural2 한글 음성 목록
    # ko-KR-Neural2-A: 여성 음성 (기본)
    # ko-KR-Neural2-B: 남성 음성
    # ko-KR-Neural2-C: 여성 음성
    # ko-KR-Neural2-D: 남성 음성
    korean_voices = [
        "ko-KR-Neural2-A",  # 여성 (기본)
        "ko-KR-Neural2-B",  # 남성
        "ko-KR-Neural2-C",  # 여성
        "ko-KR-Neural2-D",  # 남성
    ]
    
    output_dir = Path("test_outputs/korean_tts_comparison")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    for voice in korean_voices:
        result = test_korean_voice("google", voice, output_dir)
        results.append(result)
        time.sleep(0.5)  # API 호출 간격
    
    return results


def main():
    """메인 테스트 함수"""
    print("=" * 80)
    print("🎤 한글 TTS 음질 비교 테스트")
    print("=" * 80)
    print()
    print("목적: 한글이 가장 자연스러운 TTS 제공자 찾기")
    print()
    
    output_dir = Path("test_outputs/korean_tts_comparison")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    # 1. OpenAI TTS (현재 사용 중)
    print("\n" + "=" * 80)
    print("1️⃣ OpenAI TTS (현재 사용 중)")
    print("=" * 80)
    result = test_korean_voice("openai", None, output_dir)
    results.append(result)
    time.sleep(1)
    
    # 2. Google Cloud TTS - 다양한 음성 옵션
    print("\n" + "=" * 80)
    print("2️⃣ Google Cloud TTS (Neural2) - 다양한 한글 음성")
    print("=" * 80)
    google_results = test_google_korean_voices()
    results.extend(google_results)
    
    # 3. ElevenLabs (API 키가 있는 경우)
    print("\n" + "=" * 80)
    print("3️⃣ ElevenLabs Multilingual v2")
    print("=" * 80)
    import os
    if os.getenv("ELEVENLABS_API_KEY"):
        result = test_korean_voice("replicate_elevenlabs", None, output_dir)
        results.append(result)
    else:
        print("⚠️ ELEVENLABS_API_KEY가 설정되지 않아 테스트를 건너뜁니다.")
        results.append({
            "provider": "replicate_elevenlabs",
            "voice": "default",
            "success": False,
            "error": "ELEVENLABS_API_KEY not set"
        })
    
    # 결과 요약
    print("\n" + "=" * 80)
    print("📊 테스트 결과 요약")
    print("=" * 80)
    print()
    
    print("🇰🇷 한글 TTS 테스트 결과:")
    print("-" * 80)
    for result in results:
        if result["success"]:
            print(f"✅ {result['provider']:20s} | {result.get('voice', 'default'):20s} | 시간: {result['elapsed_time']:6.2f}초 | 크기: {result['file_size_kb']:7.2f} KB")
        else:
            print(f"❌ {result['provider']:20s} | {result.get('voice', 'default'):20s} | 오류: {result.get('error', 'Unknown')[:50]}")
    print()
    
    # 성공률
    total = len(results)
    successful = len([r for r in results if r["success"]])
    print(f"📈 전체 성공률: {successful}/{total} ({successful/total*100:.1f}%)")
    print()
    
    # 결과를 JSON 파일로 저장
    import json
    results_file = output_dir / f"korean_tts_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"📄 상세 결과 저장: {results_file}")
    print()
    print("=" * 80)
    print("✅ 테스트 완료!")
    print("=" * 80)
    print()
    print("💡 다음 단계:")
    print("   1. test_outputs/korean_tts_comparison/ 폴더에서 생성된 오디오 파일들을 들어보세요")
    print("   2. 각 음성의 자연스러움, 발음 명확도, 억양을 비교해보세요")
    print("   3. 가장 자연스러운 음성을 선택하여 프로젝트에 적용하세요")
    print()
    print("📌 추천 비교 순서:")
    print("   1. OpenAI (현재 사용 중) vs Google Cloud TTS Neural2-A (기본 여성)")
    print("   2. Google Cloud TTS의 다양한 음성 옵션 비교")
    print("   3. ElevenLabs (API 키가 있는 경우)")


if __name__ == "__main__":
    main()

















