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

try:
    from google import genai as _genai_check  # noqa: F401
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from utils.logger import get_logger
except ImportError:
    from src.utils.logger import get_logger

load_dotenv()


class SummaryGenerator:
    """책 요약 생성 클래스"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.claude_api_key = os.getenv("CLAUDE_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    def generate_summary(
        self,
        book_title: str,
        author: str = None,
        language: str = "ko",
        duration_minutes: float = 5.0,
        context_text: str = None
    ) -> str:
        """
        책 요약 생성
        
        Args:
            book_title: 책 제목
            author: 저자 이름
            language: 언어 ('ko' 또는 'en')
            duration_minutes: 요약 길이 (분 단위, 기본값: 5분)
            context_text: 참고할 컨텍스트 텍스트 (예: 유튜브 자막)
            
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
        
        # 템플릿 형식 사용 (인트로/아웃트로 제거)
        # [HOOK], [SUMMARY], [BRIDGE] 형식으로만 작성
        intro_text = None
        outro_text = None
        
        # Hook 문구 생성 (언어별)
        if language == "ko":
            hook_examples = [
                "만약 당신의 인생을 바꾼 문장이 단 한 줄이라면, 이 책은 그 한 줄을 제공합니다.",
                "이 책이 전 세계에서 수천만 권 팔린 이유는, 우리가 모두 같은 고민을 하기 때문입니다.",
                "상상해보세요. 단 5초의 선택이 앞으로 5년을 결정한다면?",
                "이 이야기는 시작부터 비극입니다. 그런데 모두가 공감합니다."
            ]
            bridge_examples = [
                "지금부터 더 깊은 내용을 살펴보겠습니다.",
                "이제 이 책의 숨겨진 의미와 작가의 의도를 자세히 분석해보겠습니다.",
                "앞으로 이 작품이 우리에게 던지는 질문들을 하나씩 살펴보겠습니다."
            ]
        else:
            hook_examples = [
                "If there was one sentence that could change your life, this book provides that sentence.",
                "The reason this book has sold millions of copies worldwide is because we all share the same struggles.",
                "Imagine if a single 5-second choice could determine the next 5 years of your life?",
                "This story begins as a tragedy. Yet everyone can relate to it."
            ]
            bridge_examples = [
                "Now let's examine the deeper content.",
                "Let's analyze the hidden meanings and the author's intentions in detail.",
                "Let's explore the questions this work poses to us one by one."
            ]
        
        prompt = f"""다음 책에 대한 요약을 {lang_name}로 작성해주세요.
이 요약은 오디오북으로 녹음되어 정확히 약 {target_duration} 정도의 길이가 되도록 충분히 자세하게 작성해주세요.
(읽는 속도: 분당 약 150-180단어 기준, {target_duration} = 최소 {int(duration_minutes * 150)}단어 이상, 권장 {int(duration_minutes * 165)}단어)

**중요: 반드시 {int(duration_minutes * 150)}단어 이상 작성해야 합니다. {int(duration_minutes * 150)}단어 미만이면 너무 짧습니다.**

**요약 형식 (반드시 이 형식을 따라야 합니다):**
```
[HOOK]
(짧고 강렬한 문장 - 시청자가 3초 만에 빠져들게 하는 문장)

[SUMMARY]
({target_duration} 핵심 요약 - 최소 {int(duration_minutes * 150)}단어 이상)

[BRIDGE]
(다음 NotebookLM 분석으로 자연스럽게 넘어가는 연결 문장)
```

**HOOK 작성 가이드 (매우 중요 - 첫 15초 집중도 향상):**
- **첫 3초 안에 시청자의 호기심을 자극해야 함** (이탈 방지 핵심)
- 책의 가장 흥미롭고 충격적인 요소 활용
- 미스터리, 반전, 중요한 장면, 논쟁적 질문 등 사용
- **10-20초 분량의 강렬한 오프닝** (평균 시청 시간 향상)
- **구체적이고 감정을 자극하는 문장 사용**
- **"만약", "상상해보세요", "당신은 알고 있나요?" 같은 질문형 시작 권장**
- **숫자나 구체적 사실 포함** (예: "수천만 권 팔린 이유", "5초의 선택이 5년을 결정")
- **반전이나 충격적 사실로 시작** (예: "이 이야기는 시작부터 비극입니다")
- 예시: {hook_examples[0] if language == "ko" else hook_examples[0]}

책 제목: {book_title}
저자: {author or "알 수 없음"}
"""
        
        if context_text:
            prompt += f"""
**참고 자료 (유튜브 자막):**
다음은 이 책과 관련된 유튜브 영상의 자막입니다. 이 내용을 바탕으로 요약을 작성해주세요.
자막의 내용을 참고하되, 영상의 내용을 그대로 베끼지 말고 책의 핵심 내용을 잘 요약해서 구성해주세요.
자막 내용 중 불필요한 부분(인사말, 광고 등)은 제외하고 핵심 내용 위주로 작성해주세요.

---
{context_text[:50000]}... (내용이 길어 생략될 수 있음)
---
"""
        
        if book_info:
            if book_info.get('description'):
                prompt += f"\\n책 설명: {book_info['description'][:1000]}\\n"
            if book_info.get('categories'):
                prompt += f"카테고리: {', '.join(book_info['categories'])}\\n"
        
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
**SUMMARY 작성 가이드 (매우 중요):**
1. **반드시 최소 {int(duration_minutes * 150)}단어 이상 작성하세요. 이것은 필수 요구사항입니다.**
2. 책의 주요 내용과 줄거리를 매우 상세히 포함하세요 (각 장의 주요 사건들을 하나하나 자세히 설명)
3. 주요 등장인물과 배경을 매우 자세히 소개하세요 (인물의 성격, 배경, 역할, 심리 상태 등을 구체적으로)
4. 책의 핵심 주제와 메시지를 매우 깊이 있게 설명하세요 (작가의 의도, 사회적 의미, 철학적 함의 등을 상세히)
5. 중요한 사건이나 전개를 매우 충분히 요약하세요 (사건의 전후 맥락, 인물의 심리 변화, 배경 설명 등을 포함)
6. 각 섹션을 확장하고 구체적인 예시와 설명을 추가하세요
7. 자연스럽게 읽을 수 있는 문체로 작성하세요
8. **{target_duration} 분량을 채우기 위해 가능한 한 상세하게 작성하세요**
9. **요약이 너무 짧으면 안 됩니다. {int(duration_minutes * 150)}단어 이상이 되도록 반드시 충분히 길게 작성하세요**
10. **각 문단을 길게 작성하고, 설명을 반복하거나 다른 각도에서 다시 설명하는 것도 좋습니다**

**BRIDGE 작성 가이드:**
- 다음 NotebookLM 분석으로 자연스럽게 넘어가도록 연결
- 시청자가 계속 시청하도록 유도
- 간결하고 명확한 전환 문장
- 예시: {bridge_examples[0] if language == "ko" else bridge_examples[0]}

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
                        model="claude-3-5-sonnet-20240620",
                        max_tokens=4096,  # Claude 최대값
                        messages=[{
                            "role": "user",
                            "content": prompt
                        }]
                    )
                    summary = response.content[0].text
                    # 템플릿 형식 사용 시 인트로/아웃트로 추가하지 않음
                    if intro_text is None and outro_text is None:
                        # [HOOK], [SUMMARY], [BRIDGE] 형식만 사용
                        summary = self._clean_template_format(summary, language)
                    else:
                        summary = self._ensure_intro_outro(summary, intro_text, outro_text, language)
                except Exception as claude_error:
                    self.logger.warning(f"Claude API 오류: {claude_error}")
                    self.logger.info("🔄 OpenAI API로 대체 시도 중...")
                    # Claude 실패 시 OpenAI로 대체
                    if OPENAI_AVAILABLE and self.openai_api_key:
                        try:
                            # 최신 OpenAI API 사용
                            from openai import OpenAI
                            client = OpenAI(api_key=self.openai_api_key)
                            response = client.chat.completions.create(
                                model="gpt-4o",
                                messages=[
                                    {"role": "system", "content": f"You are a helpful assistant that generates book summaries in {lang_name}."},
                                    {"role": "user", "content": prompt}
                                ],
                                max_tokens=4000  # 최대 요약 길이 (약 15-20분 분량 가능)
                            )
                            summary = response.choices[0].message.content
                            # 템플릿 형식 사용 시 인트로/아웃트로 추가하지 않음
                            if intro_text is None and outro_text is None:
                                # [HOOK], [SUMMARY], [BRIDGE] 형식만 사용
                                summary = self._clean_template_format(summary, language)
                            else:
                                summary = self._ensure_intro_outro(summary, intro_text, outro_text, language)
                        except Exception as openai_error:
                            self.logger.error(f"OpenAI API 오류: {openai_error}")
                            # Gemini fallback
                            if GEMINI_AVAILABLE and self.gemini_api_key:
                                self.logger.info("🔄 Gemini API로 대체 시도 중...")
                                summary = self._call_gemini_api(prompt)
                                summary = self._clean_template_format(summary, language)
                            else:
                                raise openai_error
                    else:
                        # OpenAI 없으면 Gemini fallback
                        if GEMINI_AVAILABLE and self.gemini_api_key:
                            self.logger.info("🔄 Gemini API로 대체 시도 중...")
                            summary = self._call_gemini_api(prompt)
                            summary = self._clean_template_format(summary, language)
                        else:
                            raise claude_error
            # OpenAI API 사용
            elif OPENAI_AVAILABLE and self.openai_api_key:
                try:
                    # 최신 OpenAI API 사용
                    from openai import OpenAI
                    client = OpenAI(api_key=self.openai_api_key)
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": f"You are a helpful assistant that generates book summaries in {lang_name}."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=4000  # 최대 요약 길이 (약 15-20분 분량 가능)
                    )
                    summary = response.choices[0].message.content
                    # 인트로/아웃트로 확인 및 추가
                    summary = self._ensure_intro_outro(summary, intro_text, outro_text, language)
                except Exception as openai_error:
                    self.logger.error(f"OpenAI API 오류: {openai_error}")
                    if GEMINI_AVAILABLE and self.gemini_api_key:
                        self.logger.info("🔄 Gemini API로 대체 시도 중...")
                        summary = self._call_gemini_api(prompt)
                        summary = self._clean_template_format(summary, language)
                    else:
                        raise openai_error
            # Gemini API 사용
            elif GEMINI_AVAILABLE and self.gemini_api_key:
                self.logger.info("🚀 Gemini API 사용 중...")
                summary = self._call_gemini_api(prompt)
                summary = self._clean_template_format(summary, language)
            else:
                raise Exception("AI API 키가 설정되지 않았습니다. CLAUDE_API_KEY, OPENAI_API_KEY, 또는 GEMINI_API_KEY 중 하나를 설정하세요.")
            
            return summary.strip()
            
        except Exception as e:
            self.logger.error(f"요약 생성 오류: {e}")
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
        
        # 인트로가 없으면 추가, 있으면 우리가 지정한 형식인지 확인
        if not summary.strip().lower().startswith(intro_text.lower()):
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
        
        return summary
    
    def _call_gemini_api(self, prompt: str) -> str:
        """Gemini API 호출 (Vertex AI 서비스 계정 사용)"""
        from google import genai
        import google.auth

        # 서비스 계정 키 파일 경로
        key_file = Path("secrets/google-cloud-tts-key.json")
        if not key_file.exists():
            raise FileNotFoundError(f"서비스 계정 키 파일이 없습니다: {key_file}")

        credentials, _ = google.auth.load_credentials_from_file(
            str(key_file),
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        client = genai.Client(
            vertexai=True,
            project="youtubeshorts-478213",
            location="us-central1",
            credentials=credentials,
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                max_output_tokens=8192,
                temperature=0.7,
            ),
        )
        return response.text

    def _clean_template_format(self, summary: str, language: str) -> str:
        """
        템플릿 형식([HOOK], [SUMMARY], [BRIDGE])에서 불필요한 인트로/아웃트로 제거
        
        Args:
            summary: 요약 텍스트
            language: 언어
            
        Returns:
            정리된 요약 텍스트
        """
        summary = summary.strip()
        
        # 언어별 인트로 패턴 제거
        if language == "ko":
            intro_patterns = [
                "이제 소설의 내용을 요약하겠습니다",
                "요약하겠습니다",
                "요약하겠다",
                "요약합니다",
                "요약을 시작",
                "요약을 하겠습니다"
            ]
            outro_patterns = [
                "이상으로 마치겠습니다",
                "마치겠습니다",
                "마치겠다",
                "마칩니다",
                "이상으로",
                "이상입니다",
                "마무리하겠습니다"
            ]
        else:
            intro_patterns = [
                "I will now summarize the novel's content",
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
        
        # 첫 부분에서 인트로 제거
        lines = summary.split('\n')
        cleaned_lines = []
        intro_removed = False
        
        for i, line in enumerate(lines):
            # 첫 3줄 내에서 인트로 패턴 찾아서 제거
            if not intro_removed and i < 3:
                if any(pattern.lower() in line.lower() for pattern in intro_patterns):
                    intro_removed = True
                    continue
            cleaned_lines.append(line)
        
        summary = '\n'.join(cleaned_lines).strip()
        
        # 마지막 부분에서 아웃트로 제거 (BRIDGE 이후에 있는 경우)
        if '[BRIDGE]' in summary.upper() or '[BRIDGE]' in summary:
            # BRIDGE 이후의 아웃트로만 제거
            bridge_index = summary.upper().find('[BRIDGE]')
            if bridge_index != -1:
                bridge_part = summary[bridge_index:]
                main_part = summary[:bridge_index]
                
                # BRIDGE 부분에서 아웃트로 제거
                bridge_lines = bridge_part.split('\n')
                cleaned_bridge = []
                outro_removed = False
                
                for line in bridge_lines:
                    if not outro_removed:
                        if any(pattern.lower() in line.lower() for pattern in outro_patterns):
                            outro_removed = True
                            continue
                    cleaned_bridge.append(line)
                
                summary = main_part + '\n' + '\n'.join(cleaned_bridge)
        
        return summary.strip().strip()
    
    def save_summary(
        self,
        summary: str,
        book_title: str,
        author: str = None,
        language: str = "ko",
        duration_minutes: float = 5.0
    ) -> Path:
        """
        요약 텍스트 저장 (메타데이터 주석 처리 포함)
        
        Args:
            summary: 요약 텍스트
            book_title: 책 제목
            author: 저자 이름
            language: 언어
            duration_minutes: 요약 길이 (분 단위, 기본값: 5.0)
            
        Returns:
            저장된 파일 경로
        """
        from utils.file_utils import safe_title
        safe_title_str = safe_title(book_title)
        output_dir = Path("assets/summaries")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        lang_suffix = "ko" if language == "ko" else "en"
        # .md 파일로 저장 (표준 형식)
        output_path = output_dir / f"{safe_title_str}_summary_{lang_suffix}.md"
        
        # 메타데이터 주석 처리 (언어별)
        lang_name = "Korean" if language == "ko" else "English"
        
        # duration 텍스트 생성 (언어별)
        if language == "ko":
            if duration_minutes >= 1:
                duration_text = f"약 {int(duration_minutes)}분"
            else:
                duration_text = f"약 {int(duration_minutes * 60)}초"
            script_label = "서머리 스크립트"
        else:
            if duration_minutes >= 1:
                duration_text = f"about {int(duration_minutes)} minutes"
            else:
                duration_text = f"about {int(duration_minutes * 60)} seconds"
            script_label = "summary script"
        
        # 메타데이터를 HTML 주석으로 감싸기
        metadata_lines = []
        metadata_lines.append(f"<!-- 📘 {book_title} -->")
        if author:
            metadata_lines.append(f"<!-- {author} -->")
        metadata_lines.append(f"<!-- TTS 기준 {duration_text} {script_label} ({lang_name}) -->")
        metadata_lines.append("")  # 빈 줄 추가
        
        # 메타데이터 + 실제 요약 내용
        full_content = "\n".join(metadata_lines) + summary
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        self.logger.info(f"✅ 요약 저장 완료: {output_path}")
        self.logger.info("📝 메타데이터 주석 처리 완료")
        return output_path


def main():
    """메인 실행 함수"""
    import argparse
    
    logger = get_logger(__name__)
    
    parser = argparse.ArgumentParser(description='책 요약 생성')
    parser.add_argument('--title', type=str, required=True, help='책 제목')
    parser.add_argument('--author', type=str, help='저자 이름')
    parser.add_argument('--language', type=str, default='ko', choices=['ko', 'en'], help='언어 (기본값: ko)')
    parser.add_argument('--duration', type=float, default=5.0, help='요약 길이 (분 단위, 기본값: 5.0)')
    
    args = parser.parse_args()
    
    generator = SummaryGenerator()
    
    logger.info("=" * 60)
    logger.info("📚 책 요약 생성 시작")
    logger.info("=" * 60)
    logger.info(f"책 제목: {args.title}")
    logger.info(f"저자: {args.author or '알 수 없음'}")
    logger.info(f"언어: {args.language}")
    logger.info(f"목표 길이: {args.duration}분")
    
    try:
        summary = generator.generate_summary(
            book_title=args.title,
            author=args.author,
            language=args.language,
            duration_minutes=args.duration
        )
        
        output_path = generator.save_summary(
            summary=summary,
            book_title=args.title,
            author=args.author,
            language=args.language,
            duration_minutes=args.duration
        )
        
        logger.info("=" * 60)
        logger.info("✅ 요약 생성 완료!")
        logger.info("=" * 60)
        logger.info(f"📁 저장 위치: {output_path}")
        logger.info("📝 요약 미리보기:")
        logger.info("-" * 60)
        logger.info(summary[:500] + "..." if len(summary) > 500 else summary)
        logger.info("-" * 60)
        
    except Exception as e:
        logger.error(f"오류 발생: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

