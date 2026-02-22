# 한글 Summary+Video 썸네일 프롬프트 템플릿

## 사용 방법

아래 프롬프트에서 플레이스홀더를 교체하여 이미지 생성 AI(DALL-E, Midjourney 등)에 사용하세요.

| 플레이스홀더 | 설명 | 예시 |
|------------|------|------|
| `{author_name}` | 저자 이름 | 빅터 프랭클 |
| `{hook_sentence}` | 책 제목이 아닌 핵심 메시지를 궁금증 유발 문장으로 | 고통 속에서도 의미를 찾을 수 있는가? |
| `{illustration_subject}` | 저자 또는 책 주인공 묘사 | 수용소에서 별을 바라보는 남성 |
| `{thematic_background}` | 책의 핵심 상징물이나 배경 | 철조망, 희미한 빛 한 줄기 |

---

## 프롬프트 (복사하여 사용)

```
Create a YouTube thumbnail in 16:9 ratio (1920x1080px).

LAYOUT:
- White background with faint grid/notebook paper texture
- Blue geometric frame elements on left and right edges (circles and rectangles, similar to infographic UI style)
- Top 35% of image: Large bold Korean text, black, centered, maximum contrast
- Bottom 60% of image: Illustrated scene

TEXT (top area):
"{author_name}: {hook_sentence}"
Font: Bold sans-serif, very large (approx 80-90pt), black

ILLUSTRATED SCENE (bottom area):
Watercolor and pen-and-ink illustration style, NOT photorealistic.
Show: {illustration_subject} + {thematic_background}
Style: Soft watercolor washes with fine pen lines. Warm, slightly vintage tone.
Composition: Subject centered or slightly left, background tells the story of the book.

COLOR PALETTE: Mostly white/cream background. Illustration has natural watercolor colors (warm browns, soft blues, muted greens). Blue geometric frame accents (#1A73E8 or similar).

DO NOT include: photo-realistic imagery, dark/moody background, excessive text, logos, channel name.
```

---

## 체크리스트

업로드 전 아래 6가지를 모두 확인하세요:

- [ ] 텍스트가 책 제목이 아닌 "훅 카피"인가?
- [ ] 일러스트 스타일인가? (사진 X)
- [ ] 흰 배경 + 파란 프레임인가?
- [ ] 텍스트가 상단에 크고 굵게 있는가?
- [ ] 인물 or 동물이 포함되어 있는가?
- [ ] 전체적으로 복잡하지 않은가? (요소 3개 이하)

---

## 예시

**나쁜 예**: `나는 고양이로소이다 — 나쓰메 소세키`

**좋은 예**: `나쓰메 소세키: 근대를 비판한 고양이`
