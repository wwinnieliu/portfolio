"""
Find how much of a photo/video frame's edges can be cut away:
- thin stray lines and white specks along the edges (left over from mockup
  exports or screenshots) are always removed;
- large empty margins (plain black, white or grey background) are cut down
  to a small even margin around the subject.

find_box(frames) returns (left, top, right, bottom) in pixels of the frames,
or None when nothing should change.
"""
import numpy as np

DIFF = 40          # how far from the background colour a pixel must be to count as "something"
FILL = 0.01        # share of a row/column that must be "something" for that line to count
EDGE = 0.06        # stray lines are only looked for in this outer band
THIN = 0.015       # a run of lines thinner than this (share of the side) near the edge is a stray line
PAD = 0.06         # margin kept around the subject (share of its longer side)
PAD_MIN = 0.05     # ...but never less than this share of the image's shorter side (keeps shadows)
MIN_CUT = 0.02     # ignore margins smaller than this; only shave the stray lines then


def _lines(occ, n):
    """[start, end) of the subject along one axis, plus how far stray lines reach in from each end."""
    idx = np.flatnonzero(occ)
    if not len(idx):
        return None
    runs = np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1)
    edge, thin = n * EDGE, max(2, n * THIN)
    keep, lo_stray, hi_stray = [], 0, n
    for r in runs:
        if len(r) < thin and r[-1] < edge:
            lo_stray = max(lo_stray, r[-1] + 1)
        elif len(r) < thin and r[0] >= n - edge:
            hi_stray = min(hi_stray, r[0])
        else:
            keep.append(r)
    if not keep:
        return None
    return keep[0][0], keep[-1][-1] + 1, lo_stray, hi_stray


def find_box(frames):
    """frames: list of HxW uint8 greyscale arrays (same size). Union of all frames is kept."""
    h, w = frames[0].shape
    rows, cols = np.zeros(h, bool), np.zeros(w, bool)
    for a in frames:
        a = a.astype(np.int16)
        b = max(2, int(min(h, w) * 0.02))
        band = np.concatenate([a[:b].ravel(), a[-b:].ravel(), a[:, :b].ravel(), a[:, -b:].ravel()])
        bg = np.median(band)
        on = np.abs(a - bg) > DIFF
        rows |= on.mean(1) > FILL
        cols |= on.mean(0) > FILL
    r, c = _lines(rows, h), _lines(cols, w)
    if not r or not c:
        return None
    pad = int(max(max(r[1] - r[0], c[1] - c[0]) * PAD, min(h, w) * PAD_MIN))

    def side(start, end, lo_stray, hi_stray, n):
        lo = start - pad if start - pad > n * MIN_CUT else 0
        hi = end + pad if n - (end + pad) > n * MIN_CUT else n
        # always step past stray edge lines (plus a hair)
        if lo_stray:
            lo = max(lo, min(lo_stray + 2, start))
        if hi_stray < n:
            hi = min(hi, max(hi_stray - 2, end))
        return max(0, lo), min(n, hi)

    top, bottom = side(*r, h)
    left, right = side(*c, w)
    if (left, top, right, bottom) == (0, 0, w, h):
        return None
    return left, top, right, bottom


# ───────── extending a background instead of cropping ─────────

def subject_box(a):
    """(left, top, right, bottom) of the subject in greyscale array a, ignoring stray edge lines."""
    h, w = a.shape
    a = a.astype(np.int16)
    b = max(2, int(min(h, w) * 0.02))
    band = np.concatenate([a[:b].ravel(), a[-b:].ravel(), a[:, :b].ravel(), a[:, -b:].ravel()])
    on = np.abs(a - np.median(band)) > DIFF
    r, c = _lines(on.mean(1) > FILL, h), _lines(on.mean(0) > FILL, w)
    if not r or not c:
        return None
    return c[0], r[0], c[1], r[1]


def _smooth(line, k):
    """box-blur a (n, 3) line of colours along its length, 3 passes ≈ gaussian."""
    if k < 2:
        return line
    ker = np.ones(k) / k
    for _ in range(3):
        line = np.stack([np.convolve(np.pad(line[:, i], k, mode="edge"), ker, "same")[k:-k]
                         for i in range(line.shape[1])], 1)
    return line


def _extend_top(img, n, mode):
    """img: (h, w, 3) float. Returns n new rows to put above it."""
    h, w, _ = img.shape
    if n <= 0:
        return img[:0]
    if mode == "mirror" and n < h // 3:
        return img[1:n + 1][::-1]
    if mode == "solid":
        # the plain colour of the background, for a subject that runs off the edge
        return np.broadcast_to(np.percentile(img[:max(4, h // 100)], 25, axis=(0, 1)), (n, w, 3)).copy()
    # stretch a softened copy of the edge, fading in from the real edge row
    k = max(4, h // 100)
    line = _smooth(img[:k].mean(0), max(3, w // 60))
    block = np.repeat(line[None], n, 0)
    f = min(n, max(8, h // 40))
    t = (np.arange(f)[::-1] / f)[:, None, None]       # 1 at the seam → 0
    block[n - f:] = t * img[0][None] + (1 - t) * block[n - f:]
    return block


def extend(img, top=0, bottom=0, left=0, right=0, mode="stretch"):
    """Grow an image by continuing its own background on each side."""
    img = img.astype(np.float32)
    img = np.concatenate([_extend_top(img, top, mode), img,
                          _extend_top(img[::-1], bottom, mode)[::-1]], 0)
    t = img.transpose(1, 0, 2)
    t = np.concatenate([_extend_top(t, left, mode), t,
                        _extend_top(t[::-1], right, mode)[::-1]], 0)
    return np.clip(t.transpose(1, 0, 2), 0, 255).astype(np.uint8)



# ───────── finishing what a photo cut off ─────────

def _sample(img, x, y):
    """bilinear colours of img at float coordinates x, y."""
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = (x - x0)[..., None], (y - y0)[..., None]
    h, w, _ = img.shape
    x0, x1 = np.clip(x0, 0, w - 1), np.clip(x0 + 1, 0, w - 1)
    y0, y1 = np.clip(y0, 0, h - 1), np.clip(y0 + 1, 0, h - 1)
    return ((img[y0, x0] * (1 - fx) + img[y0, x1] * fx) * (1 - fy)
            + (img[y1, x0] * (1 - fx) + img[y1, x1] * fx) * fy)


def tip_apex(a, b):
    """where the two edges of an object meet. a, b: [[x1, y1], [x2, y2]]."""
    (x1, y1), (x2, y2) = a
    (x3, y3), (x4, y4) = b
    d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    p, q = x1 * y2 - y1 * x2, x3 * y4 - y3 * x4
    return ((p * (x3 - x4) - (x1 - x2) * q) / d, (p * (y3 - y4) - (y1 - y2) * q) / d)


def complete_tip(img, cut, a, b):
    """img: (h, w, 3) float, photo content above row `cut`. An object runs off that row
    between edges a and b. Below it, continue each edge's own bands along that edge,
    joined with a mitre where they meet, so the object ends in a real corner."""
    ax, ay = tip_apex(a, b)
    ys, xs = np.mgrid[cut:min(img.shape[0], int(ay) + 3), 0:img.shape[1]].astype(np.float32)
    def dist(line):
        # distance from line, positive on the side the object is on
        (x1, y1), (x2, y2) = line
        nx, ny = y2 - y1, x1 - x2
        k = np.hypot(nx, ny)
        inside = (other_mid[0] - x1) * nx + (other_mid[1] - y1) * ny
        s = 1 if inside > 0 else -1
        return s * ((xs - x1) * nx + (ys - y1) * ny) / k
    def along(line):
        # slide each pixel along the edge back up into the photo
        (x1, y1), (x2, y2) = line
        src_y = cut - 2.0
        t = (ys - src_y) / (y2 - y1)
        return _sample(img, xs - t * (x2 - x1), np.full_like(ys, src_y))
    def at_cut(line):
        (x1, y1), (x2, y2) = line
        return x1 + (cut - y1) * (x2 - x1) / (y2 - y1)
    other_mid = ((at_cut(a) + at_cut(b)) / 2, float(cut))     # a point inside the object
    da, db = dist(a), dist(b)
    mix = np.clip((db - da) / 6 + 0.5, 0, 1)[..., None]     # 1 near edge a → 0 near edge b
    paint = along(a) * mix + along(b) * (1 - mix)
    alpha = np.clip(np.minimum(da, db) / 1.5 + 0.5, 0, 1)[..., None]
    img[cut:cut + ys.shape[0]] = img[cut:cut + ys.shape[0]] * (1 - alpha) + paint * alpha
    return img


def continue_dark(img, cut, side, seed=7):
    """Rows beyond `cut` on one side ("top" rows above it, "bottom" rows from it on), filled with
    the dark background found at that edge of the photo, column by column, with the photo's own
    grain: no seam. Columns where the work reaches the edge borrow from the dark ones beside them."""
    img = img.astype(np.float32)
    h, w, _ = img.shape
    band = img[cut:cut + 24] if side == "top" else img[cut - 24:cut]
    line = np.median(band, 0)
    grey = line.mean(1)
    dark = grey < 30
    pad = w // 50                                       # stay clear of the glow around the work
    dark &= np.convolve(~dark, np.ones(2 * pad + 1), "same") == 0
    xs = np.arange(w)
    line = np.stack([np.interp(xs, xs[dark], line[dark, i]) for i in range(3)], 1)
    line = _smooth(line, max(3, w // 30))
    grain = float(np.median(band[:, dark].mean(2).std(0)))
    n = cut if side == "top" else h - cut
    rows = np.repeat(line[None], n, 0)
    rows += np.random.default_rng(seed).normal(0, grain, (n, w, 1))
    rows -= rows[:, dark].mean((0, 1)) - band[:, dark].mean((0, 1))   # same overall level as the photo
    if side == "top":
        img[:cut] = rows
    else:
        img[cut:] = rows
    return img
