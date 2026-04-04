#!/usr/bin/env python3
"""
GPU 서버 (192.168.0.151)에서 실행하는 Flux 이미지 생성 API 서버
포트: 9001

Usage (서버에서):
    ~/venv-gpu/bin/python scripts/flux_server.py

API:
    POST /generate
    {
        "prompt": "watercolor illustration of ...",
        "width": 1920,
        "height": 1080,
        "steps": 4,
        "seed": -1
    }
    → { "image_base64": "...", "seed": 12345 }

    GET /health
    → { "status": "ok", "model": "FLUX.1-schnell" }
"""

import base64
import io
import json
import random
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

PORT = 9001
MODEL_ID = "black-forest-labs/FLUX.1-schnell"

# 전역 파이프라인 (최초 1회 로드)
pipeline = None


def load_pipeline():
    global pipeline
    if pipeline is not None:
        return pipeline

    print(f"Loading {MODEL_ID}...", flush=True)
    start = time.time()

    try:
        import torch
        from diffusers import FluxPipeline

        pipeline = FluxPipeline.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.bfloat16,
        )
        pipeline.enable_model_cpu_offload()  # VRAM 절약
        # 두 번째 GPU도 활용 가능하면 사용
        # pipeline = pipeline.to("cuda")

        elapsed = time.time() - start
        print(f"✅ Model loaded in {elapsed:.1f}s", flush=True)
    except Exception as e:
        print(f"❌ Model load failed: {e}", file=sys.stderr, flush=True)
        sys.exit(1)

    return pipeline


def generate_image(
    prompt: str,
    width: int = 1920,
    height: int = 1080,
    steps: int = 4,
    seed: int = -1,
) -> tuple[str, int]:
    """이미지 생성 후 base64 반환"""
    import torch

    pipe = load_pipeline()

    if seed < 0:
        seed = random.randint(0, 2**32 - 1)

    generator = torch.Generator("cpu").manual_seed(seed)

    result = pipe(
        prompt=prompt,
        width=width,
        height=height,
        num_inference_steps=steps,
        generator=generator,
        guidance_scale=0.0,  # schnell은 0 권장
    )

    img = result.images[0]
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    img_b64 = base64.b64encode(buf.getvalue()).decode()

    return img_b64, seed


class FluxHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}", flush=True)

    def send_json(self, status: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self.send_json(200, {
                "status": "ok",
                "model": MODEL_ID,
                "loaded": pipeline is not None,
            })
        else:
            self.send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/generate":
            self.send_json(404, {"error": "not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        try:
            req = json.loads(body)
        except Exception:
            self.send_json(400, {"error": "invalid JSON"})
            return

        prompt = req.get("prompt", "")
        if not prompt:
            self.send_json(400, {"error": "prompt is required"})
            return

        width = int(req.get("width", 1920))
        height = int(req.get("height", 1080))
        steps = int(req.get("steps", 4))
        seed = int(req.get("seed", -1))

        print(f"Generating: {prompt[:80]}... ({width}x{height}, steps={steps})", flush=True)
        start = time.time()

        try:
            img_b64, used_seed = generate_image(prompt, width, height, steps, seed)
            elapsed = time.time() - start
            print(f"✅ Done in {elapsed:.1f}s, seed={used_seed}", flush=True)
            self.send_json(200, {
                "image_base64": img_b64,
                "seed": used_seed,
                "elapsed_s": round(elapsed, 2),
            })
        except Exception as e:
            print(f"❌ Generation failed: {e}", file=sys.stderr, flush=True)
            self.send_json(500, {"error": str(e)})


def main():
    print(f"🚀 Flux API Server starting on port {PORT}")
    print(f"Model: {MODEL_ID}")
    print("Pre-loading model...")
    load_pipeline()

    server = HTTPServer(("0.0.0.0", PORT), FluxHandler)
    print(f"✅ Listening on http://0.0.0.0:{PORT}")
    print("Endpoints: GET /health, POST /generate")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()
