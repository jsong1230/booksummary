# BookSummary 기술 스택

## 기술 스택 개요

| 계층 | 기술 | 버전 | 역할 |
|------|------|------|------|
| **언어** | Python | 3.11.10 | 전체 파이프라인 |
| **런타임** | pyenv | - | Python 버전 관리 |
| **패키지** | pip | - | Python 패키지 관리 |
| **테스트** | pytest | - | 단위 테스트 프레임워크 |
| **타입 검사** | pyright | - | 정적 타입 검사 |

## 프레임워크 및 라이브러리

### 비디오 처리

**MoviePy** (버전: 1.0.3)
- 목적: 이미지 + 오디오 영상 합성, 영상 편집
- 역할: Summary+Video와 일당백 스타일 최종 영상 생성
- 선택 이유: 파이썬 기반 강력한 영상 편집 라이브러리, 크로스플랫폼 지원
- 주요 기능: 클립 연결, 사운드 트랙 합성, 프레임 레이트 조정

**Pillow** (버전: 10.0.0)
- 목적: 이미지 처리 및 변환
- 역할: PNG → JPG 변환, 이미지 리사이징, 썸네일 생성
- 선택 이유: 빠르고 가벼운 이미지 처리 라이브러리
- 주요 기능: 이미지 로드/저장, 필터 적용, 텍스트 추가

### AI 및 API 클라이언트

**OpenAI** (anthropic 라이브러리)
- 목적: GPT 모델 기반 요약 생성 및 TTS
- API: OpenAI API (Chat Completions, Text-to-Speech)
- 모델: gpt-4-turbo (요약), TTS (nova, alloy, echo, fable, onyx, shimmer)
- 역할: 책 요약 텍스트 생성, 자연스러운 음성 생성
- 선택 이유: 가장 자연스러운 음성, 빠른 응답 속도, 비용 효율적
- 사용량: 요약당 평균 2,000-3,000 tokens

**Anthropic** (anthropic 라이브러리)
- 목적: Claude API 기반 고급 요약 생성
- API: Anthropic Claude API
- 모델: claude-3-5-sonnet-20241022
- 역할: 복잡한 책 분석 및 고품질 요약 생성
- 선택 이유: 최신 Claude 모델, 뛰어난 이해도, 한국어 지원
- 사용량: 요약당 평균 3,000-4,000 tokens

**Google Cloud Text-to-Speech**
- 목적: 고품질 한국어 음성 생성
- API: Google Cloud TTS Neural2
- 모델: ko-KR-Neural2-A (여성), ko-KR-Neural2-B (남성), ko-KR-Neural2-C (여성), ko-KR-Neural2-D (남성)
- 역할: 자연스러운 한국어 음성, TTS 제공자 선택 옵션
- 선택 이유: 가장 정확한 한국어 발음, Neural2 음성 품질 최고
- 인증: Google Cloud 서비스 계정 (secrets/google-cloud-tts-key.json)

**Replicate**
- 목적: 오픈소스 기반 다국어 TTS
- API: Replicate API
- 모델: xtts-v2 (Multilingual TTS)
- 역할: 다양한 언어의 TTS 생성, 비용 절감 옵션
- 선택 이유: 오픈소스, 완전 제어 가능, 다국어 지원

### YouTube 통합

**google-api-python-client** (버전: 1.12.0)
- 목적: YouTube Data API v3 클라이언트
- API: YouTube Data API v3
- 할당량: 10,000 units/day (약 50-60개 영상 업로드)
- 역할: 영상 업로드, 메타데이터 설정, 재생목록 추가, 댓글 관리
- 인증: OAuth 2.0 (secrets/client_secret.json, secrets/credentials.json)

**oauth2client** (버전: 4.1.3)
- 목적: OAuth 2.0 인증 처리
- 역할: YouTube API 인증 토큰 관리, 토큰 갱신
- 선택 이유: YouTube API의 표준 인증 라이브러리

### 이미지 수집 API

**Pexels API**
- 목적: 무료 고품질 이미지 제공
- 역할: 책 주제 관련 이미지 다운로드
- 활용: 주요 이미지 소스 (100개 중 40개)
- 비용: 무료

**Pixabay API**
- 목적: 무료 이미지 및 비디오 제공
- 역할: 책 주제 관련 이미지 다운로드
- 활용: 보조 이미지 소스 (100개 중 35개)
- 비용: 무료

**Unsplash API**
- 목적: 창작자 친화적 무료 이미지
- 역할: 책 주제 관련 이미지 다운로드
- 활용: 보조 이미지 소스 (100개 중 25개)
- 비용: 무료

**Google Books API**
- 목적: 책 정보 및 커버 이미지 제공
- 역할: 책 커버 자동 다운로드, 책 설명 추출
- 활용: 책 정보 메타데이터 수집

### 제휴 및 마케팅

**Amazon Associates API**
- 목적: Amazon 제휴 링크 생성
- 태그: joohans-20
- 역할: 책 구매 링크 자동 생성
- 구현: URL 매개변수 기반 (title + partner tag)

**알라딘 TTB (Text-to-Business)**
- 목적: 한국 도서 제휴 링크
- ID: ttbjsong12301317001
- 역할: 한국 도서 구매 링크 자동 생성
- 구현: 검색 기반 URL 생성

### 데이터 처리

**requests** (버전: 2.31.0)
- 목적: HTTP 요청 처리
- 역할: API 호출, 이미지 다운로드, 웹 스크래핑
- 사용: YouTube 자막 다운로드, 이미지 수집

**python-dotenv** (버전: 1.0.0)
- 목적: 환경 변수 관리
- 역할: .env 파일에서 API 키 및 설정값 로드
- 파일 위치: `/Users/jsong/dev/jsong1230-github/booksummary/.env`

**youtube-transcript-api** (버전: 0.6.1)
- 목적: YouTube 자막 추출
- 역할: 일당백 스타일 영상 제작을 위한 스크립트 다운로드
- 스크립트: `scripts/fetch_separate_scripts.py`

### 유틸리티

**argparse**
- 목적: 커맨드 라인 인터페이스
- 역할: 각 스크립트의 파라미터 처리
- 사용: `--book-title`, `--language`, `--provider` 등

## API 통합

### YouTube Data API v3

**엔드포인트 및 기능:**

| 기능 | 메서드 | 할당량 |
|------|--------|--------|
| 영상 업로드 | resumable.insert | 1,500 units |
| 메타데이터 설정 | videos.update | 50 units |
| 재생목록 추가 | playlistItems.insert | 50 units |
| 댓글 추가 | comments.insert | 50 units |
| 채널 정보 조회 | channels.list | 1 unit |

**일일 할당량:** 10,000 units
- 이론적 한계: 약 6-7개 영상 완전 업로드
- 실제 운영: 약 50-60개 영상 빠른 처리

**인증 방식:**
- OAuth 2.0 (3-legged)
- 사용자 동의 필요 (첫 설정 시 1회)
- 토큰 자동 갱신

### OpenAI API

**엔드포인트:**
- Chat Completions (요약 생성): gpt-4-turbo
- Text-to-Speech: nova, alloy, echo, fable, onyx, shimmer

**TTS 음성 선택:**

| 제공자 | 음성 | 언어 | 특징 |
|--------|------|------|------|
| OpenAI | nova | ko/en | 자연스러움, 기본값 |
| OpenAI | alloy | en | 중성적, 영문 권장 |
| OpenAI | echo | ko/en | 남성적 음성 |
| OpenAI | fable | en | 영국식 악센트 |
| Google Neural2 | A | ko | 여성, 가장 자연스러움 |
| Google Neural2 | B | ko | 남성, 깊은 목소리 |

**가격:** 약 $0.10 per 1M 입력 문자 (TTS)

### Google Cloud APIs

**서비스:**
- Text-to-Speech Neural2 (한국어)
- Books API (책 정보 조회)

**인증:** 서비스 계정 (JSON 키 파일)

### Anthropic API

**모델:** claude-3-5-sonnet-20241022
- 입력: $3 per 1M 토큰
- 출력: $15 per 1M 토큰

**사용:** 고급 요약 생성, 복잡한 텍스트 분석

## 개발 환경 설정

### Python 환경

**Python 버전:** 3.11.10
- 관리자: pyenv
- 설치 경로: `/Users/jsong/.pyenv/versions/3.11.10/bin/python`
- 가상환경: `.venv` (문제 있음, pyenv Python 직접 사용 권장)

**권장 명령:**
```bash
# pyenv Python 직접 사용 (권장)
/Users/jsong/.pyenv/versions/3.11.10/bin/python script.py

# 또는 alias 설정
alias python311="/Users/jsong/.pyenv/versions/3.11.10/bin/python"
python311 script.py
```

### 의존성 설치

```bash
# pip 업그레이드
pip install --upgrade pip

# 의존성 설치
pip install -r requirements.txt

# 개발 의존성 (선택사항)
pip install pytest pyright black ruff isort
```

### 환경 변수 설정

**파일 위치:** `/Users/jsong/dev/jsong1230-github/booksummary/.env`

**필수 변수:**

```env
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Google Cloud
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=secrets/google-cloud-tts-key.json

# YouTube
YOUTUBE_API_KEY=AIzaSy...
YOUTUBE_CLIENT_ID=xxx.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=xxx

# Replicate
REPLICATE_API_TOKEN=r8_...

# 이미지 API
PEXELS_API_KEY=
PIXABAY_API_KEY=
UNSPLASH_API_KEY=

# 제휴
AMAZON_ASSOCIATE_TAG=joohans-20
ALADIN_TTB_ID=ttbjsong12301317001

# 설정
TTS_PROVIDER=openai  # openai, google, replicate
TTS_VOICE=nova       # 제공자별 음성
SUMMARY_DURATION=5.0 # 분 단위
SUMMARY_AUDIO_VOLUME=1.2  # 음량 배수
```

## 테스트 설정

### 테스트 프레임워크

**pytest** - 단위 테스트 실행
```bash
pytest                          # 모든 테스트 실행
pytest tests/test_translations.py  # 특정 테스트
pytest --cov=src               # 커버리지 리포트
```

### 테스트 커버리지

**현재 상태:** ~40-50%
- `test_translations.py` - 번역 매핑 (높음)
- `test_affiliate_links.py` - 제휴 링크 (높음)
- `test_video_utils.py` - 영상 유틸리티 (중간)
- `test_integration.py` - 통합 테스트 (낮음)

### 타입 검사

**pyright** - 정적 타입 검사
```bash
pyright src/                    # 타입 검사
pyright --version              # 버전 확인
```

## 인증 및 보안

### API 인증

**YouTube API:**
- 유형: OAuth 2.0 (3-legged)
- 파일:
  - `secrets/client_secret.json` - 클라이언트 ID/비밀
  - `secrets/credentials.json` - 액세스 토큰
- 설정: 첫 실행 시 브라우저에서 승인 필요

**Google Cloud:**
- 유형: Service Account (JSON 키)
- 파일: `secrets/google-cloud-tts-key.json`
- 설정: Google Cloud Console에서 생성

**API 키 관리:**
- OpenAI: `OPENAI_API_KEY` (환경 변수)
- Anthropic: `ANTHROPIC_API_KEY` (환경 변수)
- Pexels/Pixabay/Unsplash: 환경 변수로 관리

### 보안 정책

**절대 커밋 금지 파일:**
- `secrets/*` - 모든 인증 파일
- `.env` - 환경 변수 (비밀 포함)
- `*.key`, `*.pem` - 개인 키

**Git 무시 설정:**
```
secrets/
.env
.env.local
*.key
*.pem
credentials.json
```

## 알려진 제약사항

### YouTube API 할당량

**일일 한계:** 10,000 units/day

**영상당 비용:**
- 업로드: 1,500 units
- 메타데이터 설정: 50 units
- 재생목록 추가: 50 units
- 댓글 추가: 50 units
- 총계: ~1,650 units

**일일 한계:** 약 6-7개 영상 완전 처리

**우회 전략:**
- 오후/저녁에 업로드 (일일 할당량 갱신: 자정 PST)
- 배치 처리: 여러 날에 걸쳐 업로드
- 메타데이터는 미리 준비

### NotebookLM 의존성

**제약:**
- 오디오/비디오 수동 생성 필요 (API 없음)
- 음성 선택 불가 (자동 생성)
- 길이 제어 불가

**우회:** 별도 TTS 생성 후 오디오 대체

### 썸네일 자동 생성

**현재:** AI 생성 X, 사용자 제공 또는 기본 템플릿
- input/ 폴더의 이미지 사용
- PNG → JPG 자동 변환
- 크기 조정 (1280x720 권장)

**개선 기회:** DALL-E 또는 Stable Diffusion 통합

### 자동 번역

**현재:** 매핑 기반 (200+ 항목)
- 한글 ↔ 영문 직역
- 새로운 책 추가 시 수동 매핑 필요

**개선 기회:** Claude API 기반 자동 번역

## 성능 최적화

### 병렬 처리

**지원:** 이미지 다운로드, API 호출
```python
# 100개 이미지 동시 다운로드 (약 2-3초)
# 순차 처리: 100-150초 → 병렬: 10-15초
```

### 캐싱 전략

**구현:**
- 이미 다운로드한 이미지 건너뛰기
- API 결과 로컬 저장 (book_info.json)
- 중복 요청 방지

### 리소스 최적화

**메모리:** MoviePy 영상 처리 시 청크 단위 처리
**디스크:** 중간 파일 자동 정리
**네트워크:** 이미지 압축 (JPEG 품질 85%)

## 배포 및 모니터링

### 실행 환경

- **OS:** macOS (Darwin 25.3.0)
- **Shell:** zsh
- **Python:** 3.11.10 (pyenv)
- **프로젝트 경로:** `/Users/jsong/dev/jsong1230-github/booksummary`

### 로깅

**구현:**
- 스크립트별 로그 파일
- 실행 시간 기록
- 에러 추적 및 재시도 메커니즘

### 에러 처리

**전략:**
1. API 실패 시 지수 백오프 재시도 (최대 3회)
2. 네트워크 오류 자동 복구
3. 부분 실패 시 실패한 항목만 재처리
4. 상세한 에러 로깅

## 성능 벤치마크

| 작업 | 소요시간 | 변수 |
|------|---------|------|
| 이미지 100개 수집 | 10-20초 | API 속도, 네트워크 |
| 요약 생성 | 30-60초 | 책 길이, 모델 선택 |
| TTS 음성 생성 | 60-120초 | 요약 길이 (5분) |
| 영상 합성 | 180-300초 | 영상 길이, 품질 |
| YouTube 업로드 | 120-240초 | 네트워크, 파일 크기 |
| 전체 파이프라인 | 10-15분 | 모든 변수 종합 |

---

문서 생성 완료: 2026-02-19
마지막 업데이트: 2026-02-19
