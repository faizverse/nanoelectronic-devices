# Original procedural artwork: chip wiring dissolving into a quantum interference pattern.
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
rng = np.random.default_rng(6353)
def render(W, H, fname, text=None):
    y, x = np.mgrid[0:H, 0:W].astype(float)
    u, v = x / W, y / H
    # background: deep navy gradient
    bg = np.stack([np.full_like(u, 14), np.full_like(u, 26), np.full_like(u, 46)], -1)
    bg += (np.stack([8, 14, 24]) * (1 - v)[..., None])
    # quantum part: superposition of particle-in-a-box modes + two-source interference, right side
    cx1, cy1, cx2, cy2 = 0.70 * W, 0.42 * H, 0.86 * W, 0.62 * H
    k = 2 * np.pi / (0.045 * W)
    r1, r2 = np.hypot(x - cx1, y - cy1), np.hypot(x - cx2, y - cy2)
    psi = np.exp(1j * k * r1) / np.sqrt(r1 + 40) + 0.9 * np.exp(1j * k * r2) / np.sqrt(r2 + 40)
    box = (np.sin(3 * np.pi * u) * np.sin(2 * np.pi * v) + 0.6 * np.sin(5 * np.pi * u) * np.sin(3 * np.pi * v))
    dens = np.abs(psi) ** 2; dens /= np.percentile(dens, 99.5); dens = np.clip(dens, 0, 1.2)
    dens *= (0.55 + 0.45 * box ** 2)
    fade = np.clip((u - 0.32) / 0.35, 0, 1) ** 1.5           # quantum pattern grows to the right
    rust, gold, blue = np.array([214, 104, 62]), np.array([236, 184, 92]), np.array([92, 160, 225])
    col = (dens[..., None] * (rust * (1 - v)[..., None] + blue * v[..., None]) + (dens ** 3)[..., None] * gold * 0.6)
    img = bg + col * fade[..., None] * 0.9
    # contour rings of |psi|^2 for a crisp 'wave' look
    rings = np.exp(-((np.cos(k * r1) + np.cos(k * r2)) ** 2) * 8) * fade
    img += rings[..., None] * np.array([60, 90, 130]) * 0.35
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    # chip wiring on the left: Manhattan routes with vias, fading out to the right
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    pitch = max(8, W // 120)
    for i in range(int(W * H / 9000)):
        x0 = rng.integers(0, int(W * 0.62)) // pitch * pitch; y0 = rng.integers(0, H) // pitch * pitch
        pts = [(x0, y0)]
        for s in range(rng.integers(2, 5)):
            lx, ly = pts[-1]
            if s % 2 == 0: pts.append((lx + int(rng.integers(-12, 22)) * pitch, ly))
            else: pts.append((lx, ly + int(rng.integers(-10, 10)) * pitch))
        a = int(max(0, 1 - x0 / (W * 0.66)) * 150) + 20
        colr = (120, 165, 215, a) if rng.random() < 0.7 else (214, 120, 80, a)
        d.line(pts, fill=colr, width=max(2, pitch // 4))
        for (px, py) in (pts[0], pts[-1]):
            r = max(2, pitch // 3); d.rectangle([px - r, py - r, px + r, py + r], fill=(236, 184, 92, min(255, a + 40)))
    glow = lay.filter(ImageFilter.GaussianBlur(pitch * 0.6))
    im = Image.alpha_composite(Image.alpha_composite(im.convert("RGBA"), glow), lay).convert("RGB")
    # gentle vignette
    vig = np.clip(1.15 - 0.55 * ((u - 0.5) ** 2 + (v - 0.5) ** 2) * 2.2, 0.55, 1)
    arr = (np.asarray(im).astype(float) * vig[..., None]).astype(np.uint8); im = Image.fromarray(arr)
    if text:
        d = ImageDraw.Draw(im); F = "/usr/share/fonts/truetype/dejavu/"
        try:
            fb = ImageFont.truetype(F + "DejaVuSerif-Bold.ttf", 66); fm = ImageFont.truetype(F + "DejaVuSans.ttf", 30); fs = ImageFont.truetype(F + "DejaVuSans-Bold.ttf", 28)
        except OSError:
            fb = fm = fs = ImageFont.load_default()
        # dark panel for legibility
        pan = Image.new("RGBA", im.size, (0, 0, 0, 0)); pd = ImageDraw.Draw(pan); pd.rectangle([0, 0, int(W * 0.66), H], fill=(10, 20, 38, 150))
        im = Image.alpha_composite(im.convert("RGBA"), pan.filter(ImageFilter.GaussianBlur(30))).convert("RGB"); d = ImageDraw.Draw(im)
        d.text((64, 92), "KKKC6353", font=fs, fill=(236, 184, 92))
        d.text((64, 132), "Nanoelectronic", font=fb, fill=(255, 255, 255)); d.text((64, 208), "Devices", font=fb, fill=(255, 255, 255))
        d.text((64, 306), "Interactive animations and course materials", font=fm, fill=(214, 226, 240))
        d.rectangle([64, 380, 120, 384], fill=(214, 104, 62))
        d.text((64, 410), "Dr Muhammad Faiz Bukhori", font=fs, fill=(255, 255, 255))
        d.text((64, 452), "Universiti Kebangsaan Malaysia · 2026", font=fm, fill=(214, 226, 240))
    im.save(fname, quality=86, optimize=True, progressive=True)
render(2400, 900, "hero.jpg")
render(1200, 630, "og-image.jpg", text=True)
