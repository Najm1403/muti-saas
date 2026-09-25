#!/usr/bin/env python3
"""Regenerate every STORIXX favicon / app icon from the two master images.

    python tools/regen_brand_icons.py

Two sources under apps/backend_fastfood/assets/ (square PNG, >= 512px):
  * smartshops.png  — white background   -> website favicons (browser tab)
  * logo.png        — transparent, edge-to-edge   -> Android + Windows app icons

Nothing in code depends on the pixels, so the workflow for a new logo is:
drop in a new master, run this, rebuild the apps.

Outputs
  apps/web_fastfood/assets/*                          dashboard favicons + PWA manifest  (from smartshops.png)
  apps/web_fastfood/favicon.ico                       bare /favicon.ico probe            (from smartshops.png)
  .../android/app/src/main/res/mipmap-*/ic_launcher*  Android launcher, incl. adaptive  (from logo.png)
  .../android/app/src/main/res/mipmap-anydpi-v26/…    adaptive-icon xml                  (from logo.png)
  .../windows/runner/resources/app_icon.ico           Windows exe + taskbar + installer (from logo.png)
  .../flutter_app_fastfood/web/*                      Flutter web build icons           (from logo.png)

Requires Pillow  (apps/backend_fastfood/.venv already has it).
"""
from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "apps/backend_fastfood/assets"
SRC_WEB = ASSETS / "smartshops.png"   # white bg — website favicon
SRC_APP = ASSETS / "logo.png"         # transparent, full-bleed — app icons
ICO_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def _trim(img: Image.Image, thresh: int = 24) -> Image.Image:
    """Crop the empty border off the master, then re-pad to a centred square so
    every render() controls the margin itself.

    The masters are transparent PNGs, so "content" = alpha >= `thresh`. For a
    fully-opaque source we fall back to distance-from-white.
    """
    rgba = img.convert("RGBA")
    r, g, b, a = rgba.split()
    if a.getextrema()[0] < 250:  # has real transparency
        mask = a.point(lambda p: 255 if p >= thresh else 0)
    else:                        # opaque -> use max(255-r,255-g,255-b)
        mask = ImageChops.lighter(
            ImageChops.lighter(ImageChops.invert(r), ImageChops.invert(g)),
            ImageChops.invert(b),
        ).point(lambda p: 255 if p >= thresh else 0)
    bbox = mask.getbbox()
    if not bbox:
        return rgba
    cropped = rgba.crop(bbox)
    side = max(cropped.size)
    square = Image.new("RGBA", (side, side), (255, 255, 255, 0))
    square.alpha_composite(cropped, ((side - cropped.width) // 2, (side - cropped.height) // 2))
    return square


WEB = _trim(Image.open(SRC_WEB).convert("RGBA"))
APP = _trim(Image.open(SRC_APP).convert("RGBA"))


def render(src: Image.Image, size: int, pad: float = 0.06, bg=(0, 0, 0, 0)) -> Image.Image:
    canvas = Image.new("RGBA", (size, size), bg)
    inner = max(1, round(size * (1 - 2 * pad)))
    off = (size - inner) // 2
    canvas.alpha_composite(src.resize((inner, inner), Image.LANCZOS), (off, off))
    return canvas


WHITE = (255, 255, 255, 255)


def png(img: Image.Image, path: Path, rgb: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    (img.convert("RGB") if rgb else img).save(path)
    print("  ", path.relative_to(ROOT))


def main() -> None:
    print(f"web favicon source : {SRC_WEB.relative_to(ROOT)}")
    print(f"app icon source    : {SRC_APP.relative_to(ROOT)}\n")

    # ── SaaS dashboards — from smartshops.png (white bg) ───────────────
    web = ROOT / "apps/web_fastfood/assets"
    print("web dashboards (smartshops.png):")
    png(render(WEB, 16, 0.02, WHITE), web / "favicon-16x16.png")
    png(render(WEB, 32, 0.02, WHITE), web / "favicon-32x32.png")
    png(render(WEB, 48, 0.04, WHITE), web / "favicon-48x48.png")
    png(render(WEB, 180, 0.12, WHITE), web / "apple-touch-icon.png", rgb=True)
    png(render(WEB, 192, 0.08, WHITE), web / "icon-192.png")
    png(render(WEB, 512, 0.08, WHITE), web / "icon-512.png")
    png(render(WEB, 512, 0.18, WHITE), web / "maskable-512.png")
    # transparent brand mark for in-page UI (dark sidebar / login card)
    png(render(WEB, 192, 0.03), web / "logo-mark.png")
    shutil.copy(SRC_WEB, web / "smartshops.png")
    render(WEB, 256, 0.04, WHITE).save(web / "favicon.ico", sizes=ICO_SIZES)
    print("   apps/web_fastfood/assets/favicon.ico")
    shutil.copy(web / "favicon.ico", ROOT / "apps/web_fastfood/favicon.ico")
    print("   apps/web_fastfood/favicon.ico")
    (web / "site.webmanifest").write_text(
        '{\n'
        '  "name": "STORIXX",\n'
        '  "short_name": "STORIXX",\n'
        '  "description": "STORIXX — multi-tenant POS & retail management platform.",\n'
        '  "start_url": "/",\n'
        '  "scope": "/",\n'
        '  "display": "standalone",\n'
        '  "background_color": "#ffffff",\n'
        '  "theme_color": "#1d4ed8",\n'
        '  "icons": [\n'
        '    { "src": "/assets/favicon-32x32.png", "sizes": "32x32", "type": "image/png" },\n'
        '    { "src": "/assets/icon-192.png", "sizes": "192x192", "type": "image/png" },\n'
        '    { "src": "/assets/icon-512.png", "sizes": "512x512", "type": "image/png" },\n'
        '    { "src": "/assets/maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }\n'
        '  ]\n'
        '}\n',
        encoding="utf-8",
    )
    print("   apps/web_fastfood/assets/site.webmanifest")

    # ── Android launcher — from logo.png ──────────────────────────────
    print("android launcher (logo.png):")
    res = ROOT / "apps/flutter_app_fastfood/android/app/src/main/res"
    legacy = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
    adaptive = {"mdpi": 108, "hdpi": 162, "xhdpi": 216, "xxhdpi": 324, "xxxhdpi": 432}
    for d, px in legacy.items():
        # pre-API-26 / fallback: opaque, white bg, safe margin
        sq = render(APP, px, 0.18, WHITE)
        png(sq, res / f"mipmap-{d}/ic_launcher.png", rgb=True)
        png(sq, res / f"mipmap-{d}/ic_launcher_round.png", rgb=True)  # legacy fallback for roundIcon
    for d, px in adaptive.items():
        # API-26+ adaptive foreground: transparent, logo inside the ~66/108 safe zone
        png(render(APP, px, 0.26), res / f"mipmap-{d}/ic_launcher_foreground.png")
    (res / "mipmap-anydpi-v26").mkdir(parents=True, exist_ok=True)
    for name in ("ic_launcher.xml", "ic_launcher_round.xml"):
        (res / "mipmap-anydpi-v26" / name).write_text(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
            '    <background android:drawable="@color/ic_launcher_background" />\n'
            '    <foreground android:drawable="@mipmap/ic_launcher_foreground" />\n'
            '</adaptive-icon>\n',
            encoding="utf-8",
        )
        print("   ", (res / "mipmap-anydpi-v26" / name).relative_to(ROOT))
    (res / "values/colors.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<resources>\n'
        '    <color name="ic_launcher_background">#FFFFFFFF</color>\n'
        '</resources>\n',
        encoding="utf-8",
    )
    print("   ", (res / "values/colors.xml").relative_to(ROOT))
    png(render(APP, 512, 0.18, WHITE), res.parent / "ic_launcher-web.png", rgb=True)

    # ── Windows exe / taskbar / installer — from logo.png ─────────────
    print("windows (logo.png):")
    win_ico = ROOT / "apps/flutter_app_fastfood/windows/runner/resources/app_icon.ico"
    render(APP, 256, 0.08).save(win_ico, sizes=ICO_SIZES)
    print("   ", win_ico.relative_to(ROOT))

    # ── Flutter web build — from logo.png ────────────────────────────
    fweb = ROOT / "apps/flutter_app_fastfood/web"
    if fweb.exists():
        print("flutter web (logo.png):")
        png(render(APP, 32, 0.02), fweb / "favicon.png")
        png(render(APP, 192, 0.08), fweb / "icons/Icon-192.png")
        png(render(APP, 512, 0.08), fweb / "icons/Icon-512.png")
        png(render(APP, 192, 0.22), fweb / "icons/Icon-maskable-192.png")
        png(render(APP, 512, 0.22), fweb / "icons/Icon-maskable-512.png")

    print("\ndone — rebuild: flutter build windows / flutter build apk, then recompile the Inno installer")


if __name__ == "__main__":
    main()
