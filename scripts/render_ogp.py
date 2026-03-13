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



def vertical_gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    width, height = size
    image = Image.new('RGB', size, top)
    draw = ImageDraw.Draw(image)
    for y in range(height):
        ratio = y / max(1, height - 1)
        color = tuple(int(top[i] * (1 - ratio) + bottom[i] * ratio) for i in range(3))
        draw.line((0, y, width, y), fill=color)
    return image



def rounded_box(draw: ImageDraw.ImageDraw, box, radius: int, fill, outline=None, width: int = 1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)



def main() -> None:
    image = vertical_gradient((WIDTH, HEIGHT), (247, 255, 248), (236, 247, 255)).convert('RGBA')
    draw = ImageDraw.Draw(image, 'RGBA')

    draw.ellipse((1002, 18, 1158, 174), fill=(221, 247, 227, 255))
    draw.ellipse((32, 446, 208, 622), fill=(221, 238, 255, 255))

    rounded_box(draw, (72, 72, 1128, 558), 28, fill=(255, 255, 255, 255), outline=(229, 231, 239, 255), width=2)
    rounded_box(draw, (112, 112, 1088, 518), 24, fill=(47, 158, 68, 255))

    accent_overlay = vertical_gradient((976, 406), (47, 158, 68), (100, 201, 122)).convert('RGBA')
    mask = Image.new('L', (976, 406), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 975, 405), radius=24, fill=255)
    image.paste(accent_overlay, (112, 112), mask)

    screen = vertical_gradient((420, 330), (27, 34, 48), (38, 53, 74)).convert('RGBA')
    screen_mask = Image.new('L', (420, 330), 0)
    ImageDraw.Draw(screen_mask).rounded_rectangle((0, 0, 419, 329), radius=22, fill=255)
    image.paste(screen, (614, 150), screen_mask)

    draw = ImageDraw.Draw(image, 'RGBA')
    rounded_box(draw, (650, 188, 762, 218), 15, fill=(255, 107, 74, 255))
    rounded_box(draw, (650, 246, 838, 280), 17, fill=(59, 130, 246, 46))
    rounded_box(draw, (852, 246, 980, 280), 17, fill=(168, 85, 247, 46))
    rounded_box(draw, (650, 294, 806, 328), 17, fill=(47, 158, 68, 52))
    rounded_box(draw, (650, 356, 990, 366), 5, fill=(141, 179, 217, 76))
    rounded_box(draw, (650, 388, 942, 398), 5, fill=(141, 179, 217, 61))
    rounded_box(draw, (650, 420, 878, 430), 5, fill=(141, 179, 217, 46))

    font_small_bold = load_font(16, bold=True)
    font_label = load_font(26, bold=True)
    font_title = load_font(64, bold=True)
    font_sub = load_font(28, bold=True)
    font_chip = load_font(18, bold=True)

    draw.text((706, 203), 'ON AIR', anchor='mm', font=font_small_bold, fill=(255, 255, 255, 255))
    draw.text((160, 190), 'Daily AI Audio Brief', font=font_label, fill=(233, 255, 240, 255))
    draw.text((160, 284), 'ずんだもん', font=font_title, fill=(255, 255, 255, 255))
    draw.text((160, 362), '1分AIニュース', font=font_title, fill=(255, 255, 255, 255))
    draw.text((160, 430), 'AIニュースを、ずんだもんの声で', font=font_sub, fill=(243, 255, 246, 255))
    draw.text((160, 468), '1分前後にまとめてお届け', font=font_sub, fill=(243, 255, 246, 255))
    draw.text((674, 268), '透明性', font=font_chip, fill=(220, 235, 255, 255))
    draw.text((877, 268), '研究', font=font_chip, fill=(242, 222, 255, 255))
    draw.text((674, 316), 'インフラ', font=font_chip, fill=(226, 255, 231, 255))

    wave_points = [(694, 468), (724, 430), (754, 506), (784, 468), (814, 430), (844, 506), (874, 468), (904, 430), (934, 506), (964, 468)]
    draw.line(wave_points, fill=(140, 240, 160, 255), width=10, joint='curve')

    OUT.parent.mkdir(parents=True, exist_ok=True)
    image.convert('RGB').save(OUT, format='PNG', optimize=True)
    print(f'Rendered: {OUT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
