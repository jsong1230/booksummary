# Beyond Page — Claude Code Prompt & 썸네일 공식 가이드

---

## PART 1: Claude Code 프롬프트

### 📋 Summary+Video 영상 생성 프롬프트

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

### 📋 일당백 스타일 영상 생성 프롬프트

```
[저자명-책제목] 일당백 스타일 한글 영문 영상 생성해줘.

input 폴더에서 파일을 아래 역할 기준으로 자동 인식해줘:
- PNG 중 썸네일 2개 (한글/영문 구분)
- PNG 중 인포그래픽 4개 (한글 1·2, 영문 1·2 구분)
- MP4 4개 → NotebookLM 동영상
  (한글 part1, 한글 part2, 영문 part1, 영문 part2 구분)
언어·파트 구분이 불명확하면 파일명의 ko/en, part1/part2,
1dang/infographic 등 키워드로 판단.
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

### 📋 배치 처리 프롬프트 (큐 기반, 추후 자동화용)

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

## PART 2: 2위 썸네일 공식 분석 및 복제 가이드

### 🔍 "나는 고양이로소이다" 썸네일 해부 (CTR 4.3%)

**시각적 구성요소:**

| 요소 | 상세 |
|------|------|
| 배경 | 흰색 + 연한 격자 패턴 (노트 용지 느낌) |
| 테두리 | 파란색 기하학 도형 (원, 사각형) — 인포그래픽 프레임 |
| 메인 이미지 | 수채화/펜화 스타일 일러스트 (인물 + 고양이 + 배경) |
| 텍스트 위치 | 상단 1/3, 센터 정렬 |
| 텍스트 스타일 | 굵은 블랙 한글, 배경 대비 최대 |
| 텍스트 내용 | **저자명: [책의 핵심 메시지를 한 문장으로]** |
| 색감 | 전체적으로 밝고 깔끔, 이미지만 컬러 포인트 |

**CTR이 높은 결정적 이유:**

1. **제목 카피가 훅으로 작동** — "근대를 비판한 고양이"는 궁금증을 유발하는 문장형 카피. 단순히 책 제목을 넣는 것보다 훨씬 강력함.

2. **일러스트 스타일의 차별성** — 사진 기반 채널이 많은 북튜브에서 수채화 일러스트가 시각적으로 튀어 보임.

3. **인물 + 동물 조합** — 인간의 얼굴 + 동물은 클릭율을 높이는 검증된 조합.

4. **정보량이 적당함** — 텍스트 1줄(또는 2줄), 이미지 1개. 복잡하지 않음.

---

### ✍️ Nano Banana 썸네일 프롬프트 개선안

#### Summary+Video용 (Gems가 생성하는 프롬프트 대체)

현재 방식 대신, Gems가 아래 형식으로 프롬프트를 출력하도록 수정:

**[한글 Summary+Video 썸네일 프롬프트 템플릿]**

```
Create a YouTube thumbnail in 16:9 ratio (1920x1080px).

LAYOUT:
- White background with faint grid/notebook paper texture
- Blue geometric frame elements on left and right edges (circles and rectangles, similar to infographic UI style)
- Top 35% of image: Large bold Korean text, black, centered, maximum contrast
- Bottom 60% of image: Illustrated scene

TEXT (top area):
"[저자명]: [책의 핵심 메시지를 궁금증을 유발하는 한 문장으로]"
Font: Bold sans-serif, very large (approx 80-90pt), black

ILLUSTRATED SCENE (bottom area):
Watercolor and pen-and-ink illustration style, NOT photorealistic.
Show: [저자 또는 책 주인공의 일러스트 인물] + [책의 핵심 상징물이나 배경]
Style: Soft watercolor washes with fine pen lines. Warm, slightly vintage tone.
Composition: Subject centered or slightly left, background tells the story of the book.

COLOR PALETTE: Mostly white/cream background. Illustration has natural watercolor colors (warm browns, soft blues, muted greens). Blue geometric frame accents (#1A73E8 or similar).

DO NOT include: photo-realistic imagery, dark/moody background, excessive text, logos, channel name.
```

---

**[영문 Summary+Video 썸네일 프롬프트 템플릿]**

```
Create a YouTube thumbnail in 16:9 ratio (1920x1080px).

LAYOUT:
- White background with faint grid/notebook paper texture
- Blue geometric frame elements on left and right edges (circles, rectangles - infographic UI style)
- Top 35%: Large bold English text, black, centered
- Bottom 60%: Illustrated scene

TEXT (top area):
"[Author Name]: [One-line hook about the book's core message]"
Font: Bold sans-serif, very large, black, high contrast against white

ILLUSTRATED SCENE (bottom area):
Watercolor and pen-and-ink illustration style.
Show: [Illustrated portrait of author or main character] + [symbolic background related to book's theme]
Style: Soft watercolor with fine pen details. Vintage, slightly warm tone. NOT photorealistic.

COLOR: Mostly white/cream. Watercolor natural tones. Blue geometric frame (#1A73E8).

DO NOT include: photorealistic elements, dark backgrounds, excessive text, channel branding.
```

---

#### 일당백 스타일용 (직접 입력하던 프롬프트 개선)

기존: `"작가-제목 롱폼용 한글 혹은 영문 썸네일 생성해줘"` (너무 단순)

개선 프롬프트:

**한글 일당백 썸네일:**
```
[저자명]-[책제목] 일당백 스타일 한글 썸네일 만들어줘.

형식:
- 16:9, 1920x1080
- 배경: 흰색 + 격자 패턴
- 파란색 인포그래픽 테두리 프레임
- 상단 텍스트: "[저자명]: [이 책의 핵심 메시지를 호기심 유발 문장으로]" — 굵은 블랙 한글, 크게
- 하단 일러스트: [저자 or 책 캐릭터]의 수채화+펜화 스타일 일러스트. 배경에 책의 세계관 반영.
- 전체 느낌: 깔끔하고 밝음. 일러스트가 포인트. 사진 X.
```

**영문 일당백 썸네일:**
```
[Author]-[Title] 1DANG100 style English thumbnail.

Format: 16:9, 1920x1080
Background: White with faint grid texture
Frame: Blue geometric infographic-style border (circles + rectangles on edges)
Top text: "[Author]: [Hook sentence about book's core theme]" — Bold black, very large
Bottom illustration: Watercolor + pen-and-ink style portrait of [author/character] with thematic background
Overall feel: Clean, bright, illustration as focal point. No photos.
```

---

### 📏 Gems 프롬프트 수정 권장사항

현재 Gems가 생성하는 썸네일 프롬프트에서 **아래 3가지를 반드시 추가**하도록 Gems 지시문을 수정:

1. **텍스트를 책 제목 그대로 넣지 말 것** → 책의 핵심 메시지를 "궁금증 유발 문장"으로 변환해서 넣도록
   - ❌ "나는 고양이로소이다 — 나쓰메 소세키"
   - ✅ "나쓰메 소세키: 근대를 비판한 고양이"

2. **반드시 수채화+펜화 스타일(일러스트) 지정** → 사진 리얼리즘 제외

3. **파란색 기하학 인포그래픽 프레임** → 채널의 시각적 아이덴티티 유지

---

### ⚡ 빠른 실행 체크리스트

새 영상 업로드 전 썸네일 확인:
- [ ] 텍스트가 책 제목이 아닌 "훅 카피"인가?
- [ ] 일러스트 스타일인가? (사진 X)
- [ ] 흰 배경 + 파란 프레임인가?
- [ ] 텍스트가 상단에 크고 굵게 있는가?
- [ ] 인물 or 동물이 포함되어 있는가?
- [ ] 전체적으로 복잡하지 않은가? (요소 3개 이하)

이 체크리스트 6개를 모두 통과하면 CTR 4%+ 가능성 높음.
