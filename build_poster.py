#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import subprocess
import textwrap
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
SCRATCH = ROOT / "scratch"
OUT = ROOT / "output"


@dataclass(frozen=True)
class Source:
    key: str
    label: str
    url: str
    source_page: str
    kind: str = "portrait"
    filename: str | None = None
    crop_bias_x: float = 0.5
    crop_bias_y: float = 0.42


SOURCES = [
    Source(
        "bruno",
        "Bruno Balen",
        "https://pbs.twimg.com/profile_images/1964627526107439104/km6JSrWi_400x400.jpg",
        "https://x.com/Bruno_Balen",
        crop_bias_y=0.48,
    ),
    Source(
        "nika",
        "Nika Pintar",
        "https://static.wixstatic.com/media/4178d0_da591177e53a413fbe2b578784a333d7~mv2.png/v1/fill/w_1080,h_1080,al_c/Nika%20Pintar.png",
        "https://www.longevityinvestors.ch/davos-speakers-2024/nika-pintar",
        crop_bias_y=0.44,
    ),
    Source(
        "evelyne",
        "Evelyne Bischof",
        "https://static.tildacdn.one/tild3037-3964-4539-b331-653330646630/Eva.jpeg",
        "https://hlms.co/evelyne",
        crop_bias_y=0.38,
    ),
    Source(
        "michael",
        "Michael Snyder",
        "https://gregor.stanford.edu/sites/g/files/sbiybj22476/files/styles/card_1192x596/public/media/image/michael_snyder_0.jpg?h=00474aed&itok=0bfJ3H5B",
        "https://gregor.stanford.edu/people/michael-snyder-phd",
        crop_bias_y=0.42,
    ),
    Source(
        "vadim",
        "Vadim Gladyshev",
        "https://gladyshevlab.bwh.harvard.edu/wp-content/themes/gladyshev/data/team/photos/vadim-gladyshev.jpg",
        "https://gladyshevlab.bwh.harvard.edu/team/",
        crop_bias_y=0.42,
    ),
    Source(
        "steve",
        "Steve Horvath",
        "https://s3.amazonaws.com/cms.ipressroom.com/173/files/20166/5792ae172cfac209150c62cb_Steve+Horvath/Steve+Horvath_30eed368-c3fc-4ee7-84e6-dc0eeba88cdc-prv.jpg",
        "https://newsroom.ucla.edu/file?fid=5792ae172cfac209150c62cb",
        crop_bias_y=0.42,
    ),
    Source(
        "brian",
        "Brian Kennedy",
        "https://www.buckinstitute.org/wp-content/uploads/2018/06/14_BRIAN_KENNEDY_0014.jpg",
        "https://www.buckinstitute.org/news/brian-k-kennedy-phd-appointed-as-new-ceo-of-buck-institute-for-age-research/",
        crop_bias_y=0.42,
    ),
    Source(
        "ani_logo",
        "ANI.AI logo",
        "https://ani.ai/assets/ani-ai-logo-black.png",
        "https://ani.ai/",
        kind="logo",
        filename="ani-ai-logo-black.png",
    ),
    Source(
        "xprize_svg",
        "XPRIZE logo",
        "https://assets-us-01.kc-usercontent.com/9bc15d1f-8a5c-007d-b507-e3496e85af86/400b6a1b-6641-4887-9b70-3cc9e27706ce/XPRIZE-Logo-Black.svg",
        "https://www.xprize.org/competitions/healthspan",
        kind="logo",
        filename="xprize-logo-black.svg",
    ),
    Source(
        "healthspan_logo",
        "XPRIZE Healthspan logo",
        "https://assets-us-01.kc-usercontent.com/9bc15d1f-8a5c-007d-b507-e3496e85af86/753f3f3b-4089-4e49-a164-ec40b9a018ad/XPHS-Logo-Inline-WHITE_Hevolution.png?w=1000",
        "https://www.xprize.org/competitions/healthspan",
        kind="logo",
        filename="xprize-healthspan-white.png",
    ),
    Source(
        "solve_fshd_logo",
        "SOLVE FSHD logo",
        "https://assets-us-01.kc-usercontent.com/9bc15d1f-8a5c-007d-b507-e3496e85af86/9635780c-b4ea-4325-9b2f-e471e46ea952/sovefshd.png?w=900",
        "https://www.xprize.org/sponsors/solve-fshd",
        kind="logo",
        filename="solve-fshd.png",
    ),
]


def ensure_dirs() -> None:
    for path in (ASSETS, SCRATCH, OUT):
        path.mkdir(parents=True, exist_ok=True)


def asset_path(source: Source) -> Path:
    if source.filename:
        return ASSETS / source.filename
    ext = source.url.split("?")[0].split(".")[-1].lower()
    if ext not in {"jpg", "jpeg", "png", "webp", "svg"}:
        ext = "jpg"
    return ASSETS / f"{source.key}.{ext}"


def download(url: str, path: Path) -> None:
    if path.exists() and path.stat().st_size > 1000:
        return
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 poster-builder"},
    )
    with urllib.request.urlopen(req, timeout=45) as response:
        payload = response.read()
    path.write_bytes(payload)


def rasterize_svg(svg: Path, out_png: Path) -> bool:
    if out_png.exists() and out_png.stat().st_size > 1000:
        return True
    try:
        subprocess.run(
            ["qlmanage", "-t", "-s", "1600", "-o", str(out_png.parent), str(svg)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=30,
        )
    except Exception:
        return False
    generated = out_png.parent / f"{svg.name}.png"
    if generated.exists():
        generated.replace(out_png)
        return True
    return False


def font(size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
    candidates = {
        "regular": [
            "/System/Library/Fonts/HelveticaNeue.ttc",
            "/System/Library/Fonts/SFNS.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
        ],
        "medium": [
            "/System/Library/Fonts/HelveticaNeue.ttc",
            "/System/Library/Fonts/SFNS.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        ],
        "bold": [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial Black.ttf",
            "/System/Library/Fonts/SFNS.ttf",
        ],
        "condensed": [
            "/System/Library/Fonts/Avenir Next Condensed.ttc",
            "/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial Narrow.ttf",
        ],
    }[weight]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def cover_crop(im: Image.Image, size: tuple[int, int], bias_x: float = 0.5, bias_y: float = 0.5) -> Image.Image:
    im = ImageOps.exif_transpose(im).convert("RGB")
    target_w, target_h = size
    scale = max(target_w / im.width, target_h / im.height)
    new_w = math.ceil(im.width * scale)
    new_h = math.ceil(im.height * scale)
    im = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = int((new_w - target_w) * bias_x)
    top = int((new_h - target_h) * bias_y)
    left = max(0, min(new_w - target_w, left))
    top = max(0, min(new_h - target_h, top))
    return im.crop((left, top, left + target_w, top + target_h))


def portrait_tile(source: Source, tile_w: int, tile_h: int) -> Image.Image:
    raw = Image.open(asset_path(source))
    crop = cover_crop(raw, (tile_w, tile_h), source.crop_bias_x, source.crop_bias_y)
    gray = ImageOps.grayscale(crop)
    gray = ImageOps.autocontrast(gray, cutoff=1)
    gray = ImageEnhance.Contrast(gray).enhance(1.08)
    # Gentle matte keeps web portraits from looking mismatched.
    rgb = ImageOps.colorize(gray, black="#171717", white="#f4f1eb")
    return rgb.filter(ImageFilter.UnsharpMask(radius=1.4, percent=70, threshold=3))


def paste_fit(base: Image.Image, im: Image.Image, box: tuple[int, int, int, int], mode: str = "contain") -> None:
    x, y, w, h = box
    im = ImageOps.exif_transpose(im).convert("RGBA")
    if mode == "cover":
        fitted = cover_crop(im.convert("RGB"), (w, h)).convert("RGBA")
    else:
        scale = min(w / im.width, h / im.height)
        fitted = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.Resampling.LANCZOS)
    px = x + (w - fitted.width) // 2
    py = y + (h - fitted.height) // 2
    base.alpha_composite(fitted, (px, py))


def draw_centered_text(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, fnt, fill) -> None:
    x, y, w, h = box
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((x + (w - tw) / 2, y + (h - th) / 2 - bbox[1]), text, font=fnt, fill=fill)


def make_contact_sheet(portraits: list[Source]) -> None:
    tile = (360, 430)
    label_h = 58
    gap = 24
    cols = 4
    rows = math.ceil(len(portraits) / cols)
    sheet = Image.new("RGB", (cols * tile[0] + (cols + 1) * gap, rows * (tile[1] + label_h) + (rows + 1) * gap), "white")
    d = ImageDraw.Draw(sheet)
    for i, source in enumerate(portraits):
        col = i % cols
        row = i // cols
        x = gap + col * (tile[0] + gap)
        y = gap + row * (tile[1] + label_h + gap)
        im = portrait_tile(source, *tile)
        sheet.paste(im, (x, y))
        draw_centered_text(d, (x, y + tile[1] + 8, tile[0], 36), source.label, font(24), "#171717")
    sheet.save(OUT / "ANI_XPRIZE_CORE_TEAM_POSTER_CONTACT_SHEET.png")


def make_poster(portraits: list[Source]) -> Image.Image:
    W, H = 3300, 4200
    poster = Image.new("RGBA", (W, H), "#f7f5ef")
    d = ImageDraw.Draw(poster)

    ink = "#111111"
    soft = "#67645f"
    line = "#c9c3b8"
    paper = "#f7f5ef"
    black = "#111111"

    margin = 190
    logo_h = 105
    ani_logo = Image.open(ASSETS / "ani-ai-logo-black.png")
    paste_fit(poster, ani_logo, (margin, 150, 300, logo_h))

    xprize_text = "XPRIZE"
    xprize_font = font(74, "bold")
    bbox = d.textbbox((0, 0), xprize_text, font=xprize_font)
    d.text((W - margin - (bbox[2] - bbox[0]), 164), xprize_text, font=xprize_font, fill=ink)

    d.line((margin, 315, W - margin, 315), fill=line, width=2)
    title_font = font(168, "regular")
    subtitle_font = font(48, "regular")
    small_font = font(34, "regular")
    name_font = font(40, "regular")

    d.text((margin, 460), "ANI.AI XPRIZE", font=title_font, fill=ink)
    d.text((margin, 635), "Core Team", font=title_font, fill=ink)
    d.text((margin, 860), "XPRIZE Healthspan / XPRIZE FSHD", font=subtitle_font, fill=soft)

    # Small constellation points echo the ANI deck without adding color.
    for x, y, r in [
        (2520, 515, 6), (2835, 600, 4), (2705, 780, 5), (3005, 875, 4),
        (2390, 845, 4), (2620, 965, 5), (3040, 470, 5), (2860, 1010, 4),
    ]:
        d.ellipse((x - r, y - r, x + r, y + r), fill=ink)
    for a, b in [((2520, 515), (2835, 600)), ((2835, 600), (2705, 780)), ((2705, 780), (3005, 875)), ((2390, 845), (2620, 965))]:
        d.line((a[0], a[1], b[0], b[1]), fill="#d8d3ca", width=2)

    top_y = 1190
    tile_w, tile_h = 392, 500
    gap_x = 64
    row_gap = 128
    cols_top = 4
    start_x_top = (W - (cols_top * tile_w + (cols_top - 1) * gap_x)) // 2
    cols_bottom = 3
    start_x_bottom = (W - (cols_bottom * tile_w + (cols_bottom - 1) * gap_x)) // 2

    positions: list[tuple[int, int]] = []
    for i in range(4):
        positions.append((start_x_top + i * (tile_w + gap_x), top_y))
    bottom_y = top_y + tile_h + 92 + row_gap
    for i in range(3):
        positions.append((start_x_bottom + i * (tile_w + gap_x), bottom_y))

    for source, (x, y) in zip(portraits, positions):
        im = portrait_tile(source, tile_w, tile_h)
        poster.alpha_composite(im.convert("RGBA"), (x, y))
        d.rectangle((x, y, x + tile_w, y + tile_h), outline="#0f0f0f", width=2)
        draw_centered_text(d, (x - 20, y + tile_h + 28, tile_w + 40, 58), source.label, name_font, ink)

    divider_y = bottom_y + tile_h + 170
    d.line((margin, divider_y, W - margin, divider_y), fill=line, width=2)

    # Bottom logo band: understated and non-hierarchical.
    band_y = divider_y + 105
    band_h = 430
    d.rounded_rectangle((margin, band_y, W - margin, band_y + band_h), radius=0, fill=black)

    health = Image.open(ASSETS / "xprize-healthspan-white.png")
    paste_fit(poster, health, (margin + 120, band_y + 78, 1140, 175))

    solve = Image.open(ASSETS / "solve-fshd.png").convert("RGBA")
    # Desaturate and invert toward white so it sits with the Healthspan mark.
    alpha = solve.getchannel("A") if solve.mode == "RGBA" else None
    gray = ImageOps.grayscale(solve.convert("RGB"))
    gray = ImageOps.autocontrast(gray)
    solve_white = ImageOps.colorize(gray, black="#f7f5ef", white="#f7f5ef").convert("RGBA")
    if alpha:
        solve_white.putalpha(alpha)
    paste_fit(poster, solve_white, (W - margin - 1000, band_y + 78, 860, 175))

    d.line((W // 2, band_y + 80, W // 2, band_y + band_h - 80), fill="#696969", width=2)
    draw_centered_text(d, (margin, band_y + 285, W - 2 * margin, 54), "XPRIZE Healthspan  /  SOLVE FSHD Bonus Prize", small_font, "#e8e2d8")

    footer_y = band_y + band_h + 92
    d.text((margin, footer_y), "ANI.AI", font=font(38, "regular"), fill=soft)
    footer = "Portraits and marks normalized from public source pages. Names only; no role hierarchy."
    bbox = d.textbbox((0, 0), footer, font=font(31, "regular"))
    d.text((W - margin - (bbox[2] - bbox[0]), footer_y + 3), footer, font=font(31, "regular"), fill=soft)

    return poster


def write_sources_md() -> None:
    lines = [
        "# ANI.AI XPRIZE Core Team Poster Sources",
        "",
        "Generated by `build_poster.py`. Portraits were converted to a uniform black-and-white treatment and cropped to a common size.",
        "",
        "| Asset | Source page | Direct asset URL |",
        "|---|---|---|",
    ]
    for s in SOURCES:
        lines.append(f"| {s.label} | {s.source_page} | {s.url} |")
    (ROOT / "SOURCES.md").write_text("\n".join(lines) + "\n")
    (ROOT / "source_manifest.json").write_text(json.dumps([s.__dict__ for s in SOURCES], indent=2) + "\n")


def main() -> None:
    ensure_dirs()
    for source in SOURCES:
        download(source.url, asset_path(source))

    xprize_svg = ASSETS / "xprize-logo-black.svg"
    if xprize_svg.exists():
        rasterize_svg(xprize_svg, ASSETS / "xprize-logo-black.png")

    portraits = [s for s in SOURCES if s.kind == "portrait"]
    make_contact_sheet(portraits)
    poster = make_poster(portraits)

    png = OUT / "ANI_AI_XPRIZE_CORE_TEAM_POSTER_2026-06-10.png"
    pdf = OUT / "ANI_AI_XPRIZE_CORE_TEAM_POSTER_2026-06-10.pdf"
    poster.convert("RGB").save(png, quality=96)
    poster.convert("RGB").save(pdf, "PDF", resolution=300.0)
    write_sources_md()
    print(png)
    print(pdf)
    print(OUT / "ANI_XPRIZE_CORE_TEAM_POSTER_CONTACT_SHEET.png")


if __name__ == "__main__":
    main()
