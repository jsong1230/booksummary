# Beyond Page 개선사항 구현 계획

## Context

`docs/beyond_page_todo.md`와 `docs/beyond_page_guide.md`에 정리된 채널 개선 항목들 중 **코드로 구현 가능한 항목**을 우선순위별로 구현합니다. 현재 영상 끝부분에 구독 유도가 전혀 없고(신규 시청자 97%인데 구독 전환 안 됨), 썸네일 프롬프트가 문서에만 존재하여 일관성 유지가 어려운 상황입니다.

---

## 구현 범위

### 구현 대상 (코드 변경)
| 우선순위 | 항목 | 유형 |
|---------|------|------|
| 🔴 1 | 영상 마지막 20초 구독 유도 CTA 오버레이 | 신규 모듈 + 기존 파일 수정 |
| 🔴 2 | 썸네일 프롬프트 템플릿 시스템 | 신규 파일 (templates/) |
| 🟡 3 | Input 폴더 유효성 검증 | 기존 파일 수정 |

### 구현 제외 (운영/프로세스 변경)
- 영문 영상 축소 (운영 결정)
- 커뮤니티 공유 루틴 (수동 프로세스)
- NotebookLM 배치화 (외부 도구)
- 영문 채널 분리 (전략적 결정)
- Gems 지시문 수정 (외부 도구, 단 문서화는 포함)

---

## Step 1: 구독 유도 CTA 오버레이 (🔴)

### 1.1 신규 파일 생성: `src/utils/subscribe_cta.py`

PIL 기반 반투명 하단 바 오버레이를 생성하는 유틸리티:

```
create_subscribe_cta_clip(
    duration: float = 20.0,
    language: str = "ko",
    resolution: tuple = (1920, 1080),
    opacity: float = 0.85,
    fade_in_duration: float = 1.5
) -> ImageClip or None
```

- 하단 120px 높이의 반투명 검은 바
- 한글: `"이 영상이 도움이 되셨다면 구독과 좋아요 부탁드립니다!"`
- 영문: `"If you enjoyed this, please subscribe and like!"`
- 폰트: 기존 패턴 재사용 (`AppleGothic.ttf` / `Arial`)
  - 참고: `src/03_make_video.py:1297-1315` 폰트 탐색 로직
- 1.5초 fade-in 효과
- moviepy 버전 호환 처리 (new/old API)

### 1.2 Summary+Video 파이프라인 통합

**수정 파일**: `src/03_make_video.py`

삽입 위치: line 1720 (concatenation 완료) ~ line 1727 (자막 처리) 사이

```python
# CTA 오버레이 추가
if add_subscribe_cta:
    cta_duration = min(20.0, total_duration * 0.1)
    cta_start = total_duration - cta_duration
    cta_clip = create_subscribe_cta_clip(
        duration=cta_duration, language=language,
        resolution=self.resolution
    )
    if cta_clip:
        final_video = CompositeVideoClip([final_video, cta_clip.set_start(cta_start)])
```

- `create_video()` 메서드에 `add_subscribe_cta: bool = True` 파라미터 추가
- `main()` parser에 `--no-cta` 플래그 추가

### 1.3 일당백(Episode) 파이프라인 통합

**수정 파일**: `src/create_full_episode.py`

삽입 위치: line 711 (concatenation) ~ line 722 (렌더링) 사이

동일 패턴, `create_full_episode()` 함수에 `add_subscribe_cta: bool = True` 파라미터 추가

### 1.4 상위 호출 스크립트 연결

**수정 파일**: `src/10_create_video_with_summary.py`
- `--no-cta` 옵션을 `03_make_video.py`의 `create_video()`에 전달

---

## Step 2: 썸네일 프롬프트 템플릿 (🔴)

### 2.1 디렉토리 구조 생성

```
templates/
  thumbnails/
    summary_video_ko.md    # 한글 Summary+Video 썸네일
    summary_video_en.md    # 영문 Summary+Video 썸네일
    episode_ko.md          # 한글 일당백 썸네일
    episode_en.md          # 영문 일당백 썸네일
  gems/
    gems_instructions.md   # Gems 필수 3가지 조건 문서화
```

### 2.2 템플릿 내용

`docs/beyond_page_guide.md`의 프롬프트를 구조화하여 이동:
- Summary+Video 한글 (guide.md lines 124-146)
- Summary+Video 영문 (guide.md lines 152-173)
- 일당백 한글 (guide.md lines 183-194)
- 일당백 영문 (guide.md lines 197-206)

각 템플릿에 `{author_name}`, `{hook_sentence}`, `{illustration_subject}` 등 플레이스홀더 포함

### 2.3 Gems 필수 조건 문서화

`templates/gems/gems_instructions.md`에 3가지 필수 조건 정리:
1. 훅 카피 (책 제목 그대로 X, 궁금증 유발 문장으로 변환)
2. 수채화+펜화 일러스트 스타일 (사진 리얼리즘 X)
3. 파란색 기하학 인포그래픽 프레임 (#1A73E8)

---

## Step 3: Input 폴더 유효성 검증 (🟡)

### 3.1 검증 함수 추가

**수정 파일**: `scripts/prepare_files_from_downloads.py`

```
validate_input_folder(
    input_dir: Path,
    prefix: str = None,
    style: str = "summary"  # "summary" or "episode"
) -> dict  # {'valid': bool, 'warnings': list, 'errors': list, 'detected_files': dict}
```

검증 규칙:
- Summary 스타일: audio 2개, summary(MD) 2개, thumbnail(PNG) 2개 기대
- Episode 스타일: video(MP4) 4개, infographic(PNG) 4개, thumbnail 2개 기대
- 언어 마커(`kr`/`ko`/`en`) 확인
- 인식 불가 파일 경고

### 3.2 CLI 통합

- `--validate-only` 플래그: 검증만 실행, 파일 이동 안 함
- 기본 동작: 자동 검증 후 에러 있으면 `--force` 없이는 진행 중단

---

## 핵심 파일 목록

| 파일 | 작업 |
|------|------|
| `src/utils/subscribe_cta.py` | **신규** - CTA 오버레이 생성 모듈 |
| `src/03_make_video.py` | 수정 - CTA 통합 (line 1720 부근) |
| `src/create_full_episode.py` | 수정 - CTA 통합 (line 711 부근) |
| `src/10_create_video_with_summary.py` | 수정 - `--no-cta` 옵션 전달 |
| `templates/thumbnails/*.md` | **신규** - 프롬프트 템플릿 4개 |
| `templates/gems/gems_instructions.md` | **신규** - Gems 필수 조건 |
| `scripts/prepare_files_from_downloads.py` | 수정 - 검증 함수 추가 |

---

## 검증 방법

1. **CTA 오버레이 테스트**
   - 짧은 테스트 영상으로 CTA 표시 확인 (한글/영문)
   - `--no-cta` 플래그로 CTA 없는 영상도 생성 가능 확인
   - 기존 영상 생성 워크플로우가 깨지지 않는지 확인

2. **템플릿 확인**
   - 각 템플릿 파일이 올바른 형식인지 확인
   - 플레이스홀더가 명확히 표시되어 있는지 확인

3. **Input 검증 테스트**
   - 정상 input 폴더 → valid: true
   - 파일 누락 → errors 리스트에 표시
   - `--validate-only` 플래그 동작 확인

4. **기존 테스트 실행**
   ```bash
   pytest
   ```
   모든 기존 테스트 통과 확인
