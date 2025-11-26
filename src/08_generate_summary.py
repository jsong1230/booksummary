"""
책 요약 생성 스크립트
AI를 사용하여 책의 요약을 생성합니다 (한글/영문)
"""

import os
import json
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# AI API 임포트
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

load_dotenv()


class SummaryGenerator:
    """책 요약 생성 클래스"""
    
    def __init__(self):
        self.claude_api_key = os.getenv("CLAUDE_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
    
    def generate_summary(
        self,
        book_title: str,
        author: str = None,
        language: str = "ko",
        duration_minutes: float = 5.0,
        use_engaging_opening: bool = False
    ) -> str:
        """
        책 요약 생성
        
        Args:
            book_title: 책 제목
            author: 저자 이름
            language: 언어 ('ko' 또는 'en')
            duration_minutes: 요약 길이 (분 단위, 기본값: 5분)
            
        Returns:
            생성된 요약 텍스트
        """
        # 책 정보 로드 시도
        book_info = None
        from utils.file_utils import safe_title
        safe_title_str = safe_title(book_title)
        book_info_path = Path("assets/images") / safe_title_str / "book_info.json"
        if book_info_path.exists():
            try:
                with open(book_info_path, 'r', encoding='utf-8') as f:
                    book_info = json.load(f)
            except:
                pass
        
        # 프롬프트 구성
        lang_name = "한국어" if language == "ko" else "English"
        target_duration = f"{int(duration_minutes)}분" if duration_minutes >= 1 else f"{int(duration_minutes * 60)}초"
        
        # 언어별 인트로/아웃트로 문구
        if use_engaging_opening:
            # 몰입형 오프닝 사용
            if language == "ko":
                intro_text = None  # AI가 생성하도록 함
                outro_text = "이상으로 마치겠습니다."
            else:
                intro_text = None  # AI가 생성하도록 함
                outro_text = "That concludes the summary."
        else:
            # 기본 인트로/아웃트로
            if language == "ko":
                intro_text = "이제 소설의 내용을 요약하겠습니다."
                outro_text = "이상으로 마치겠습니다."
            else:
                intro_text = "I will now summarize the novel's content."
                outro_text = "That concludes the summary."
        
        prompt = f"""다음 책에 대한 요약을 {lang_name}로 작성해주세요.
이 요약은 오디오북으로 녹음되어 정확히 약 {target_duration} 정도의 길이가 되도록 충분히 자세하게 작성해주세요.
(읽는 속도: 분당 약 150-180단어 기준, {target_duration} = 최소 {int(duration_minutes * 150)}단어 이상, 권장 {int(duration_minutes * 165)}단어)

**중요: 반드시 {int(duration_minutes * 150)}단어 이상 작성해야 합니다. {int(duration_minutes * 150)}단어 미만이면 너무 짧습니다.**

**요약 형식:**
{f'- 반드시 "{intro_text}"로 시작하세요' if intro_text else '- **몰입형 오프닝으로 시작하세요**: 책의 미스터리, 충격적인 장면, 인물의 비밀, 논쟁적인 질문 등으로 청취자의 호기심을 자극하는 10-20초 분량의 강렬한 오프닝을 작성하세요. 예: "이 책의 주인공은 마지막 장에서...", "이 주인공이 실제로 겪은 고난의 정체는?", "1980년 광주에서 일어난 충격적인 사건은..." 등'}
- 반드시 "{outro_text}"로 끝나세요

책 제목: {book_title}
저자: {author or "알 수 없음"}
"""
        
        if book_info:
            if book_info.get('description'):
                prompt += f"\n책 설명: {book_info['description'][:1000]}\n"
            if book_info.get('categories'):
                prompt += f"카테고리: {', '.join(book_info['categories'])}\n"
        
        # 언어별 문체 지시
        style_instruction = ""
        if language == "ko":
            style_instruction = """
**문체 지시 (한국어):**
- 반드시 존댓말(합니다, 입니다, 있습니다 등)을 사용하세요
- 반말이나 구어체를 사용하지 마세요
- 정중하고 격식 있는 문체로 작성하세요
- 예: "이 소설은...입니다", "주인공은...합니다", "이러한 상황에서...됩니다"
"""
        else:
            style_instruction = """
**Style Instructions (English):**
- Use formal and professional language
- Write in a clear and engaging narrative style
"""
        
        prompt += f"""
요약 작성 가이드 (매우 중요):
{f'1. **몰입형 오프닝 (10-20초 분량)**: 책의 가장 흥미롭고 충격적인 요소(미스터리, 반전, 중요한 장면, 논쟁적 질문 등)로 시작하여 청취자를 즉시 몰입시키세요. 스토리텔링 기반으로 호기심을 자극하세요.' if use_engaging_opening else ''}
{f'2' if not use_engaging_opening else '2'}. **반드시 최소 {int(duration_minutes * 150)}단어 이상 작성하세요. 이것은 필수 요구사항입니다.**
{f'3' if not use_engaging_opening else '3'}. 책의 주요 내용과 줄거리를 매우 상세히 포함하세요 (각 장의 주요 사건들을 하나하나 자세히 설명)
{f'4' if not use_engaging_opening else '4'}. 주요 등장인물과 배경을 매우 자세히 소개하세요 (인물의 성격, 배경, 역할, 심리 상태 등을 구체적으로)
{f'5' if not use_engaging_opening else '5'}. 책의 핵심 주제와 메시지를 매우 깊이 있게 설명하세요 (작가의 의도, 사회적 의미, 철학적 함의 등을 상세히)
{f'6' if not use_engaging_opening else '6'}. 중요한 사건이나 전개를 매우 충분히 요약하세요 (사건의 전후 맥락, 인물의 심리 변화, 배경 설명 등을 포함)
{f'7' if not use_engaging_opening else '7'}. 각 섹션을 확장하고 구체적인 예시와 설명을 추가하세요
{f'8' if not use_engaging_opening else '8'}. 자연스럽게 읽을 수 있는 문체로 작성하세요
{f'9' if not use_engaging_opening else '9'}. **{target_duration} 분량을 채우기 위해 가능한 한 상세하게 작성하세요**
{f'10' if not use_engaging_opening else '10'}. **요약이 너무 짧으면 안 됩니다. {int(duration_minutes * 150)}단어 이상이 되도록 반드시 충분히 길게 작성하세요**
{f'11' if not use_engaging_opening else '11'}. **각 문단을 길게 작성하고, 설명을 반복하거나 다른 각도에서 다시 설명하는 것도 좋습니다**
{f'12. **오프닝에서 제기한 호기심을 본문에서 자연스럽게 풀어가며, 몰입형 오프닝과 본문이 자연스럽게 연결되도록 작성하세요.' if use_engaging_opening else ''}

{style_instruction}

**최종 확인사항 (반드시 확인):**
- **반드시 {int(duration_minutes * 150)}단어 이상 작성했는지 확인하세요. {int(duration_minutes * 150)}단어 미만이면 실패입니다.**
- {int(duration_minutes * 150)}단어 미만이면 요약을 더 확장하고 상세히 작성하세요
- 각 섹션을 더 길게 작성하고, 구체적인 예시와 설명을 추가하세요
- {lang_name}로만 작성하세요
- 자연스럽게 읽을 수 있는 문체로 작성하세요
- 문단을 적절히 나누어 가독성을 높이세요
- 책의 전체적인 흐름을 이해할 수 있도록 작성하세요
"""
        
        try:
            # Claude API 우선 사용
            if ANTHROPIC_AVAILABLE and self.claude_api_key:
                try:
                    client = anthropic.Anthropic(api_key=self.claude_api_key)
                    response = client.messages.create(
                        model="claude-3-opus-20240229",
                        max_tokens=4096,  # Claude 최대값
                        messages=[{
                            "role": "user",
                            "content": prompt
                        }]
                    )
                    summary = response.content[0].text
                    # 인트로/아웃트로 확인 및 추가 (몰입형 오프닝인 경우 intro_text가 None일 수 있음)
                    if intro_text:
                        summary = self._ensure_intro_outro(summary, intro_text, outro_text, language)
                    else:
                        # 몰입형 오프닝인 경우 outro만 확인
                        if outro_text and outro_text not in summary:
                            summary = summary.rstrip() + f"\n\n{outro_text}"
                except Exception as claude_error:
                    print(f"⚠️ Claude API 오류: {claude_error}")
                    print("🔄 OpenAI API로 대체 시도 중...")
                    # Claude 실패 시 OpenAI로 대체
                    if OPENAI_AVAILABLE and self.openai_api_key:
                        try:
                            # 최신 OpenAI API 사용
                            from openai import OpenAI
                            client = OpenAI(api_key=self.openai_api_key)
                            response = client.chat.completions.create(
                                model="gpt-4",
                                messages=[
                                    {"role": "system", "content": f"You are a helpful assistant that generates book summaries in {lang_name}."},
                                    {"role": "user", "content": prompt}
                                ],
                                max_tokens=4000  # 최대 요약 길이 (약 15-20분 분량 가능)
                            )
                            summary = response.choices[0].message.content
                            # 인트로/아웃트로 확인 및 추가 (몰입형 오프닝인 경우 intro_text가 None일 수 있음)
                            if intro_text:
                                summary = self._ensure_intro_outro(summary, intro_text, outro_text, language)
                            else:
                                # 몰입형 오프닝인 경우 outro만 확인
                                if outro_text and outro_text not in summary:
                                    summary = summary.rstrip() + f"\n\n{outro_text}"
                        except Exception as openai_error:
                            print(f"❌ OpenAI API 오류: {openai_error}")
                            raise openai_error
                    else:
                        raise claude_error
            # OpenAI API 사용
            elif OPENAI_AVAILABLE and self.openai_api_key:
                try:
                    # 최신 OpenAI API 사용
                    from openai import OpenAI
                    client = OpenAI(api_key=self.openai_api_key)
                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": f"You are a helpful assistant that generates book summaries in {lang_name}."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=4000  # 최대 요약 길이 (약 15-20분 분량 가능)
                    )
                    summary = response.choices[0].message.content
                    # 인트로/아웃트로 확인 및 추가 (몰입형 오프닝인 경우 intro_text가 None일 수 있음)
                    if intro_text:
                        summary = self._ensure_intro_outro(summary, intro_text, outro_text, language)
                    else:
                        # 몰입형 오프닝인 경우 outro만 확인
                        if outro_text and outro_text not in summary:
                            summary = summary.rstrip() + f"\n\n{outro_text}"
                except Exception as openai_error:
                    print(f"❌ OpenAI API 오류: {openai_error}")
                    raise openai_error
            else:
                raise Exception("AI API 키가 설정되지 않았습니다.")
            
            return summary.strip()
            
        except Exception as e:
            print(f"❌ 요약 생성 오류: {e}")
            raise
    
    def _ensure_intro_outro(
        self,
        summary: str,
        intro_text: str,
        outro_text: str,
        language: str
    ) -> str:
        """
        요약 텍스트에 인트로와 아웃트로가 있는지 확인하고 없으면 추가
        중복 제거 로직 포함
        
        Args:
            summary: 요약 텍스트
            intro_text: 인트로 문구
            outro_text: 아웃트로 문구
            language: 언어
            
        Returns:
            인트로/아웃트로가 포함된 요약 텍스트
        """
        summary = summary.strip()
        
        # 언어별 인트로 패턴 설정
        if language == "ko":
            intro_patterns = [
                "요약하겠습니다",
                "요약하겠다",
                "요약합니다",
                "요약을 시작",
                "요약을 하겠습니다"
            ]
            outro_patterns = [
                "마치겠습니다",
                "마치겠다",
                "마칩니다",
                "이상으로",
                "이상입니다",
                "마무리하겠습니다"
            ]
        else:  # en
            intro_patterns = [
                "I will now summarize",
                "I will summarize",
                "summarize the novel",
                "summary of the novel",
                "summarizing the novel"
            ]
            outro_patterns = [
                "That concludes the summary",
                "This concludes the summary",
                "concludes the summary",
                "end of the summary",
                "summary concludes"
            ]
        
        # 첫 200자 내에서 인트로 패턴 확인
        first_part = summary[:200] if len(summary) > 200 else summary
        has_intro = False
        for pattern in intro_patterns:
            if pattern.lower() in first_part.lower():
                has_intro = True
                break
        
        # 인트로 중복 제거
        if has_intro:
            lines = summary.split('\n')
            new_lines = []
            intro_removed = False
            for i, line in enumerate(lines):
                # 첫 5줄 내에서 인트로 패턴 찾아서 제거 (한 번만)
                if not intro_removed and i < 5:
                    if any(p.lower() in line.lower() for p in intro_patterns):
                        intro_removed = True
                        continue
                new_lines.append(line)
            summary = '\n'.join(new_lines).strip()
        
        # 인트로가 없으면 추가, 있으면 우리가 지정한 형식인지 확인 (intro_text가 None이 아닌 경우만)
        if intro_text and not summary.strip().lower().startswith(intro_text.lower()):
            # 기존 인트로가 우리 형식이 아니면 제거하고 추가
            lines = summary.split('\n')
            new_lines = []
            for i, line in enumerate(lines[:5]):  # 첫 5줄만 확인
                if any(p.lower() in line.lower() for p in intro_patterns):
                    continue
                new_lines.append(line)
            if len(lines) > 5:
                new_lines.extend(lines[5:])
            summary = '\n'.join(new_lines).strip()
            summary = f"{intro_text}\n\n{summary}"
        
        # 마지막 200자 내에서 아웃트로 패턴 확인
        last_part = summary[-200:] if len(summary) > 200 else summary
        has_outro = False
        for pattern in outro_patterns:
            if pattern.lower() in last_part.lower():
                has_outro = True
                break
        
        # 아웃트로 중복 제거
        if has_outro:
            lines = summary.split('\n')
            new_lines = []
            outro_removed = False
            for i in range(len(lines) - 1, -1, -1):
                # 마지막 5줄 내에서 아웃트로 패턴 찾아서 제거 (한 번만)
                if not outro_removed and i >= len(lines) - 5:
                    if any(p.lower() in lines[i].lower() for p in outro_patterns):
                        outro_removed = True
                        continue
                new_lines.insert(0, lines[i])
            summary = '\n'.join(new_lines).strip()
        
        # 아웃트로가 없으면 추가, 있으면 우리가 지정한 형식인지 확인
        if not summary.strip().lower().endswith(outro_text.lower()):
            # 기존 아웃트로가 우리 형식이 아니면 제거하고 추가
            lines = summary.split('\n')
            new_lines = []
            for i in range(len(lines) - 1, max(-1, len(lines) - 6), -1):  # 마지막 5줄만 확인
                if any(p.lower() in lines[i].lower() for p in outro_patterns):
                    continue
                new_lines.insert(0, lines[i])
            if len(lines) > 5:
                new_lines = lines[:len(lines) - 5] + new_lines
            summary = '\n'.join(new_lines).strip()
            summary = f"{summary}\n\n{outro_text}"
        
        return summary.strip()
    
    def save_summary(
        self,
        summary: str,
        book_title: str,
        language: str = "ko"
    ) -> Path:
        """
        요약 텍스트 저장
        
        Args:
            summary: 요약 텍스트
            book_title: 책 제목
            language: 언어
            
        Returns:
            저장된 파일 경로
        """
        from utils.file_utils import safe_title
        safe_title_str = safe_title(book_title)
        output_dir = Path("assets/summaries")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        lang_suffix = "ko" if language == "ko" else "en"
        output_path = output_dir / f"{safe_title_str}_summary_{lang_suffix}.txt"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print(f"✅ 요약 저장 완료: {output_path}")
        return output_path


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='책 요약 생성')
    parser.add_argument('--title', type=str, required=True, help='책 제목')
    parser.add_argument('--author', type=str, help='저자 이름')
    parser.add_argument('--language', type=str, default='ko', choices=['ko', 'en'], help='언어 (기본값: ko)')
    parser.add_argument('--duration', type=float, default=5.0, help='요약 길이 (분 단위, 기본값: 5.0)')
    parser.add_argument('--engaging-opening', action='store_true', help='몰입형 오프닝 사용 (호기심을 자극하는 스타일)')
    
    args = parser.parse_args()
    
    generator = SummaryGenerator()
    
    print("=" * 60)
    print("📚 책 요약 생성 시작")
    print("=" * 60)
    print(f"책 제목: {args.title}")
    print(f"저자: {args.author or '알 수 없음'}")
    print(f"언어: {args.language}")
    print(f"목표 길이: {args.duration}분")
    print()
    
    try:
        summary = generator.generate_summary(
            book_title=args.title,
            author=args.author,
            language=args.language,
            duration_minutes=args.duration,
            use_engaging_opening=args.engaging_opening
        )
        
        output_path = generator.save_summary(
            summary=summary,
            book_title=args.title,
            language=args.language
        )
        
        print()
        print("=" * 60)
        print("✅ 요약 생성 완료!")
        print("=" * 60)
        print(f"📁 저장 위치: {output_path}")
        print()
        print("📝 요약 미리보기:")
        print("-" * 60)
        print(summary[:500] + "..." if len(summary) > 500 else summary)
        print("-" * 60)
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

