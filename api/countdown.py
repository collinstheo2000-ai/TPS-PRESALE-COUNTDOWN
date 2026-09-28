"""
Email countdown timer — returns an animated GIF drawn at the moment it's requested.

Deploy on Vercel (free). Use in Mailchimp (Code block) as:
  <img src="https://YOUR-APP.vercel.app/api/countdown?end=2026-10-15T18:00:00%2B01:00" width="600" style="display:block;max-width:100%;height:auto;" alt="Countdown">

Query parameters (all optional except `end`):
  end      Deadline in ISO format with timezone, e.g. 2026-10-15T18:00:00Z (UTC)
           or 2026-10-15T18:00:00+01:00 (write the + as %2B in the URL)
  bg       Background colour hex (default ffffff, the email body)
  fg       Number colour hex (default ffffff)
  label    Label colour hex (default f3e6fa)
  box      Box colour hex (default c75ca5, TPS pink)
  box2     Second box colour for a diagonal gradient (default 6e3379, TPS purple);
           use box2=none for solid boxes
  endfg    Colour of the "expired" text (default 6e3379)
  width    Image width in px (default 600, 300-800)
  expired  Text shown once the deadline has passed (default "OFFER ENDED")
"""

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from io import BytesIO
from urllib.parse import urlparse, parse_qs

import os

from PIL import Image, ImageChops, ImageDraw, ImageFont

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
# Colour presets from the TPS27 campaign palette; pick with ?theme=<name>.
# Any individual colour parameter still overrides the preset.
THEMES = {
    "midnight":  dict(bg="ffffff", box="6f00cb", box2="40008c", fg="f1d864", label="cfa9e4", endfg="40008c"),
    "punch":     dict(bg="ffffff", box="ff376e", box2="ff5aa8", fg="ffffc1", label="ffffc1", endfg="ff376e"),
    "electric":  dict(bg="ffffff", box="40008c", box2="none",   fg="ffffff", label="8af2ff", endfg="40008c"),
    "cream":     dict(bg="ffffff", box="ffffc1", box2="none",   fg="40008c", label="ff376e", endfg="40008c"),
    "blue":      dict(bg="ffffff", box="0f84f6", box2="40008c", fg="ffffff", label="8af2ff", endfg="0f84f6"),
}
DEFAULT_THEME = "cream"

FRAMES = 60  # one minute of ticking; the GIF then rests on its last frame


def hex_colour(value, default):
    value = (value or default).lstrip("#")
    try:
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return tuple(int(default[i:i + 2], 16) for i in (0, 2, 4))


def font(size, weight="700"):
    try:
        return ImageFont.truetype(os.path.join(FONT_DIR, f"SpaceGrotesk-{weight}.ttf"), size)
    except OSError:
        return ImageFont.load_default(size=size)


def gradient(size, c1, c2):
    """Diagonal gradient from c1 (top left) to c2 (bottom right)."""
    w, h = size
    g = Image.new("L", size)
    g.putdata([int(255 * (x / max(w - 1, 1) + y / max(h - 1, 1)) / 2) for y in range(h) for x in range(w)])
    return Image.composite(Image.new("RGB", size, c2), Image.new("RGB", size, c1), g)


def centred_text(draw, box, text, fnt, fill):
    x0, y0, x1, y1 = box
    l, t, r, b = draw.textbbox((0, 0), text, font=fnt)
    draw.text((x0 + (x1 - x0 - (r - l)) / 2 - l, y0 + (y1 - y0 - (b - t)) / 2 - t),
              text, font=fnt, fill=fill)


def parse_end(raw):
    # A literal "+" in a URL arrives as a space, so put it back
    end = datetime.fromisoformat(raw.strip().replace("Z", "+00:00").replace(" ", "+"))
    return end if end.tzinfo else end.replace(tzinfo=timezone.utc)


def render(end, opts, now=None):
    opts = {**THEMES.get(opts.get("theme", DEFAULT_THEME).lower(), THEMES[DEFAULT_THEME]), **opts}
    try:
        width = max(300, min(int(opts.get("width", 600)), 800))
    except ValueError:
        width = 600
    height = int(width * 0.22)  # ~4.5:1 landscape, a touch wider than the header banner
    bg = hex_colour(opts.get("bg"), "ffffff")
    fg = hex_colour(opts.get("fg"), "ffffff")
    lab = hex_colour(opts.get("label"), "f3e6fa")
    box1 = hex_colour(opts.get("box"), "c75ca5")
    box2 = None if opts.get("box2", "").lower() == "none" else hex_colour(opts.get("box2"), "6e3379")
    endfg = hex_colour(opts.get("endfg"), "6e3379")
    expired_text = opts.get("expired", "PRESALE CLOSED")[:40]

    num_font, lab_font = font(int(height * 0.42), "700"), font(int(height * 0.105), "500")
    labels = ["DAYS", "HOURS", "MINS", "SECS"]
    pad, gap = width * 0.02, width * 0.025
    box_w = (width - 2 * pad - 3 * gap) / 4
    y0, y1 = height * 0.06, height * 0.94
    boxes = [(pad + n * (box_w + gap), y0, pad + n * (box_w + gap) + box_w, y1) for n in range(4)]

    now = now or datetime.now(timezone.utc)
    remaining = int((end - now).total_seconds())

    if remaining <= 0:
        img = Image.new("RGB", (width, height), bg)
        centred_text(ImageDraw.Draw(img), (0, 0, width, height), expired_text, font(int(height * 0.24)), endfg)
        frames = [img]
    else:
        # Static layer: background, gradient boxes and labels, drawn once
        base = Image.new("RGB", (width, height), bg)
        fill = gradient((width, height), box1, box2) if box2 else Image.new("RGB", (width, height), box1)
        mask = Image.new("L", (width, height), 0)
        md = ImageDraw.Draw(mask)
        for b in boxes:
            md.rounded_rectangle(b, radius=int(height * 0.09), fill=255)
        base.paste(fill, (0, 0), mask)
        bd = ImageDraw.Draw(base)
        for (x0, by0, x1, by1), name in zip(boxes, labels):
            centred_text(bd, (x0, by0 + (by1 - by0) * 0.66, x1, by1 - (by1 - by0) * 0.08), name, lab_font, lab)

        frames = []
        for i in range(min(FRAMES, remaining + 1)):
            s = remaining - i
            values = [s // 86400, s % 86400 // 3600, s % 3600 // 60, s % 60]
            img = base.copy()
            d = ImageDraw.Draw(img)
            for (x0, by0, x1, by1), v in zip(boxes, values):
                centred_text(d, (x0, by0 + (by1 - by0) * 0.04, x1, by0 + (by1 - by0) * 0.66), f"{v:02d}", num_font, fg)
            frames.append(img)

    # Shared palette across frames keeps the file small and colours stable
    palette_src = frames[0].quantize(colors=256, method=Image.Quantize.MAXCOVERAGE)
    # Pin exact background pixels to one exact-colour palette slot so the timer
    # blends seamlessly into the email (quantizers otherwise drift it to off-white)
    pal = palette_src.getpalette()[:768]
    pal += [0] * (768 - len(pal))
    pal[765:768] = list(bg)
    palette_src.putpalette(pal)
    bg_img = Image.new("RGB", (width, height), bg)
    out_frames = []
    for f in frames:
        q = f.quantize(palette=palette_src, dither=Image.Dither.NONE)
        is_bg = ImageChops.difference(f, bg_img).convert("L").point(lambda v: 255 if v == 0 else 0)
        q.paste(255, (0, 0), is_bg)
        out_frames.append(q)
    frames = out_frames

    out = BytesIO()
    frames[0].save(out, format="GIF", save_all=True, append_images=frames[1:],
                   duration=1000, optimize=True)  # no loop: plays once so time never jumps back
    return out.getvalue()


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        opts = {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}
        try:
            end = parse_end(opts["end"])
        except (KeyError, ValueError):
            self.send_response(400)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Add ?end=2026-10-15T18:00:00Z to the URL")
            return

        gif = render(end, opts)
        self.send_response(200)
        self.send_header("Content-Type", "image/gif")
        self.send_header("Content-Length", str(len(gif)))
        # Never cache, so every open draws the real time remaining
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(gif)
