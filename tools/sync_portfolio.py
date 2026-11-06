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
  GIFs become looping mp4s.
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
from trim import find_box, extend, tip_apex, complete_tip, continue_dark

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
    if ext in VIDEO or ext in GIF:
        return base + ".mp4"   # GIFs become looping videos: a fraction of the size
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


def card_fill(edge):
    """How to grow a card: dark and plain → continue it; dark with the work running off
    the edge → plain colour (a mirror would duplicate the work); walls, greys → mirror."""
    if np.median(edge) >= 40:
        return "mirror"
    return "stretch" if edge.std((0, 1)).max() < 12 else "solid"


def make_card(dst_dir, cover, tips=None):
    """card.jpg: the cover grown to the card's 4:3 shape by continuing its own
    background (mirrored), so the card never crops the work. None if it already fits.
    tips: objects the photo itself cuts off at the bottom, as [edge a, edge b] pairs in
    cover.jpg pixels; they get finished, and the whole picture is centred on the card."""
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
        band = max(4, h // 30)
        edge = np.concatenate([im[:band], im[-band:]])
        top, bottom = extra // 2, extra - extra // 2
        mode = card_fill(edge)
        if mode == "solid":
            # the work runs off one edge only: leave it touching the card there,
            # and add all the background on the plain side
            calm_top, calm_bottom = (im[:band].std((0, 1)).max() < 12, im[-band:].std((0, 1)).max() < 12)
            if calm_top != calm_bottom:
                top, bottom = (extra, 0) if calm_top else (0, extra)
        if tips:
            reach = min(extra, max(round(tip_apex(a, b)[1]) - h for a, b in tips))
            top = (extra - reach) // 2
            bottom = extra - top
        im = extend(im, top=top, bottom=bottom, mode=mode)
        if tips:
            im = continue_dark(continue_dark(im, top, "top"), top + h, "bottom")
        for a, b in tips or []:
            shift = lambda line: [[x, y + top] for x, y in line]
            im = complete_tip(im.astype(np.float32), h + top, shift(a), shift(b))
        im = np.clip(im, 0, 255).astype(np.uint8)
    else:
        extra = round(h * CARD_AR) - w
        band = max(4, w // 30)
        edge = np.concatenate([im[:, :band], im[:, -band:]], 1)
        im = extend(im, left=extra // 2, right=extra - extra // 2, mode=card_fill(edge))
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
    elif ext in GIF:
        subprocess.run([FFMPEG, "-loglevel", "error", "-y", "-i", src, "-vf",
                        "scale='min(1920,iw)':-2:flags=lanczos,format=yuv420p",
                        "-c:v", "libx264", "-crf", "28", "-preset", "slow", "-tune", "stillimage",
                        "-movflags", "+faststart", "-an", dst], check=True)
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


def sync_media(slug, folder, shaves=None, card_from=None, tips=None):
    shaves = shaves or {}
    root = os.path.join(BASE, os.path.expanduser(folder))
    inc = os.path.join(root, "include")
    if not os.path.isdir(inc):
        inc = os.path.join(root, "included")
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
    # a still frame for each video, shown until it plays (iPhone Low Power Mode never autoplays)
    posters = []
    for name in made:
        if name.endswith(".mp4"):
            still = name[:-4] + ".poster.jpg"
            dst = os.path.join(dst_dir, name)
            out = os.path.join(dst_dir, still)
            if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(dst):
                subprocess.run([FFMPEG, "-loglevel", "error", "-y", "-ss", "0.3", "-i", dst, "-frames:v", "1",
                                "-q:v", "4", out], check=True)
            posters.append(still)
    for f in os.listdir(dst_dir):
        if f not in made and f not in posters and f not in (".sources.json", "card.jpg"):
            os.remove(os.path.join(dst_dir, f))
    covers = [m for m in made if m.startswith("cover.")]
    if not covers:
        print(f"  ! no file with 'cover' in its name in {folder}/include")
    cover = covers[0] if covers else None
    # no "cover" file: the cover: named in projects.js is used for the card only
    # card_tips belongs to one photo: ignore it once that cover file is replaced
    tip_list = None
    if tips and cover and tips["source"] == done.get(cover, "").split("|")[0]:
        tip_list = tips["tips"]
    return made, cover, make_card(dst_dir, cover or (card_from if card_from in made else None), tip_list)


def flat_runs(a):
    """[start, end) runs of rows identical to the row above: empty stretches of a flat graphic."""
    same = np.abs(a[1:].astype(np.int16) - a[:-1]).max((1, 2)) < 6
    idx = np.flatnonzero(same) + 1
    if not len(idx):
        return []
    runs = np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1)
    return [(r[0], r[-1] + 1) for r in runs if len(r) >= a.shape[0] * 0.02]


def grow_flat(a, new_h, runs):
    """Make a flat graphic taller by repeating rows in its empty stretches only."""
    extra, total = new_h - a.shape[0], sum(e - s for s, e in runs)
    counts = np.ones(a.shape[0], int)
    left = extra
    for i, (s, e) in enumerate(runs):
        n = left if i == len(runs) - 1 else round(extra * (e - s) / total)
        counts[(s + e) // 2] += n
        left -= n
    return np.repeat(a, counts, 0)


def widen(a, extra):
    """Continue a photo's background sideways, on the plain side if only one side is plain:
    a hand or arm running off the other edge stays at the frame instead of being smeared."""
    band = max(4, a.shape[1] // 100)
    calm_l, calm_r = (a[:, :band].std((0, 1)).max() < 12, a[:, -band:].std((0, 1)).max() < 12)
    left = extra // 2
    if calm_l != calm_r:
        left = extra if calm_l else 0
    return extend(a, left=left, right=extra - left)


def fit_rows(slug, layout):
    """Things side by side must share one shape. A flat graphic grows taller through its
    empty stretches, which leaves the photo beside it untouched. Otherwise a narrower photo
    gets its own background continued sideways until it matches the widest in its row."""
    dst_dir = os.path.join(IMG_DIR, slug)
    for row in layout:
        if not isinstance(row, list) or not all(f.endswith(".jpg") for f in row):
            continue
        ims = {f: np.asarray(Image.open(os.path.join(dst_dir, f)).convert("RGB")) for f in row}
        ratio = {f: a.shape[1] / a.shape[0] for f, a in ims.items()}
        runs = {f: flat_runs(a) for f, a in ims.items()}
        flat = {f for f, a in ims.items() if sum(e - s for s, e in runs[f]) >= a.shape[0] * 0.3}
        photos = [f for f in row if f not in flat] or row
        target = max(ratio[f] for f in photos)
        for f, a in ims.items():
            h, w, _ = a.shape
            if f in flat and f not in photos and ratio[f] > target and round(w / target) - h >= 2:
                a, how = grow_flat(a, round(w / target), runs[f]), "made taller"
            elif round(h * target) - w >= 2:
                a, how = widen(a, round(h * target) - w), "background extended"
            else:
                continue
            Image.fromarray(a).save(os.path.join(dst_dir, f), "JPEG", quality=88, optimize=True)
            print(f"  {f}: {how} to fit its row")


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
        named = re.search(r'cover: "([^"]+)"', b)
        t = re.search(r"card_tips: (\{.*?\}),\n", b, re.S)
        res = sync_media(slug, folder.group(1), json.loads(m.group(1)) if m else None,
                         named.group(1) if named else None, json.loads(t.group(1)) if t else None)
        if not res:
            return b
        made, cover, card = res
        layout = json.loads(re.search(r"images: (\[.*?\]),\n", b, re.S).group(1))
        # keep_order: the cover is still the card, but the page keeps its own opening
        keep = "keep_order: true" in b
        merged = merge_layout(layout, made, None if keep else cover)
        fit_rows(slug, merged)
        images = json.dumps(merged, ensure_ascii=False).replace('","', '", "')
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
