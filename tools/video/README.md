# Film and graphics (tools/video)

The demo film, README infographics and logo renders are produced by code, so they stay in sync with the real demo numbers.

```bash
pip install -r requirements-video.txt            # skia-python, numpy, Pillow
sudo apt install fonts-inter fonts-jetbrains-mono ffmpeg
python tools/video/render.py still 15.2 out.png   # one frame (seconds)
python tools/video/render.py video guard-demo.mp4 # the 46 s film, 1600x1200 @ 60 fps (about 3 min)
python tools/video/stills.py                      # infographics -> docs/images
```
`numbers.json` is a snapshot of one real demo run (file counts, rejected rows, daily spend). Regenerate it from the database if you want the film to show your own numbers.
