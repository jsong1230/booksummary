"""
다중 TTS 엔진 지원 스크립트
- OpenAI TTS
- Google Cloud TTS (Neural2)
- Replicate (xtts-v2, ElevenLabs Multilingual v2)
"""

import os
import json
import time
from pathlib import Path
from typing import Optional, Literal
from dotenv import load_dotenv
try:
    from utils.retry_utils import retry_with_backoff
except ImportError:
    from src.utils.retry_utils import retry_with_backoff

load_dotenv()

# OpenAI TTS
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Google Cloud TTS
try:
    from google.cloud import texttospeech
    GOOGLE_TTS_AVAILABLE = True
except ImportError:
    GOOGLE_TTS_AVAILABLE = False

# Replicate
try:
    import replicate
    REPLICATE_AVAILABLE = True
except ImportError:
    REPLICATE_AVAILABLE = False


class MultiTTSEngine:
    """다중 TTS 엔진 지원 클래스"""
    
    def __init__(self, provider: Literal["openai", "google", "replicate_xtts", "replicate_elevenlabs"] = "openai"):
        """
        Args:
            provider: TTS 제공자 선택
                - "openai": OpenAI TTS API
                - "google": Google Cloud TTS (Neural2)
                - "replicate_xtts": Replicate xtts-v2
                - "replicate_elevenlabs": Replicate ElevenLabs Multilingual v2
        """
        self.provider = provider
        self._init_provider()
    
    def _init_provider(self):
        """제공자별 초기화"""
        if self.provider == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError("openai 패키지가 설치되지 않았습니다. pip install openai")
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
            self.client = OpenAI(api_key=self.openai_api_key)
        
        elif self.provider == "google":
            if not GOOGLE_TTS_AVAILABLE:
                raise ImportError("google-cloud-texttospeech 패키지가 설치되지 않았습니다. pip install google-cloud-texttospeech")
            # Google Cloud 인증 정보 확인
            google_creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if not google_creds_path:
                # 기본 경로 확인
                default_path = Path("secrets/google-cloud-tts-key.json")
                if default_path.exists():
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(default_path.absolute())
                else:
                    raise ValueError("GOOGLE_APPLICATION_CREDENTIALS 환경 변수가 설정되지 않았거나 google-cloud-tts-key.json 파일이 없습니다.")
            self.google_client = texttospeech.TextToSpeechClient()
        
        elif self.provider == "replicate_xtts":
            if not REPLICATE_AVAILABLE:
                raise ImportError("replicate 패키지가 설치되지 않았습니다. pip install replicate")
            self.replicate_api_token = os.getenv("REPLICATE_API_TOKEN")
            if not self.replicate_api_token:
                raise ValueError("REPLICATE_API_TOKEN이 설정되지 않았습니다.")
            os.environ["REPLICATE_API_TOKEN"] = self.replicate_api_token
        elif self.provider == "replicate_elevenlabs":
            # ElevenLabs는 직접 API 사용
            elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
            if not elevenlabs_api_key:
                raise ValueError("ELEVENLABS_API_KEY가 설정되지 않았습니다.")
    
    @retry_with_backoff(retries=3, backoff_in_seconds=1.0)
    def generate_speech(
        self,
        text: str,
        output_path: str,
        voice: str = None,
        language: str = "ko",
        model: str = None,
        **kwargs
    ) -> str:
        """
        텍스트를 음성으로 변환
        
        Args:
            text: 변환할 텍스트
            output_path: 출력 파일 경로
            voice: 음성 종류 (제공자별로 다름)
            language: 언어 ('ko' 또는 'en')
            model: 모델 (제공자별로 다름)
            **kwargs: 제공자별 추가 옵션
            
        Returns:
            생성된 오디오 파일 경로
        """
        if self.provider == "openai":
            return self._generate_openai(text, output_path, voice, language, model)
        elif self.provider == "google":
            return self._generate_google(text, output_path, voice, language, model)
        elif self.provider == "replicate_xtts":
            return self._generate_replicate_xtts(text, output_path, voice, language, model)
        elif self.provider == "replicate_elevenlabs":
            return self._generate_replicate_elevenlabs(text, output_path, voice, language, model)
        else:
            raise ValueError(f"지원하지 않는 제공자: {self.provider}")
    
    def _generate_openai(self, text: str, output_path: str, voice: str, language: str, model: str) -> str:
        """OpenAI TTS 생성"""
        # 기본값 설정
        if not voice:
            voice = "nova" if language == "ko" else "alloy"
        if not model:
            model = "tts-1-hd"
        
        print(f"🎤 OpenAI TTS 음성 생성 중...")
        print(f"   음성: {voice}")
        print(f"   모델: {model}")
        print(f"   언어: {language}")
        print()
        
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        MAX_CHARS = 4096
        if len(text) <= MAX_CHARS:
            response = self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text
            )
            with open(output_path, 'wb') as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
            print(f"✅ 음성 생성 완료: {output_path}")
        else:
            # 긴 텍스트는 분할 처리
            return self._generate_openai_long(text, output_path, voice, model, MAX_CHARS)
        
        return output_path
    
    def _generate_openai_long(self, text: str, output_path: str, voice: str, model: str, max_chars: int) -> str:
        """OpenAI TTS 긴 텍스트 처리"""
        import re
        sentences = re.split(r'([.!?]\s+)', text)
        chunks = []
        current_chunk = ""
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else "")
            if len(current_chunk) + len(sentence) <= max_chars:
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence if len(sentence) <= max_chars else sentence[:max_chars]
        
        if current_chunk:
            chunks.append(current_chunk)
        
        print(f"   📦 {len(chunks)}개의 청크로 분할됨")
        
        audio_files = []
        for i, chunk in enumerate(chunks):
            print(f"   [{i+1}/{len(chunks)}] 청크 생성 중... ({len(chunk)}자)")
            temp_audio_path = output_path.replace('.mp3', f'_temp_{i}.mp3')
            
            response = self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=chunk
            )
            
            with open(temp_audio_path, 'wb') as f:
                for chunk_bytes in response.iter_bytes():
                    f.write(chunk_bytes)
            
            audio_files.append(temp_audio_path)
        
        # 오디오 파일 연결
        print(f"   🔗 {len(audio_files)}개의 오디오 파일 연결 중...")
        try:
            from moviepy.editor import AudioFileClip, concatenate_audioclips
            audio_clips = [AudioFileClip(f) for f in audio_files]
            final_audio = concatenate_audioclips(audio_clips)
            final_audio.write_audiofile(output_path, codec='mp3', bitrate='192k')
            for f in audio_files:
                Path(f).unlink()
            for clip in audio_clips:
                clip.close()
            final_audio.close()
        except ImportError:
            import subprocess
            temp_list_file = output_path.replace('.mp3', '_temp_list.txt')
            with open(temp_list_file, 'w') as f:
                for audio_file in audio_files:
                    f.write(f"file '{Path(audio_file).absolute()}'\n")
            subprocess.run([
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', temp_list_file,
                '-c', 'copy', output_path
            ], check=True, capture_output=True)
            Path(temp_list_file).unlink()
            for f in audio_files:
                Path(f).unlink()
        
        print(f"✅ 음성 생성 완료: {output_path}")
        return output_path
    
    def _generate_google(self, text: str, output_path: str, voice: str, language: str, model: str) -> str:
        """Google Cloud TTS (Neural2) 생성"""
        print(f"🎤 Google Cloud TTS (Neural2) 음성 생성 중...")
        print(f"   언어: {language}")
        print()
        
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # 언어 코드 매핑
        lang_code_map = {
            "ko": "ko-KR",
            "en": "en-US"
        }
        lang_code = lang_code_map.get(language, "ko-KR")
        
        # Neural2 음성 선택
        # 한국어: ko-KR-Neural2-A (여성), ko-KR-Neural2-B (남성), ko-KR-Neural2-C (여성), ko-KR-Neural2-D (남성)
        # 영어: en-US-Neural2-A ~ J (다양한 음성)
        if not voice:
            if language == "ko":
                voice = "ko-KR-Neural2-A"  # 여성 음성 (기본값)
            else:
                voice = "en-US-Neural2-A"  # 여성 음성 (기본값)
                voice = "en-US-Neural2-A"  # 여성 음성 (기본값)
        
        # 길이 제한 확인 (5000 바이트)
        # 안전하게 한글 기준 1500자, 영문 기준 4500자 정도로 설정
        MAX_CHARS = 1500
        if len(text) > MAX_CHARS:
            return self._generate_google_long(text, output_path, voice, lang_code, MAX_CHARS)
        
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice_config = texttospeech.VoiceSelectionParams(
            language_code=lang_code,
            name=voice,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0,
        )
        
        response = self.google_client.synthesize_speech(
            input=synthesis_input,
            voice=voice_config,
            audio_config=audio_config
        )
        
        with open(output_path, 'wb') as f:
            f.write(response.audio_content)
        
        print(f"✅ 음성 생성 완료: {output_path}")
        return output_path
    
    def _generate_google_long(self, text: str, output_path: str, voice: str, lang_code: str, max_chars: int) -> str:
        """Google TTS 긴 텍스트 처리"""
        import re
        sentences = re.split(r'([.!?]\s+)', text)
        chunks = []
        current_chunk = ""
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else "")
            if len(current_chunk) + len(sentence) <= max_chars:
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence if len(sentence) <= max_chars else sentence[:max_chars]
        
        if current_chunk:
            chunks.append(current_chunk)
        
        print(f"   📦 {len(chunks)}개의 청크로 분할됨")
        
        audio_files = []
        
        # 음성 설정
        voice_config = texttospeech.VoiceSelectionParams(
            language_code=lang_code,
            name=voice,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0,
        )
        
        for i, chunk in enumerate(chunks):
            print(f"   [{i+1}/{len(chunks)}] 청크 생성 중... ({len(chunk)}자)")
            temp_audio_path = output_path.replace('.mp3', f'_temp_{i}.mp3')
            
            synthesis_input = texttospeech.SynthesisInput(text=chunk)
            
            response = self.google_client.synthesize_speech(
                input=synthesis_input,
                voice=voice_config,
                audio_config=audio_config
            )
            
            with open(temp_audio_path, 'wb') as f:
                f.write(response.audio_content)
            
            audio_files.append(temp_audio_path)
        
        # 오디오 파일 연결
        print(f"   🔗 {len(audio_files)}개의 오디오 파일 연결 중...")
        try:
            from moviepy.editor import AudioFileClip, concatenate_audioclips
            audio_clips = [AudioFileClip(f) for f in audio_files]
            final_audio = concatenate_audioclips(audio_clips)
            final_audio.write_audiofile(output_path, codec='mp3', bitrate='192k')
            for f in audio_files:
                Path(f).unlink()
            for clip in audio_clips:
                clip.close()
            final_audio.close()
        except ImportError:
            import subprocess
            temp_list_file = output_path.replace('.mp3', '_temp_list.txt')
            with open(temp_list_file, 'w') as f:
                for audio_file in audio_files:
                    f.write(f"file '{Path(audio_file).absolute()}'\n")
            subprocess.run([
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', temp_list_file,
                '-c', 'copy', output_path
            ], check=True, capture_output=True)
            Path(temp_list_file).unlink()
            for f in audio_files:
                Path(f).unlink()
        
        print(f"✅ 음성 생성 완료: {output_path}")
        return output_path
    
    def _generate_replicate_xtts(self, text: str, output_path: str, voice: str, language: str, model: str) -> str:
        """Replicate xtts-v2 생성"""
        print(f"🎤 Replicate xtts-v2 음성 생성 중...")
        print(f"   언어: {language}")
        print()
        
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # xtts-v2는 참조 오디오가 필요하거나 언어 코드 사용
        # 언어 코드 매핑
        lang_code_map = {
            "ko": "ko",
            "en": "en"
        }
        lang_code = lang_code_map.get(language, "ko")
        
        # xtts-v2 모델 사용 (lucataco fork, coqui/xtts-v2는 삭제됨)
        model_id = "lucataco/xtts-v2:684bc3855b37866c0c65add2ff39c78f3dea3f4ff103a436465326e0f438d55e"
        
        # 텍스트가 길면 분할
        MAX_CHARS = 2000  # xtts-v2는 더 짧은 텍스트 권장
        if len(text) > MAX_CHARS:
            print(f"   ⚠️ 텍스트가 {len(text)}자로 너무 깁니다. 첫 {MAX_CHARS}자만 사용합니다.")
            text = text[:MAX_CHARS]
        
        # 참조 음성 URL (xtts-v2는 speaker 필수)
        speaker_samples = {
            "ko": "https://replicate.delivery/pbxt/Jt79w0xsT64R1JsiJ0LQRL8UcWspg5J4RFrU6YwEKpOT1ukS/male.wav",
            "en": "https://replicate.delivery/pbxt/Jt79w0xsT64R1JsiJ0LQRL8UcWspg5J4RFrU6YwEKpOT1ukS/male.wav",
        }
        speaker_url = speaker_samples.get(lang_code, speaker_samples["en"])

        try:
            output = replicate.run(
                model_id,
                input={
                    "text": text,
                    "speaker": speaker_url,
                    "language": lang_code,
                    "cleanup_voice": False,
                }
            )
            
            # Replicate는 URL 또는 FileOutput 객체를 반환
            import requests
            audio_url = str(output)  # FileOutput도 str()로 URL 추출 가능
            if not audio_url.startswith("http"):
                if isinstance(output, (list, tuple)) and len(output) > 0:
                    audio_url = str(output[0])
                else:
                    raise ValueError(f"예상치 못한 출력 형식: {output}")
            
            # 오디오 다운로드
            response = requests.get(audio_url)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ 음성 생성 완료: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ Replicate xtts-v2 생성 오류: {e}")
            raise
    
    def _generate_replicate_elevenlabs(self, text: str, output_path: str, voice: str, language: str, model: str) -> str:
        """Replicate ElevenLabs Multilingual v2 생성"""
        print(f"🎤 Replicate ElevenLabs Multilingual v2 음성 생성 중...")
        print(f"   언어: {language}")
        print()
        
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Replicate에서 ElevenLabs 모델 사용
        # 참고: Replicate는 ElevenLabs API를 직접 제공하지 않을 수 있음
        # 대신 OpenRouter나 직접 ElevenLabs API를 사용하는 것이 더 나을 수 있음
        # 여기서는 Replicate의 다른 TTS 모델을 사용하거나, 
        # 실제로는 OpenRouter를 통해 ElevenLabs를 사용하는 것이 좋을 수 있음
        
        # 일단 Replicate에서 사용 가능한 TTS 모델 중 multilingual 지원 모델 찾기
        # 또는 OpenRouter를 통해 ElevenLabs 사용
        
        # OpenRouter를 통한 ElevenLabs 사용 (더 정확한 방법)
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_api_key:
            return self._generate_openrouter_elevenlabs(text, output_path, voice, language, openrouter_api_key)
        else:
            raise ValueError("OPENROUTER_API_KEY가 설정되지 않았습니다. Replicate를 통한 ElevenLabs는 직접 지원되지 않을 수 있습니다.")
    
    def _generate_openrouter_elevenlabs(self, text: str, output_path: str, voice: str, language: str, api_key: str) -> str:
        """OpenRouter를 통한 ElevenLabs Multilingual v2 생성"""
        print(f"   (OpenRouter를 통해 ElevenLabs 사용)")
        
        import requests
        
        # ElevenLabs API 엔드포인트 (OpenRouter를 통해)
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        # 음성 ID (기본값)
        if not voice:
            voice_id = "21m00Tcm4TlvDq8ikWAM"  # 기본 여성 음성
        else:
            voice_id = voice
        
        # 텍스트가 길면 분할
        MAX_CHARS = 5000
        if len(text) > MAX_CHARS:
            print(f"   ⚠️ 텍스트가 {len(text)}자로 너무 깁니다. 첫 {MAX_CHARS}자만 사용합니다.")
            text = text[:MAX_CHARS]
        
        # OpenRouter를 통한 ElevenLabs 호출
        # 참고: OpenRouter의 실제 API 형식 확인 필요
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # OpenRouter는 주로 LLM용이므로, TTS는 직접 ElevenLabs API를 사용하는 것이 더 나을 수 있음
        # 여기서는 일단 에러를 발생시키고, 실제 구현은 ElevenLabs 직접 API 사용 권장
        raise NotImplementedError(
            "Replicate를 통한 ElevenLabs는 직접 지원되지 않습니다. "
            "ElevenLabs API를 직접 사용하거나, OpenRouter의 TTS 지원 여부를 확인하세요."
        )


def main():
    """테스트용 메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='다중 TTS 엔진 테스트')
    parser.add_argument('--provider', type=str, required=True,
                       choices=['openai', 'google', 'replicate_xtts', 'replicate_elevenlabs'],
                       help='TTS 제공자 선택')
    parser.add_argument('--text', type=str, help='변환할 텍스트')
    parser.add_argument('--text-file', type=str, help='텍스트 파일 경로')
    parser.add_argument('--output', type=str, required=True, help='출력 오디오 파일 경로')
    parser.add_argument('--voice', type=str, help='음성 종류 (제공자별로 다름)')
    parser.add_argument('--language', type=str, default='ko', choices=['ko', 'en'], help='언어 (기본값: ko)')
    
    args = parser.parse_args()
    
    if not args.text and not args.text_file:
        print("❌ --text 또는 --text-file 중 하나를 지정해야 합니다.")
        return 1
    
    try:
        engine = MultiTTSEngine(provider=args.provider)
        
        if args.text_file:
            with open(args.text_file, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            text = args.text
        
        start_time = time.time()
        output_path = engine.generate_speech(
            text=text,
            output_path=args.output,
            voice=args.voice,
            language=args.language
        )
        elapsed_time = time.time() - start_time
        
        print()
        print("=" * 60)
        print("✅ TTS 음성 생성 완료!")
        print("=" * 60)
        print(f"📁 저장 위치: {output_path}")
        print(f"⏱️ 소요 시간: {elapsed_time:.2f}초")
        
        # 파일 크기 확인
        file_size = Path(output_path).stat().st_size / 1024  # KB
        print(f"📦 파일 크기: {file_size:.2f} KB")
        
        return 0
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

