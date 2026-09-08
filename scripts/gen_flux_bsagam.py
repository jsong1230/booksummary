#!/usr/bin/env python3
"""「B사감과 러브레터」 Flux 무드 이미지 배치 생성

글자 차단은 부정 프롬프트가 아니라 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 펼친 편지지·책·칠판·간판·현판·족자를 장면에서 아예 뺀다.
   이 작품의 핵심 소재가 '편지'이지만 편지 컷은 스톡이 이미 커버하므로
   Flux는 인물·공간·소품에만 쓴다.
"""
import base64
import json
import sys
import time
import urllib.request
from pathlib import Path

# 9002 는 파이프라인이 cpu/cuda 로 쪼개져 500 을 낸다(2026-09-06 실측) → 9010 사용.
# 포트는 매번 /health 의 model·loaded 필드로 확인할 것 ([[feedback_thumbnail_gpu151]])
FLUX = "http://192.168.0.150:9010/generate"
OUT = Path("assets/images/Miss_B_and_the_Love_Letters")

BASE = ("cinematic film still, 1920s Korea, muted desaturated palette, "
        "soft warm oil-lamp light, deep shadows, 35mm film grain, "
        "shallow depth of field, quiet somber mood")

SCENES = [
    # 인물 — 사감
    "a stern Korean woman in her late thirties wearing a dark hanbok jacket, round wire glasses, tight lips, standing alone in a dim wooden room",
    "close-up profile of a severe Korean woman with round glasses, lamplight on one side of her face, darkness behind",
    "a middle-aged Korean woman in hanbok sitting alone on a wooden floor, arms opened toward empty air, dim room",
    "a Korean woman kneeling on a bare wooden floor with clasped hands, head bowed, single lamp behind her",
    "back view of a middle-aged Korean woman in white hanbok standing at a paper-screen window at night",
    "a lone woman's silhouette against a paper window glowing with moonlight",
    "an older Korean woman's weathered hands resting on her lap, lamplight, dark background",
    "close-up of a woman's tired eyes behind round wire glasses, dim warm light",
    # 인물 — 여학생
    "three young Korean schoolgirls in white jeogori and black skirts tiptoeing down a dark wooden corridor at night, seen from behind",
    "a frightened young Korean schoolgirl in white jeogori sitting stiffly on a wooden chair, lamplight, dark room",
    "young Korean schoolgirls sleeping side by side on quilts on a wooden dormitory floor, dim blue night light",
    "two Korean schoolgirls whispering in the dark, only their faces lit by a small lamp",
    "a young Korean schoolgirl's face peeking through a narrow gap in a sliding wooden door, warm light on her cheek",
    "back view of a young Korean schoolgirl in braided hair standing alone in an empty wooden corridor",
    "a group of Korean schoolgirls in white jeogori walking across a school courtyard at dusk",
    "a young woman's hand pushing open a sliding wooden door a crack, warm light spilling out",
    # 공간
    "long dark wooden corridor of a 1920s Korean school dormitory at night, a single oil lamp far away",
    "empty Korean dormitory room with folded quilts stacked against the wall, wooden floor, dim morning light",
    "a small spartan room with a wooden desk and a single chair, oil lamp burning, night",
    "1920s Korean classroom with rows of low wooden desks, empty, pale light through windows",
    "exterior of a 1920s Korean mission school brick building at night, few windows lit",
    "a walled school courtyard at dawn, bare trees, frost on the ground",
    "moonlight falling across a traditional Korean paper-screen sliding door",
    "narrow wooden staircase in an old Korean building, darkness above",
    "view from a dark corridor toward a door with warm light leaking through the gap at its base",
    "tiled Korean roof against a deep blue night sky, a single lit window below",
    "a bare dormitory room at night, moonlight across an empty quilt on the floor",
    "the corner of a wooden veranda at night, one lamp, long shadows",
    # 소품·상징
    "an old brass oil lamp burning on a bare wooden desk, darkness around it",
    "a single pair of round wire eyeglasses lying folded on a dark wooden desk, lamplight",
    "one candle flame in a completely dark room, warm glow",
    "a pair of white rubber shoes left neatly on a wooden veranda step at night",
    "an iron door handle on an old wooden door, dim light",
    "a bare winter branch seen through a paper-screen window",
    "an empty wooden chair beside a burning oil lamp, dark room",
    "a stone well in a dark courtyard at night, faint moonlight",
    "a small wooden mailbox mounted on a stone wall, dusk",
    "a dried pressed flower resting on a dark wooden surface, single shaft of light",
    "a woman's shadow cast large across a papered wall by lamplight",
    "an unlit corridor with one shaft of moonlight crossing the wooden floor",
]


def generate(prompt: str, seed: int) -> bytes | None:
    body = json.dumps({
        "prompt": prompt, "width": 1920, "height": 1080, "steps": 4, "seed": seed
    }).encode()
    req = urllib.request.Request(FLUX, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return base64.b64decode(json.loads(r.read())["image_base64"])
    except Exception as e:
        print(f"   ❌ {e}")
        return None


def main() -> None:
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    OUT.mkdir(parents=True, exist_ok=True)
    made = 0
    t0 = time.time()
    for i, scene in enumerate(SCENES, 1):
        prompt = f"{BASE}, {scene}"
        for k in range(per):
            seed = i * 1000 + k * 7
            img = generate(prompt, seed)
            if not img:
                continue
            path = OUT / f"flux_{i:02d}_{k+1}.jpg"
            path.write_bytes(img)
            made += 1
            print(f"[{made}] {path.name}  ({time.time()-t0:.0f}s)  {scene[:50]}")
    print(f"\n✅ {made}장 생성 / {time.time()-t0:.0f}초")


if __name__ == "__main__":
    main()
