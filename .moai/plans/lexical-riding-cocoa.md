# YouTube 시청자 유입 및 채널 성장 개선 Plan

## Context

BookSummary 채널의 영상 제작 파이프라인은 기능적으로 완성도가 높으나, **시청자 유입/유지/전환**을 극대화하는 기능들이 부족합니다.
현재 코드베이스를 분석한 결과, **구현은 되어 있으나 비활성화된 기능**과 **아예 없는 기능**이 혼재합니다.

### 현재 채널의 강점
- 한글/영문 이중 언어 파이프라인 완성
- AI 기반 키워드/요약/메타데이터 자동 생성
- 제휴 링크 + 고정 댓글 자동화
- Kinetic Typography + Waveform 시각 효과 활성

### 핵심 약점 (시청자 유입 관점)
1. **영상 내 구독/좋아요 CTA 없음** - description 텍스트에만 존재
2. **인트로/아웃트로 없음** - 브랜딩 부재, end screen 미활용
3. **YouTube Shorts 미활용** - 2026년 일일 2000억 뷰, 가장 큰 유입 채널
4. **Description 구조 미최적화** - 챕터 타임스탬프가 description이 아닌 고정 댓글에만 존재
5. **플레이리스트 미관리** - 연속 시청(binge-watching) 유도 부재
6. **Ken Burns 효과 비활성** - 코드는 존재하나 static 이미지 사용 중

---

## 우선순위별 구현 계획

### Phase A: Quick Wins (기존 코드 수정, 높은 ROI)

#### A1. Description에 챕터 타임스탬프 자동 삽입
- **임팩트**: 높음 (검색 노출 + 시청 편의)
- **수정 파일**: `src/08_create_and_preview_videos.py`, `src/20_create_episode_metadata.py`
- **방법**: `10_create_video_with_summary.py`가 이미 Summary/NotebookLM 구간 시간을 알고 있음. 메타데이터 생성 시 description 최상단에 타임스탬프 삽입
- **포맷**:
  ```
  0:00 도입
  0:15 5분 핵심 요약
  5:15 AI 심층 토론
  ```

#### A2. Description에 해시태그 자동 추가
- **임팩트**: 중간 (검색 노출)
- **수정 파일**: `src/08_create_and_preview_videos.py`, `src/20_create_episode_metadata.py`
- **방법**: `utils/title_generator.py`의 `_guess_genre()` 재활용하여 장르별 해시태그 2-3개 자동 생성
- **포맷**: description 맨 끝에 `#책리뷰 #BookSummary #자기계발` (한글) / `#BookReview #BookSummary #SelfHelp` (영문)

#### A3. 영상 기본 길이 8분 이상으로 조정
- **임팩트**: 높음 (미드롤 광고 활성화)
- **수정 파일**: `src/10_create_video_with_summary.py`
- **방법**: `--summary-duration` 기본값을 `5.0` → `6.0`으로 상향 (Summary 6분 + NotebookLM ≈ 8-10분 총 영상)
- **주의**: AI 프롬프트의 단어 수 목표도 함께 조정 (750 → 900단어)

#### A4. Ken Burns 효과 활성화
- **임팩트**: 중간 (시각적 품질 향상, 이탈률 감소)
- **수정 파일**: `src/03_make_video.py`
- **방법**: `create_image_sequence()` (line 505)에서 `create_image_clip_with_ken_burns()` 호출하도록 변경. 현재 static 이미지 사용 중이지만 Ken Burns 메서드가 이미 구현되어 있음
- **옵션**: `--ken-burns` 플래그 추가 또는 기본 활성화

---

### Phase B: 중기 개발 (새 기능, 매우 높은 ROI)

#### B1. YouTube Shorts 자동 생성 스크립트 (신규)
- **임팩트**: 매우 높음 (2026년 최대 유입 채널)
- **신규 파일**: `src/26_generate_shorts.py`
- **방법**:
  1. 기존 Summary의 HOOK 섹션(첫 30초) 추출
  2. 무드 이미지 + 책 인용구 텍스트 오버레이
  3. 9:16 세로 포맷으로 변환 (1080x1920)
  4. Shorts 전용 메타데이터 생성 (`#Shorts` 해시태그 필수)
  5. 기존 `moviepy` + `assets/images/` 활용
- **자동화**: 한 권의 책에서 3-5개 Shorts 자동 생성
  - Short 1: HOOK 섹션 (첫 30초)
  - Short 2: 핵심 인용구 + 무드 이미지
  - Short 3: "이 책의 한 줄 요약" + 배경 이미지

#### B2. 인트로/아웃트로 자동 삽입
- **임팩트**: 높음 (브랜딩 + end screen 활용)
- **수정 파일**: `src/03_make_video.py`, `src/create_full_episode.py`
- **방법**:
  - 인트로(3초): 채널 로고 + 책 제목 텍스트 카드, 페이드인
  - 아웃트로(15초): "구독 좋아요 알림설정" CTA + 관련 영상 추천 영역 (YouTube end screen 배치용 빈 공간)
  - `assets/branding/` 폴더에 인트로/아웃트로 템플릿 저장

#### B3. 플레이리스트 자동 관리 스크립트 (신규)
- **임팩트**: 높음 (연속 시청 유도, 총 시청시간 증가)
- **신규 파일**: `src/27_manage_playlists.py`
- **방법**:
  1. YouTube API로 채널의 모든 영상 목록 조회
  2. 장르별 자동 분류 (`title_generator.py`의 `_guess_genre()` 재활용)
  3. 플레이리스트 자동 생성/업데이트 (자기계발, 소설, 철학, 경제 등)
  4. 신규 업로드 시 자동으로 적절한 플레이리스트에 추가
- **데이터**: `ildangbaek_books.csv`에 장르 정보 추가 가능

#### B4. 고정 댓글 CTA 강화
- **임팩트**: 중간 (댓글 참여 유도)
- **수정 파일**: `src/utils/pinned_comment.py`
- **방법**: 현재 고정 댓글에 참여 유도 질문 추가
  - "이 책에서 가장 인상 깊은 구절은 무엇인가요?"
  - "다음에 리뷰할 책을 댓글로 추천해주세요!"
  - 이미 `generate_discussion_question()` 함수가 있으므로 AI 생성 질문 활용

---

### Phase C: 장기 개발 (높은 효과, 개발 비용 큼)

#### C1. 커뮤니티 탭 자동 포스팅 (신규)
- **신규 파일**: `src/28_community_posts.py`
- **방법**: YouTube Data API로 커뮤니티 포스트 자동 생성
  - 주 3회: 책 인용구(무드 이미지 재활용), 다음 리뷰 투표, 근황
  - `ildangbaek_books.csv`에서 예정 도서 목록으로 투표 생성

#### C2. 썸네일 A/B 테스트 자동화
- **수정 파일**: `src/10_generate_thumbnail.py`
- **방법**: 색상/구도 변형 2-3개 자동 생성 후 YouTube "Test & Compare" API 활용

#### C3. Summary+Video 영상에 배경음악 추가
- **수정 파일**: `src/03_make_video.py`
- **방법**: Episode 포맷에만 있는 BGM을 Summary 구간에도 적용 (저음량 ambient)

---

## 수정 대상 파일 요약

| 파일 | Phase | 변경 내용 |
|------|-------|-----------|
| `src/08_create_and_preview_videos.py` | A1, A2 | 챕터 타임스탬프 + 해시태그 삽입 |
| `src/20_create_episode_metadata.py` | A1, A2 | 에피소드 메타데이터에도 동일 적용 |
| `src/10_create_video_with_summary.py` | A3 | summary-duration 기본값 6.0, 단어 목표 조정 |
| `src/03_make_video.py` | A4, B2 | Ken Burns 활성화 + 인트로/아웃트로 |
| `src/08_generate_summary.py` | A3 | 단어 수 목표 상향 (750→900) |
| `src/utils/title_generator.py` | A2 | 해시태그 생성 함수 추가 |
| `src/26_generate_shorts.py` (신규) | B1 | Shorts 자동 생성 |
| `src/27_manage_playlists.py` (신규) | B3 | 플레이리스트 자동 관리 |
| `src/utils/pinned_comment.py` | B4 | CTA 강화 |
| `src/create_full_episode.py` | B2 | 에피소드에도 인트로/아웃트로 |
| `src/28_community_posts.py` (신규) | C1 | 커뮤니티 탭 자동화 |

## 검증 방법

1. Phase A 구현 후: 기존 pytest 통과 확인
2. 각 메타데이터 변경: `--metadata-only` 모드로 JSON 미리보기 후 description 구조 확인
3. Ken Burns: 짧은 테스트 영상(10초) 생성하여 효과 확인
4. Shorts: 테스트 책 1권으로 Shorts 3개 자동 생성 후 포맷/해상도 확인
5. 플레이리스트: `--dry-run` 모드로 장르 분류 결과 미리보기
