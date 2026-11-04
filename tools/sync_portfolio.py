#!/usr/bin/env python3
"""
Copy each project's media from "<project folder>/include/" into the site.

  python3 site/tools/sync_portfolio.py            # every project
  python3 site/tools/sync_portfolio.py clix       # one project (by slug)

Rules
- Only files inside a project's include/ folder end up on the site.
- A file with "cover" in its name becomes cover.<ext>: the home-page card
  and the first (hero) image on the project page. It can be an image or video.
- Photos are converted to JPEG (longest side 2400px), .mov/.mp4 to 1080p mp4,
  GIFs are copied as-is.
- Media is used exactly as it is in include/ (no trimming). tools/trim.py can
  cut stray edge lines and big empty margins if TRIM is set to True.
- assets/img/<slug>/ is rebuilt so it holds exactly what include/ holds.
- The `images` layout in assets/projects.js is kept where files still exist;
  new files are added at the end as full-width images, removed ones dropped.

Each project in projects.js links to its folder with  folder: "Clix",
Needs python3 with pillow, numpy and imageio-ffmpeg:
  python3 -m pip install --user pillow numpy imageio-ffmpeg
"""
import json, os, re, shutil, subprocess, sys, time

import numpy as np
from PIL import Image, ImageOps
import imageio_ffmpeg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trim import find_box, extend

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.dirname(SITE)  # "portfolio images"
PROJECTS_JS = os.path.join(SITE, "assets", "projects.js")
IMG_DIR = os.path.join(SITE, "assets", "img")

PHOTO = (".jpg", ".jpeg", ".png", ".heic", ".tif", ".tiff", ".webp")
VIDEO = (".mov", ".mp4", ".m4v")
GIF = (".gif",)
MAX_EDGE = 2400
CARD_AR = 4 / 3   # home-page cards; keep in step with .card__media in style.css
# auto-trim (tools/trim.py) is off: Winnie wants images exactly as in include/.
# set TRIM = True to cut stray edge lines and big empty margins again.
TRIM = False


def slugify(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "file"


def out_name(src):
    stem, ext = os.path.splitext(os.path.basename(src))
    ext = ext.lower()
    base = "cover" if "cover" in stem.lower() else slugify(stem)
    if ext in PHOTO:
        return base + ".jpg"
    if ext in VIDEO:
        return base + ".mp4"
    return base + ext


def stamp(src, shave=0):
    st = os.stat(src)
    return f"{os.path.basename(src)}|{st.st_size}|{int(st.st_mtime)}|trim={TRIM}|shave={shave}"


def trim_photo(path, shave=0):
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    if shave:
        # cut the same share off every side, so the picture keeps its shape
        dx, dy = round(im.width * shave), round(im.height * shave)
        im = im.crop((dx, dy, im.width - dx, im.height - dy))
    small = im.copy()
    small.thumbnail((800, 800))
    box = find_box([np.asarray(small.convert("L"))]) if TRIM else None
    if box:
        k = im.width / small.width
        im = im.crop(tuple(int(round(v * k)) for v in box))
    im.save(path, "JPEG", quality=82, optimize=True)


def make_card(dst_dir, cover):
    """card.jpg: the cover grown to the card's 4:3 shape by continuing its own
    background (mirrored), so the card never crops the work. None if it already fits."""
    card = os.path.join(dst_dir, "card.jpg")
    if os.path.exists(card):
        os.remove(card)
    if not cover or not cover.endswith(".jpg"):
        return None
    im = np.asarray(Image.open(os.path.join(dst_dir, cover)).convert("RGB"))
    h, w, _ = im.shape
    if abs(w / h - CARD_AR) < 0.01:
        return None
    if w / h > CARD_AR:
        extra = round(w / CARD_AR) - h
        im = extend(im, top=extra // 2, bottom=extra - extra // 2, mode="mirror")
    else:
        extra = round(h * CARD_AR) - w
        im = extend(im, left=extra // 2, right=extra - extra // 2, mode="mirror")
    Image.fromarray(im).save(card, "JPEG", quality=82, optimize=True)
    return "card.jpg"


def video_frames(src, n=8):
    """n evenly spaced greyscale frames, 640px wide, plus the video's size."""
    info = subprocess.run([FFMPEG, "-hide_banner", "-i", src], capture_output=True, text=True).stderr
    w, h = map(int, re.search(r"Video:.*?(\d{2,5})x(\d{2,5})", info).groups())
    hh, mm, ss = re.search(r"Duration: (\d+):(\d+):([\d.]+)", info).groups()
    dur = int(hh) * 3600 + int(mm) * 60 + float(ss)
    sw, sh = 640, int(round(640 * h / w))
    frames = []
    for i in range(n):
        raw = subprocess.run([FFMPEG, "-loglevel", "error", "-ss", f"{dur * (i + 0.5) / n:.2f}", "-i", src,
                              "-frames:v", "1", "-vf", f"scale={sw}:{sh},format=gray", "-f", "rawvideo", "-"],
                             capture_output=True).stdout
        if len(raw) == sw * sh:
            frames.append(np.frombuffer(raw, np.uint8).reshape(sh, sw))
    return frames, w, h


def convert(src, dst, shave=0):
    ext = os.path.splitext(src)[1].lower()
    if ext in PHOTO:
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "90",
                        "-Z", str(MAX_EDGE), src, "--out", dst],
                       check=True, stdout=subprocess.DEVNULL)
        trim_photo(dst, shave)
    elif ext in VIDEO:
        frames, w, h = video_frames(src) if TRIM else ([], 0, 0)
        box = find_box(frames) if frames else None
        vf = []
        if box:
            k = w / frames[0].shape[1]
            l, t, r, b = (int(v * k) // 2 * 2 for v in box)
            vf.append(f"crop={r - l}:{b - t}:{l}:{t}")
        vf.append("scale='min(1920,iw)':-2")
        subprocess.run([FFMPEG, "-loglevel", "error", "-y", "-i", src, "-vf", ",".join(vf),
                        "-c:v", "libx264", "-crf", "24", "-preset", "medium", "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", "-an", dst], check=True)
    else:
        shutil.copy2(src, dst)


def sync_media(slug, folder, shaves=None):
    shaves = shaves or {}
    inc = os.path.join(BASE, folder, "include")
    if not os.path.isdir(inc):
        print(f"  ! {inc} not found, skipped")
        return None
    srcs = sorted(f for f in os.listdir(inc)
                  if not f.startswith(".") and f.lower().endswith(PHOTO + VIDEO + GIF))
    dst_dir = os.path.join(IMG_DIR, slug)
    os.makedirs(dst_dir, exist_ok=True)
    # .sources.json remembers which include/ file each output came from,
    # so unchanged files (videos especially) are not converted again
    record = os.path.join(dst_dir, ".sources.json")
    try:
        done = json.load(open(record))
    except (OSError, ValueError):
        done = {}
    made = []
    for f in srcs:
        src, name = os.path.join(inc, f), out_name(f)
        if name in made:
            print(f"  ! two files map to {name}; skipped {f}")
            continue
        dst = os.path.join(dst_dir, name)
        shave = shaves.get(name, 0)
        if not (os.path.exists(dst) and done.get(name) == stamp(src, shave)):
            print(f"  {f} -> {name}")
            convert(src, dst, shave)
            done[name] = stamp(src, shave)
        made.append(name)
    json.dump({k: v for k, v in done.items() if k in made}, open(record, "w"), indent=1)
    for f in os.listdir(dst_dir):
        if f not in made and f not in (".sources.json", "card.jpg"):
            os.remove(os.path.join(dst_dir, f))
    covers = [m for m in made if m.startswith("cover.")]
    if not covers:
        print(f"  ! no file with 'cover' in its name in {folder}/include")
    cover = covers[0] if covers else None
    return made, cover, make_card(dst_dir, cover)


def merge_layout(layout, made, cover):
    have, seen, out = set(made), set(), []
    for item in layout:
        row = item if isinstance(item, list) else [item]
        row = [f for f in row if f in have and f != cover and f not in seen]
        seen.update(row)
        if len(row) == 1:
            out.append(row[0])
        elif row:
            out.append(row)
    out += [f for f in made if f not in seen and f != cover]
    return ([cover] if cover else []) + out


def main():
    only = set(sys.argv[1:])
    js = open(PROJECTS_JS, encoding="utf-8").read()

    def fix(block):
        b = block.group(0)
        slug = re.search(r'slug: "([^"]+)"', b).group(1)
        folder = re.search(r'folder: "([^"]+)"', b)
        if not folder or (only and slug not in only):
            return b
        print(slug)
        # shave: { "file.jpg": 0.02 } cuts 2% off every side of that picture
        m = re.search(r"shave: (\{.*?\}),\n", b, re.S)
        res = sync_media(slug, folder.group(1), json.loads(m.group(1)) if m else None)
        if not res:
            return b
        made, cover, card = res
        layout = json.loads(re.search(r"images: (\[.*?\]),\n", b, re.S).group(1))
        images = json.dumps(merge_layout(layout, made, cover), ensure_ascii=False).replace('","', '", "')
        b = re.sub(r"images: \[.*?\],\n", lambda _: f"images: {images},\n", b, flags=re.S)
        b = re.sub(r'    card: "[^"]*",\n', "", b)
        if card:
            b = b.replace("    images:", f'    card: "{card}",\n    images:', 1)
        if cover:
            b = re.sub(r'cover: "[^"]*"', f'cover: "{cover}"', b) if "cover:" in b else \
                b.replace("    images:", f'    cover: "{cover}",\n    images:', 1)
        return b

    js = re.sub(r"\n  \{\n.*?\n  \},", fix, js, flags=re.S)
    # a new version makes browsers fetch changed media instead of cached copies
    stamp_line = f'window.MEDIA_VERSION = "{int(time.time())}";'
    js = re.sub(r'window\.MEDIA_VERSION = "[^"]*";', stamp_line, js) if "MEDIA_VERSION" in js \
        else js.rstrip() + "\n" + stamp_line + "\n"
    open(PROJECTS_JS, "w", encoding="utf-8").write(js)


if __name__ == "__main__":
    main()
