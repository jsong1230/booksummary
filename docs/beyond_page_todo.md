# Beyond Page — 개선 TODO 리스트 & Claude Code 프롬프트

---

## 📋 TODO 리스트

### 🔴 즉시 (이번 주)

- [ ] **썸네일 훅 카피 전환** — 책 제목 그대로 쓰지 않고 "저자명: 핵심 메시지 한 문장"으로 변경
- [ ] **일당백 썸네일 프롬프트 교체** — "롱폼용 썸네일 생성해줘" → 개선된 프롬프트로 교체
- [ ] **Gems 지시문 수정** — Summary+Video 썸네일 프롬프트에 훅 카피·일러스트·파란 프레임 3가지 조건 추가
- [ ] **영상 마지막 20초 구독 유도 멘트 추가** — 신규 시청자 97%인데 구독 전환이 안 되는 핵심 원인

### 🟡 이번 달

- [ ] **영문 영상 주 4개 → 주 2개로 축소** — 리소스 50% 투입, 기여 10% 미만. 절약 에너지를 한글 품질에 투자
- [ ] **업로드 후 48시간 커뮤니티 공유 루틴 만들기** — 책 장르별 공유처 정리
  - 인문고전 → 독서 카카오오픈채팅, 네이버 독서 카페
  - AI/기술 → 클리앙, 관련 오픈채팅
  - 자기계발 → 관련 카페/커뮤니티
- [ ] **Claude Code input 폴더 구조 표준화** — 새 프롬프트 기준으로 파일 정리 습관 통일
- [ ] **1위 영상 썸네일 스타일 분석 → 표준 적용** — "생각에 관한 생각" CTR 3.7% 패턴을 summary 계열에 적용

### 🟢 다음 달 이후

- [ ] **NotebookLM 세션 배치화** — 매일 컨텍스트 스위칭 대신 주 2회 몰아서 처리
- [ ] **콘텐츠 큐 시스템 구축** — Notion 또는 Google Sheets로 책 선정~업로드 상태 추적
- [ ] **배치 처리 프롬프트 실제 적용** — input_queue 폴더 기반 자동화
- [ ] **영문 채널 별도 분리 검토** — 한글 채널 구독자 500명 이후 타이밍

---

## 💻 Claude Code 복붙 프롬프트

---

### 1. Summary+Video 영상 생성

```
[저자명-책제목] summary+video 형식으로 한글 영문 영상 생성해줘.

input 폴더에서 파일을 아래 역할 기준으로 자동 인식해줘:
- PNG 2개 → 썸네일 (한글/영문 구분)
- MD 2개 → 요약 스크립트 (한글/영문 구분)
- MP4 2개 → NotebookLM 동영상 (한글/영문 구분)
언어 구분이 불명확하면 파일명의 ko/en, korean/english, 한글/영문 키워드로 판단.
그래도 불명확하면 파일 내용을 읽어서 언어 판단.

output 폴더에 다음 2개 영상 생성:
1. [저자명-책제목]_ko.mp4 (한글 — 요약 스크립트 + NotebookLM 동영상 합본)
2. [저자명-책제목]_en.mp4 (영문 — 요약 스크립트 + NotebookLM 동영상 합본)

각 영상 규격:
- 해상도: 1920x1080 (16:9)
- 썸네일 표시 시간: 3초 (페이드인)
- 스크립트 기반 자막 자동 삽입
- 배경음악: bgm 폴더 내 파일 랜덤 선택 (볼륨 15%)
```

---

### 2. 일당백 영상 생성

```
[저자명-책제목] 일당백 스타일 한글 영문 영상 생성해줘.

input 폴더에서 파일을 아래 역할 기준으로 자동 인식해줘:
- PNG 중 썸네일 2개 (한글/영문 구분)
- PNG 중 인포그래픽 4개 (한글 1·2, 영문 1·2 구분)
- MP4 4개 → NotebookLM 동영상
  (한글 part1, 한글 part2, 영문 part1, 영문 part2 구분)
언어·파트 구분이 불명확하면 파일명의 ko/en, part1/part2,
infographic 등 키워드로 판단.
그래도 불명확하면 파일 크기·길이 순서로 판단.

output 폴더에 다음 2개 영상 생성:
1. [저자명-책제목]_1dang100_ko.mp4 (한글 일당백, 13~16분)
2. [저자명-책제목]_1dang100_en.mp4 (영문 일당백, 13~16분)

편집 구조 (한글 기준):
- 0:00~0:10 썸네일 인트로 (페이드인)
- Part 1 동영상 재생
- 챕터 구분 인터타이틀 삽입
- 인포그래픽 1 삽입 (10초 표시, 페이드 0.5초)
- Part 2 동영상 재생
- 인포그래픽 2 삽입 (10초 표시, 페이드 0.5초)
- 아웃트로 5초

각 영상 규격:
- 해상도: 1920x1080 (16:9)
- 배경음악: bgm 폴더 내 파일 랜덤 선택 (볼륨 10%)
```

---

### 3. 배치 처리 (큐 기반)

```
input_queue 폴더에 있는 모든 서브폴더를 순서대로 처리해서 영상 생성해줘.

각 서브폴더 이름 형식: [저자명-책제목_유형]
유형: summary / 1dang100

처리 순서:
1. 폴더명에서 저자명, 책제목, 유형 파싱
2. 유형에 따라 summary 또는 1dang100 워크플로우 실행
3. output 폴더에 결과 저장
4. 처리 완료된 폴더를 input_queue/done/ 으로 이동
5. 처리 로그를 process_log.txt에 기록

오류 발생 시:
- 해당 폴더 처리 건너뛰고 다음 폴더 처리 계속
- 오류 내용을 process_log.txt에 기록
```

---

### 4. 한글 일당백 썸네일 (Nano Banana용)

```
[저자명]-[책제목] 일당백 스타일 한글 썸네일 만들어줘.

형식:
- 16:9, 1920x1080
- 배경: 흰색 + 격자 패턴
- 파란색 인포그래픽 테두리 프레임 (원·사각형 기하학 도형, 좌우 가장자리)
- 상단 텍스트: "[저자명]: [이 책의 핵심 메시지를 호기심 유발 문장으로]"
  → 책 제목 그대로 쓰지 말 것. 궁금증을 유발하는 한 문장으로 변환.
  → 굵은 블랙 한글, 매우 크게, 센터 정렬
- 하단 일러스트: [저자 or 책 캐릭터]의 수채화+펜화 스타일 일러스트.
  배경에 책의 세계관 반영. 사진 리얼리즘 절대 사용하지 말 것.
- 전체 느낌: 깔끔하고 밝음. 일러스트가 포인트.
```

---

### 5. 영문 일당백 썸네일 (Nano Banana용)

```
[Author]-[Title] 1DANG100 style English thumbnail.

Format: 16:9, 1920x1080
Background: White with faint grid/notebook paper texture
Frame: Blue geometric infographic-style border (circles + rectangles on left and right edges, #1A73E8)
Top text: "[Author]: [Hook sentence — NOT the book title. Convert to a curiosity-driven one-liner.]"
  → Bold black sans-serif, very large, centered
Bottom illustration: Watercolor + pen-and-ink style portrait of [author/main character]
  with thematic background reflecting the book's world. NOT photorealistic.
Overall feel: Clean, bright, illustration as focal point.

DO NOT include: photorealistic imagery, dark background, excessive text, logos, channel name.
```

---

### 6. 한글 Summary+Video 썸네일 (Nano Banana용)

```
Create a YouTube thumbnail in 16:9 ratio (1920x1080px).

LAYOUT:
- White background with faint grid/notebook paper texture
- Blue geometric frame elements on left and right edges
  (circles and rectangles, infographic UI style, #1A73E8)
- Top 35%: Large bold Korean text, black, centered, maximum contrast
- Bottom 60%: Illustrated scene

TEXT (top area):
"[저자명]: [책의 핵심 메시지를 궁금증을 유발하는 한 문장으로]"
→ 책 제목 그대로 쓰지 말 것. 훅 카피로 변환할 것.
Font: Bold sans-serif, very large (80-90pt), black

ILLUSTRATED SCENE (bottom area):
Watercolor and pen-and-ink illustration style, NOT photorealistic.
Show: [저자 또는 책 주인공 일러스트] + [책의 핵심 상징물이나 배경]
Style: Soft watercolor washes with fine pen lines. Warm, slightly vintage tone.

DO NOT include: photo-realistic imagery, dark background, excessive text, logos.
```

---

### 7. 영문 Summary+Video 썸네일 (Nano Banana용)

```
Create a YouTube thumbnail in 16:9 ratio (1920x1080px).

LAYOUT:
- White background with faint grid/notebook paper texture
- Blue geometric frame elements on left and right edges
  (circles, rectangles, infographic UI style, #1A73E8)
- Top 35%: Large bold English text, black, centered
- Bottom 60%: Illustrated scene

TEXT (top area):
"[Author Name]: [One-line hook — NOT the book title. Curiosity-driven rewrite.]"
Font: Bold sans-serif, very large, black, high contrast against white

ILLUSTRATED SCENE (bottom area):
Watercolor and pen-and-ink illustration style. NOT photorealistic.
Show: [Illustrated portrait of author or main character] + [symbolic background]
Style: Soft watercolor with fine pen details. Vintage, warm tone.

DO NOT include: photorealistic elements, dark backgrounds, excessive text, channel branding.
```

