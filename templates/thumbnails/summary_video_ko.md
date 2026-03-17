# 한글 Summary+Video 썸네일 프롬프트 템플릿

## 사용 방법

아래 프롬프트에서 플레이스홀더를 교체하여 이미지 생성 AI(DALL-E, Midjourney 등)에 사용하세요.

| 플레이스홀더 | 설명 | 예시 |
|------------|------|------|
| `{author_name}` | 저자 이름 | 빅터 프랭클 |
| `{hook_sentence}` | 책 제목이 아닌 핵심 메시지를 궁금증 유발 문장으로 | 고통 속에서도 의미를 찾을 수 있는가? |
| `{illustration_subject}` | 저자 또는 책 주인공 묘사 | 수용소에서 별을 바라보는 남성 |
| `{thematic_background}` | 책의 핵심 상징물이나 배경 | 철조망, 희미한 빛 한 줄기 |
| `{mood_color}` | 책 분위기에 맞는 배경 색감 | 짙은 회색~적갈색 그라데이션 |
| `{light_source}` | 드라마틱 조명 효과 | 희미한 빛 한 줄기가 위에서 내려오는 느낌 |

---

## 프롬프트 (복사하여 사용)

```
Create a YouTube thumbnail in 16:9 ratio (1920x1080px).

LAYOUT:
- Background: {mood_color}, {light_source}
- Blue geometric frame elements on left and right edges (circles and rectangles, similar to infographic UI style, #1A73E8)
- Top 35% of image: Large bold Korean text, white with drop shadow, centered, maximum contrast
- Bottom 60% of image: Illustrated scene

TEXT (top area):
"{author_name}: {hook_sentence}"
Font: Bold sans-serif, very large (approx 80-90pt), white with subtle drop shadow

ILLUSTRATED SCENE (bottom area):
Watercolor and pen-and-ink illustration style, NOT photorealistic.
Show: {illustration_subject} + {thematic_background}
Style: Soft watercolor washes with fine pen lines. Dramatic lighting from the background.
Composition: Subject centered or slightly left, background tells the story of the book.

COLOR PALETTE: Dark atmospheric background. Illustration has natural watercolor colors highlighted by dramatic lighting. Blue geometric frame accents (#1A73E8).

DO NOT include: photo-realistic imagery, plain white background, excessive text, logos, channel name.
```

---

## 체크리스트

업로드 전 아래 6가지를 모두 확인하세요:

- [ ] 텍스트가 책 제목이 아닌 "훅 카피"인가?
- [ ] 일러스트 스타일인가? (사진 X)
- [ ] 어두운 배경 + 드라마틱 조명인가?
- [ ] 텍스트가 상단에 크고 굵게 (화이트) 있는가?
- [ ] 인물 or 동물이 포함되어 있는가?
- [ ] 전체적으로 복잡하지 않은가? (요소 3개 이하)

---

## 배경 색감 가이드

| 책 분위기 | 추천 배경 | 추천 조명 |
|----------|----------|----------|
| 철학/사색 | 진한 남색~검정 그라데이션 | 촛불 또는 달빛 |
| 전쟁/비극 | 짙은 회색~적갈색 그라데이션 | 불꽃 또는 석양빛 |
| 사랑/감성 | 깊은 보라~남색 그라데이션 | 따뜻한 황금빛 |
| 모험/역사 | 짙은 갈색~카키 그라데이션 | 횃불 또는 새벽빛 |
| 공포/미스터리 | 검정~짙은 녹색 그라데이션 | 희미한 단일 광원 |
| 유머/풍자 | 진한 티얼~네이비 그라데이션 | 무대 스포트라이트 |
| 자기계발 | 짙은 네이비~인디고 그라데이션 | 새벽빛 또는 스포트라이트 |

---

## 예시

**나쁜 예**: `나는 고양이로소이다 — 나쓰메 소세키`

**좋은 예**: `나쓰메 소세키: 근대를 비판한 고양이`
