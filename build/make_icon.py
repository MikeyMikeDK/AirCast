"""Tegner AirCast-ikonet (blå flise med skærm + AirPlay-trekant) til AirCast/aircast.ico."""

from pathlib import Path

from PIL import Image, ImageDraw

S = 1024
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))

# blå gradient-flise med runde hjørner
grad = Image.new("RGBA", (S, S))
gd = ImageDraw.Draw(grad)
for y in range(S):
    t = y / S
    gd.line([(0, y), (S, y)], fill=(int(61 + 20 * t), int(139 - 60 * t), int(253 - 30 * t), 255))
mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=220, fill=255)
img.paste(grad, (0, 0), mask)

d = ImageDraw.Draw(img)
white = (255, 255, 255, 255)
# skærm
d.rounded_rectangle([170, 210, 854, 650], radius=60, outline=white, width=64)
# hul i bunden af skærmen hvor trekanten sidder
d.rectangle([380, 600, 644, 700], fill=(0, 0, 0, 0))
img.paste(grad.crop((380, 600, 644, 700)), (380, 600))
# AirPlay-trekant
d.polygon([(512, 520), (300, 820), (724, 820)], fill=white)

out = Path(__file__).parent.parent / "aircast.ico"
img.save(out, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print(out)
