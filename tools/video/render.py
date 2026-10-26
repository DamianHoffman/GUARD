#!/usr/bin/env python3
"""Render the GUARD demo film or single stills.

  python tools/video/render.py still 15.5 out.png        # one frame at T seconds
  python tools/video/render.py video guard-demo.mp4      # full 60 fps film (needs ffmpeg)
  python tools/video/render.py video part1.mp4 0 12      # only seconds 0-12 (join parts with ffmpeg -f concat)
Requirements: pip install skia-python numpy ; fonts Inter + JetBrains Mono (apt: fonts-inter fonts-jetbrains-mono).
"""
import subprocess
import sys
import time

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from engine import FPS, H, W, frame_bytes, new_surface, save_png  # noqa: E402
from story import DURATION, render  # noqa: E402


def still(T, out):
    s, c = new_surface()
    render(c, T)
    save_png(s, out)


def video(out, fps=FPS, crf=19, t0=0.0, t1=None):
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    s, c = new_surface()
    first, last = int(t0 * fps), int((t1 if t1 else DURATION) * fps)
    started = time.time()
    for i in range(first, last):
        render(c, i / fps)
        p.stdin.write(frame_bytes(s))
        if (i - first) % 300 == 0:
            print(f"frame {i}/{last}  {time.time() - started:.0f}s", flush=True)
    p.stdin.close()
    p.wait()


if __name__ == "__main__":
    if sys.argv[1] == "still":
        still(float(sys.argv[2]), sys.argv[3])
    else:
        a = sys.argv[3:5]
        video(sys.argv[2], t0=float(a[0]) if a else 0.0, t1=float(a[1]) if len(a) > 1 else None)
