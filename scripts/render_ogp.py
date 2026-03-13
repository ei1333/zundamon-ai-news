#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'assets' / 'ogp.png'

WIDTH = 1200
HEIGHT = 630


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



def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top



def draw_text_centered(draw: ImageDraw.ImageDraw, center: tuple[int, int], text: str, font, fill):
    w, h = text_size(draw, text, font)
    x = center[0] - w / 2
    y = center[1] - h / 2
    draw.text((x, y), text, font=font, fill=fill)



def draw_wave(draw: ImageDraw.ImageDraw):
    points = [
        (694, 468),
        (699, 462), (704, 454), (709, 447), (714, 440), (719, 434), (724, 430),
        (729, 428), (734, 433), (739, 443), (744, 456), (749, 470), (754, 484),
        (759, 495), (764, 500), (769, 494), (774, 484), (779, 475), (784, 468),
        (789, 461), (794, 451), (799, 441), (804, 433), (809, 430), (814, 430),
        (819, 431), (824, 438), (829, 449), (834, 463), (839, 478), (844, 492),
        (849, 501), (854, 500), (859, 492), (864, 481), (869, 473), (874, 468),
        (879, 463), (884, 453), (889, 442), (894, 433), (899, 430), (904, 430),
        (909, 432), (914, 440), (919, 452), (924, 467), (929, 482), (934, 494),
        (939, 502), (944, 499), (949, 489), (954, 478), (959, 470), (964, 468),
    ]
    draw.line(points, fill=(140, 240, 160, 255), width=10, joint='curve')



def main() -> None:
    image = linear_gradient((WIDTH, HEIGHT), (247, 255, 248), (236, 247, 255), (0.0, 0.0), (1.0, 1.0)).convert('RGBA')
    draw = ImageDraw.Draw(image, 'RGBA')

    draw.ellipse((1002, 18, 1158, 174), fill=(221, 247, 227, 255))
    draw.ellipse((32, 446, 208, 622), fill=(221, 238, 255, 255))

    rounded_box(draw, (72, 72, 1128, 558), 28, fill=(255, 255, 255, 255), outline=(229, 231, 239, 255), width=2)

    accent_overlay = linear_gradient((976, 406), (47, 158, 68), (100, 201, 122), (0.0, 0.0), (1.0, 1.0)).convert('RGBA')
    mask = Image.new('L', (976, 406), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 975, 405), radius=24, fill=255)
    image.paste(accent_overlay, (112, 112), mask)

    screen = linear_gradient((420, 330), (27, 34, 48), (38, 53, 74), (0.0, 0.0), (1.0, 1.0)).convert('RGBA')
    screen_mask = Image.new('L', (420, 330), 0)
    ImageDraw.Draw(screen_mask).rounded_rectangle((0, 0, 419, 329), radius=22, fill=255)
    image.paste(screen, (614, 150), screen_mask)

    draw = ImageDraw.Draw(image, 'RGBA')
    rounded_box(draw, (650, 188, 762, 218), 15, fill=(255, 107, 74, 255))
    rounded_box(draw, (650, 246, 838, 280), 17, fill=(59, 130, 246, 46))
    rounded_box(draw, (852, 246, 980, 280), 17, fill=(168, 85, 247, 46))
    rounded_box(draw, (650, 294, 806, 328), 17, fill=(47, 158, 68, 51))
    rounded_box(draw, (650, 356, 990, 366), 5, fill=(141, 179, 217, 76))
    rounded_box(draw, (650, 388, 942, 398), 5, fill=(141, 179, 217, 61))
    rounded_box(draw, (650, 420, 878, 430), 5, fill=(141, 179, 217, 46))

    font_small_bold = load_font(16, bold=True)
    font_label = load_font(26, bold=True)
    font_title = load_font(64, bold=True)
    font_sub = load_font(28, bold=True)
    font_chip = load_font(18, bold=True)

    draw_text_centered(draw, (706, 208), 'ON AIR', font_small_bold, (255, 255, 255, 255))
    draw.text((160, 190), 'Daily AI Audio Brief', font=font_label, fill=(233, 255, 240, 255), anchor='la')
    draw.text((160, 284), 'ずんだもん', font=font_title, fill=(255, 255, 255, 255), anchor='la')
    draw.text((160, 362), '1分AIニュース', font=font_title, fill=(255, 255, 255, 255), anchor='la')
    draw.text((160, 430), 'AIニュースを、ずんだもんの声で', font=font_sub, fill=(243, 255, 246, 255), anchor='la')
    draw.text((160, 468), '1分前後にまとめてお届け', font=font_sub, fill=(243, 255, 246, 255), anchor='la')
    draw.text((674, 268), '透明性', font=font_chip, fill=(220, 235, 255, 255), anchor='la')
    draw.text((877, 268), '研究', font=font_chip, fill=(242, 222, 255, 255), anchor='la')
    draw.text((674, 316), 'インフラ', font=font_chip, fill=(226, 255, 231, 255), anchor='la')

    draw_wave(draw)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    image.convert('RGB').save(OUT, format='PNG', optimize=True)
    print(f'Rendered: {OUT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
