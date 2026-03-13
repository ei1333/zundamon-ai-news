#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent

WIDTH = 1200
HEIGHT = 630

BG_GRADIENT = ((247, 255, 248), (236, 247, 255), (0.0, 0.0), (1.0, 1.0))
ACCENT_GRADIENT = ((47, 158, 68), (100, 201, 122), (0.0, 0.0), (1.0, 1.0))
SCREEN_GRADIENT = ((27, 34, 48), (38, 53, 74), (0.0, 0.0), (1.0, 1.0))

OUTER_CARD = (72, 72, 1128, 558, 28)
ACCENT_CARD = (112, 112, 1088, 518, 24)
SCREEN_CARD = (614, 150, 1034, 480, 22)
ON_AIR_BOX = (650, 188, 762, 218, 15)
CHIPS = [
    ((650, 246, 838, 280, 17), (59, 130, 246, 46), '透明性', (674, 258), (220, 235, 255, 255)),
    ((852, 246, 980, 280, 17), (168, 85, 247, 46), '研究', (877, 258), (242, 222, 255, 255)),
    ((650, 294, 806, 328, 17), (47, 158, 68, 51), 'インフラ', (674, 306), (226, 255, 231, 255)),
]
BARS = [
    ((650, 356, 990, 366, 5), (141, 179, 217, 76)),
    ((650, 388, 942, 398, 5), (141, 179, 217, 61)),
    ((650, 420, 878, 430, 5), (141, 179, 217, 46)),
]
WAVE_SEGMENTS = [
    ((694, 468), (724, 430), (754, 506), (784, 468)),
    ((784, 468), (814, 430), (844, 506), (874, 468)),
    ((874, 468), (904, 430), (934, 506), (964, 468)),
]
DEFAULT_TEXT_NODES = [
    ('Daily AI Audio Brief', (160, 186), 26, True, (233, 255, 240, 255), 'la'),
    ('ずんだもん', (160, 274), 64, True, (255, 255, 255, 255), 'la'),
    ('1分AIニュース', (160, 352), 64, True, (255, 255, 255, 255), 'la'),
    ('AIニュースを、ずんだもんの声で', (160, 424), 28, True, (243, 255, 246, 255), 'la'),
    ('1分前後にまとめてお届け', (160, 462), 28, True, (243, 255, 246, 255), 'la'),
]


def load_font(size: int, bold: bool = False):
    candidates = []
    if bold:
        candidates += [
            '/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        ]
    else:
        candidates += [
            '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()



def lerp_color(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))



def linear_gradient(size: tuple[int, int], start: tuple[int, int, int], end: tuple[int, int, int], start_xy: tuple[float, float], end_xy: tuple[float, float]) -> Image.Image:
    width, height = size
    image = Image.new('RGB', size, start)
    draw = ImageDraw.Draw(image)
    sx, sy = start_xy
    ex, ey = end_xy
    dx = ex - sx
    dy = ey - sy
    denom = dx * dx + dy * dy or 1.0
    for y in range(height):
        for x in range(width):
            px = x / max(1, width - 1)
            py = y / max(1, height - 1)
            t = ((px - sx) * dx + (py - sy) * dy) / denom
            t = 0.0 if t < 0.0 else 1.0 if t > 1.0 else t
            draw.point((x, y), fill=lerp_color(start, end, t))
    return image



def rounded_box(draw: ImageDraw.ImageDraw, box, radius: int, fill, outline=None, width: int = 1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)



def text_bbox(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int, int, int]:
    return draw.textbbox((0, 0), text, font=font)



def draw_text_anchor(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font, fill, anchor: str):
    left, top, right, bottom = text_bbox(draw, text, font)
    width = right - left
    height = bottom - top
    x, y = xy
    if anchor == 'middle':
        draw.text((x - width / 2, y - height / 2), text, font=font, fill=fill)
    else:
        draw.text((x, y - top), text, font=font, fill=fill)



def draw_multiline_text(draw: ImageDraw.ImageDraw, x: int, y: int, lines: list[str], font, fill, line_gap: int = 10):
    current_y = y
    for line in lines:
        draw_text_anchor(draw, (x, current_y), line, font, fill, 'la')
        bbox = text_bbox(draw, line, font)
        current_y += (bbox[3] - bbox[1]) + line_gap



def cubic_bezier(p0, p1, p2, p3, steps: int = 32):
    points = []
    for i in range(steps + 1):
        t = i / steps
        mt = 1 - t
        x = (mt ** 3) * p0[0] + 3 * (mt ** 2) * t * p1[0] + 3 * mt * (t ** 2) * p2[0] + (t ** 3) * p3[0]
        y = (mt ** 3) * p0[1] + 3 * (mt ** 2) * t * p1[1] + 3 * mt * (t ** 2) * p2[1] + (t ** 3) * p3[1]
        points.append((x, y))
    return points



def draw_wave(draw: ImageDraw.ImageDraw):
    points = []
    for idx, segment in enumerate(WAVE_SEGMENTS):
        curve = cubic_bezier(*segment, steps=28)
        if idx:
            curve = curve[1:]
        points.extend(curve)
    draw.line(points, fill=(140, 240, 160, 255), width=10, joint='curve')



def paste_gradient_card(image: Image.Image, box_with_radius, gradient_def):
    x1, y1, x2, y2, radius = box_with_radius
    width = x2 - x1
    height = y2 - y1
    start, end, start_xy, end_xy = gradient_def
    overlay = linear_gradient((width, height), start, end, start_xy, end_xy).convert('RGBA')
    mask = Image.new('L', (width, height), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, width - 1, height - 1), radius=radius, fill=255)
    image.paste(overlay, (x1, y1), mask)



def trim_text(text: str, max_chars: int) -> str:
    text = ' '.join(text.split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + '…'



def clean_trailing_text(text: str) -> str:
    return text.rstrip(' 、。・,.;:!！?？…')



def fit_text(text: str, max_chars: int, max_width: int, font, *, ellipsis: bool = True) -> str:
    text = trim_text(text, max_chars) if ellipsis else ' '.join(text.split())[:max_chars].rstrip()
    probe = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    while text:
        bbox = text_bbox(probe, text, font)
        if bbox[2] - bbox[0] <= max_width:
            return clean_trailing_text(text)
        if ellipsis:
            text = text[:-2].rstrip() + '…'
        else:
            text = text[:-1].rstrip()
    return ''



def split_title_lines(title: str, font, max_width: int) -> list[str]:
    title = ' '.join(title.split())
    probe = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    bbox = text_bbox(probe, title, font)
    if bbox[2] - bbox[0] <= max_width:
        return [title]

    parts = title.replace('・', '・|').split('|') if '・' in title else [title]
    if len(parts) > 1:
        lines: list[str] = []
        current = ''
        for part in parts:
            candidate = current + part if current else part
            candidate_bbox = text_bbox(probe, candidate, font)
            if current and candidate_bbox[2] - candidate_bbox[0] > max_width:
                lines.append(current)
                current = part.lstrip()
            else:
                current = candidate
        if current:
            lines.append(current)
        if len(lines) <= 2 and all((text_bbox(probe, line, font)[2] - text_bbox(probe, line, font)[0]) <= max_width for line in lines):
            return lines

    best_split = None
    for i in range(1, len(title)):
        left = title[:i].rstrip(' ・')
        right = title[i:].lstrip(' ・')
        if not left or not right:
            continue
        left_w = text_bbox(probe, left, font)[2] - text_bbox(probe, left, font)[0]
        right_w = text_bbox(probe, right, font)[2] - text_bbox(probe, right, font)[0]
        if left_w <= max_width and right_w <= max_width:
            score = abs(left_w - right_w)
            if best_split is None or score < best_split[0]:
                best_split = (score, left, right)
    if best_split:
        return [best_split[1], best_split[2]]

    first = fit_text(title, len(title), max_width, font)
    consumed = len(first.rstrip('…'))
    rest = title[consumed:].lstrip(' ・')
    second = fit_text(rest or title, len(rest or title), max_width, font)
    return [first, second]



def render_ogp(*, out_path: Path, text_nodes: list[tuple], multiline_blocks: list[tuple] | None = None, chips=CHIPS):
    image = linear_gradient((WIDTH, HEIGHT), *BG_GRADIENT).convert('RGBA')
    draw = ImageDraw.Draw(image, 'RGBA')

    draw.ellipse((1002, 18, 1158, 174), fill=(221, 247, 227, 255))
    draw.ellipse((32, 446, 208, 622), fill=(221, 238, 255, 255))

    rounded_box(draw, OUTER_CARD[:4], OUTER_CARD[4], fill=(255, 255, 255, 255), outline=(229, 231, 239, 255), width=2)
    paste_gradient_card(image, ACCENT_CARD, ACCENT_GRADIENT)
    paste_gradient_card(image, SCREEN_CARD, SCREEN_GRADIENT)

    draw = ImageDraw.Draw(image, 'RGBA')
    rounded_box(draw, ON_AIR_BOX[:4], ON_AIR_BOX[4], fill=(255, 107, 74, 255))
    for box, fill, label, label_xy, text_fill in chips:
        rounded_box(draw, box[:4], box[4], fill=fill)
        draw_text_anchor(draw, label_xy, label, load_font(18, bold=True), text_fill, 'la')
    for box, fill in BARS:
        rounded_box(draw, box[:4], box[4], fill=fill)

    draw_text_anchor(draw, (706, 199), 'ON AIR', load_font(16, bold=True), (255, 255, 255, 255), 'middle')
    for text, xy, size, bold, fill, anchor in text_nodes:
        draw_text_anchor(draw, xy, text, load_font(size, bold=bold), fill, anchor)
    for lines, xy, size, bold, fill, line_gap in multiline_blocks or []:
        draw_multiline_text(draw, xy[0], xy[1], lines, load_font(size, bold=bold), fill, line_gap=line_gap)

    draw_wave(draw)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.convert('RGB').save(out_path, format='PNG', optimize=True)
    print(f'Rendered: {out_path.relative_to(ROOT)}')



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Render shared or per-episode OGP PNG image.')
    parser.add_argument('--date', help='Episode date in YYYY-MM-DD format')
    parser.add_argument('--title', help='Episode title for per-episode OGP')
    parser.add_argument('--summary', help='Episode summary for per-episode OGP')
    return parser.parse_args()



def main() -> None:
    args = parse_args()

    if args.date:
        date = args.date
        title_font_size = 40
        title_font = load_font(title_font_size, bold=True)
        title_lines = split_title_lines(trim_text(args.title or 'ずんだもん1分AIニュース', 28), title_font, max_width=410)
        text_nodes = [
            ('Daily Episode', (160, 186), 26, True, (233, 255, 240, 255), 'la'),
            (date, (160, 262), 44, True, (255, 255, 255, 255), 'la'),
            ('ずんだもん1分AIニュース', (160, 434 if len(title_lines) == 1 else 458), 28, True, (243, 255, 246, 255), 'la'),
        ]
        multiline_blocks = [
            (title_lines, (160, 336), title_font_size, True, (255, 255, 255, 255), 10),
        ]
        render_ogp(out_path=ROOT / 'assets' / f'ogp-{date}.png', text_nodes=text_nodes, multiline_blocks=multiline_blocks)
        return

    render_ogp(out_path=ROOT / 'assets' / 'ogp.png', text_nodes=DEFAULT_TEXT_NODES)


if __name__ == '__main__':
    main()
