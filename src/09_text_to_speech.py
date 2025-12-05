"""
TTS (Text-to-Speech) 음성 생성 스크립트
OpenAI TTS API를 사용하여 자연스러운 음성을 생성합니다
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from utils.retry_utils import retry_with_backoff

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

load_dotenv()


class TTSEngine:
    """TTS 엔진 클래스"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not OPENAI_AVAILABLE:
            raise ImportError("openai 패키지가 설치되지 않았습니다. pip install openai")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
        
        self.client = OpenAI(api_key=self.openai_api_key)
    
    @retry_with_backoff(retries=3, backoff_in_seconds=1.0)
    def generate_speech(
        self,
        text: str,
        output_path: str,
        voice: str = "alloy",
        language: str = "ko",
        model: str = "tts-1"
    ) -> str:
        """
        텍스트를 음성으로 변환
        
        Args:
            text: 변환할 텍스트
            output_path: 출력 파일 경로
            voice: 음성 종류 ('alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer')
            language: 언어 ('ko' 또는 'en')
            model: TTS 모델 ('tts-1' 또는 'tts-1-hd')
            
        Returns:
            생성된 오디오 파일 경로
        """
        # 언어에 따른 음성 선택
        if language == "ko":
            # 한국어에 적합한 음성 추천:
            # - nova: 더 따뜻하고 자연스러운 여성 음성 (추천)
            # - shimmer: 부드럽고 명확한 여성 음성
            # - alloy: 중성적이고 균형잡힌 음성
            if voice not in ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']:
                voice = "nova"  # 한국어에 가장 자연스러운 음성 (기본값)
        else:
            # 영어에 적합한 음성
            if voice not in ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']:
                voice = "alloy"
        
        print(f"🎤 TTS 음성 생성 중...")
        print(f"   음성: {voice}")
        print(f"   모델: {model}")
        print(f"   언어: {language}")
        print()
        
        # 출력 디렉토리 생성
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # OpenAI TTS API는 최대 4096자까지만 허용
        MAX_CHARS = 4096
        
        try:
            # 텍스트가 길면 분할하여 처리
            if len(text) <= MAX_CHARS:
                # 짧은 경우 한 번에 처리
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
                # 긴 경우 여러 청크로 나눠서 생성 후 연결
                print(f"   ⚠️ 텍스트가 {len(text)}자로 너무 깁니다. 여러 청크로 나눠서 생성합니다.")
                
                # 문장 단위로 분할 (마침표, 느낌표, 물음표 기준)
                import re
                sentences = re.split(r'([.!?]\s+)', text)
                
                # 문장들을 재조합하여 최대 길이 이하로 청크 생성
                chunks = []
                current_chunk = ""
                
                for i in range(0, len(sentences), 2):
                    sentence = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else "")
                    
                    if len(current_chunk) + len(sentence) <= MAX_CHARS:
                        current_chunk += sentence
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        # 새 청크가 MAX_CHARS보다 길면 강제로 자르기
                        if len(sentence) > MAX_CHARS:
                            # 문장이 너무 길면 단어 단위로 자르기
                            words = sentence.split()
                            temp_chunk = ""
                            for word in words:
                                if len(temp_chunk) + len(word) + 1 <= MAX_CHARS:
                                    temp_chunk += word + " "
                                else:
                                    if temp_chunk:
                                        chunks.append(temp_chunk.strip())
                                    temp_chunk = word + " "
                            current_chunk = temp_chunk
                        else:
                            current_chunk = sentence
                
                if current_chunk:
                    chunks.append(current_chunk)
                
                print(f"   📦 {len(chunks)}개의 청크로 분할됨")
                
                # 각 청크를 TTS로 변환
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
                
                # 오디오 파일들을 연결
                print(f"   🔗 {len(audio_files)}개의 오디오 파일 연결 중...")
                try:
                    from moviepy.editor import AudioFileClip, concatenate_audioclips
                    
                    audio_clips = [AudioFileClip(f) for f in audio_files]
                    final_audio = concatenate_audioclips(audio_clips)
                    final_audio.write_audiofile(output_path, codec='mp3', bitrate='192k')
                    
                    # 임시 파일 삭제
                    for f in audio_files:
                        Path(f).unlink()
                    
                    # 클립 닫기
                    for clip in audio_clips:
                        clip.close()
                    final_audio.close()
                    
                except ImportError:
                    # moviepy가 없으면 ffmpeg로 연결
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
                    
                    # 임시 파일 삭제
                    Path(temp_list_file).unlink()
                    for f in audio_files:
                        Path(f).unlink()
                
                print(f"✅ 음성 생성 완료: {output_path}")
            
            return output_path
            
        except Exception as e:
            print(f"❌ TTS 생성 오류: {e}")
            raise
    
    def generate_from_file(
        self,
        text_file_path: str,
        output_path: str = None,
        voice: str = "alloy",
        language: str = "ko",
        model: str = "tts-1"
    ) -> str:
        """
        텍스트 파일에서 읽어서 음성 생성
        
        Args:
            text_file_path: 텍스트 파일 경로
            output_path: 출력 파일 경로 (None이면 자동 생성)
            voice: 음성 종류
            language: 언어
            model: TTS 모델
            
        Returns:
            생성된 오디오 파일 경로
        """
        text_path = Path(text_file_path)
        if not text_path.exists():
            raise FileNotFoundError(f"텍스트 파일을 찾을 수 없습니다: {text_file_path}")
        
        # 텍스트 읽기
        with open(text_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # 출력 경로 자동 생성
        if output_path is None:
            lang_suffix = "ko" if language == "ko" else "en"
            output_path = text_path.parent / f"{text_path.stem}_tts_{lang_suffix}.mp3"
            output_path = str(output_path)
        
        return self.generate_speech(
            text=text,
            output_path=output_path,
            voice=voice,
            language=language,
            model=model
        )


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TTS 음성 생성')
    parser.add_argument('--text', type=str, help='변환할 텍스트')
    parser.add_argument('--text-file', type=str, help='텍스트 파일 경로')
    parser.add_argument('--output', type=str, required=True, help='출력 오디오 파일 경로')
    parser.add_argument('--voice', type=str, default='alloy', choices=['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'], help='음성 종류 (기본값: alloy)')
    parser.add_argument('--language', type=str, default='ko', choices=['ko', 'en'], help='언어 (기본값: ko)')
    parser.add_argument('--model', type=str, default='tts-1', choices=['tts-1', 'tts-1-hd'], help='TTS 모델 (기본값: tts-1)')
    
    args = parser.parse_args()
    
    if not args.text and not args.text_file:
        print("❌ --text 또는 --text-file 중 하나를 지정해야 합니다.")
        return 1
    
    try:
        engine = TTSEngine()
        
        if args.text_file:
            output_path = engine.generate_from_file(
                text_file_path=args.text_file,
                output_path=args.output,
                voice=args.voice,
                language=args.language,
                model=args.model
            )
        else:
            output_path = engine.generate_speech(
                text=args.text,
                output_path=args.output,
                voice=args.voice,
                language=args.language,
                model=args.model
            )
        
        print()
        print("=" * 60)
        print("✅ TTS 음성 생성 완료!")
        print("=" * 60)
        print(f"📁 저장 위치: {output_path}")
        
        return 0
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return 1


if __name__ == "__main__":
    exit(main())


