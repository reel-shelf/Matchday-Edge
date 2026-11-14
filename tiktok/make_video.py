import subprocess, sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
OUT = sys.argv[1]

F = "/usr/share/fonts/opentype/inter/"
def font(name, size): return ImageFont.truetype(F + name, size)
F_HOOK = font("Inter-ExtraBold.otf", 92)
F_NUM = font("InterDisplay-Bold.otf", 230)
F_BODY = font("Inter-Bold.otf", 62)
F_USER = font("Inter-SemiBold.otf", 40) if True else None
F_SMALL = font("Inter-Bold.otf", 44)

BG_TOP, BG_BOT = (18, 18, 28), (44, 20, 60)
ACCENT = (255, 210, 63)
CARD = (255, 255, 255)
INK = (20, 20, 24)
MUTED = (110, 110, 120)

HOOK = "Worst excuses people actually used to skip work"
JOKES = [  # (rank, user, text, optional reply)
    (10, "Sam Hamilton", "Power's out and I have to use a straw to blow bubbles into the fish tank.", None),
    (9, "Carter", "Told my boss I was having a vision problem. When he asked what was going on, I said I couldn't see myself coming in.", None),
    (8, "Smitty", "Had a guy call in \"well\" because it was a nice day and he wanted to drink beer on his porch all day.", None),
    (7, "Cornholio", "I've called in with a fake flu that somehow everyone else managed to catch.", None),
    (6, "Lostbutdontfindme", "\"I dreamed I was at work last night and I'm not going to work a double. See you tomorrow.\"", None),
    (5, "Toaster_media", "Watched my co-worker walk in the door, saw it start to rain, called dispatch in front of the foreman, said he's sick, then left.", None),
    (4, "Carly", "I don't know, but my grandma has died about 47 times.", None),
    (3, "Papa D", "Guy said he had a fever of 109 and sent a picture for proof. The thermometer was sitting right over the stove.", None),
    (2, "drpageisdisappear", "His old man died, so I gave him 3 days off. Next week he calls in Tuesday... he has to help his old man move.", None),
    (1, "Jesse gierisch", "Real text from our work group chat:\n\"I gotta take my lizard to the orthodontist at 8am tmw\"", "Jit missing a tooth"),
]

def gradient():
    im = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(BG_TOP, BG_BOT)))
    return im
BG = gradient()

def wrap(d, text, f, maxw):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split():
            test = (cur + " " + w).strip()
            if d.textlength(test, font=f) <= maxw: cur = test
            else: lines.append(cur); cur = w
        lines.append(cur)
    return lines

def make_card(user, text, reply):
    pad, cw = 60, 920
    tmp = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lines = wrap(tmp, text, F_BODY, cw - 2 * pad)
    lh = 80
    h = pad + 70 + len(lines) * lh + pad
    if reply: h += 150
    card = Image.new("RGBA", (cw, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, cw - 1, h - 1], 44, fill=CARD)
    # avatar + username
    d.ellipse([pad, pad, pad + 50, pad + 50], fill=ACCENT)
    d.text((pad + 25, pad + 25), user[0].upper(), font=F_SMALL, fill=INK, anchor="mm")
    d.text((pad + 70, pad + 25), user, font=F_USER, fill=MUTED, anchor="lm")
    y = pad + 85
    for ln in lines:
        d.text((pad, y), ln, font=F_BODY, fill=INK); y += lh
    if reply:
        y += 30
        rw = d.textlength(reply, font=F_BODY) + 80
        d.rounded_rectangle([cw - pad - rw, y, cw - pad, y + 100], 50, fill=(0, 132, 255))
        d.text((cw - pad - rw / 2, y + 50), reply, font=F_BODY, fill="white", anchor="mm")
    shadow = Image.new("RGBA", (cw + 80, h + 80), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([40, 50, cw + 40, h + 50], 44, fill=(0, 0, 0, 140))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    shadow.alpha_composite(card, (40, 40))
    return shadow

def ease(t): t = max(0, min(1, t)); return 1 - (1 - t) ** 3
def pop(t):  # overshoot scale
    t = max(0, min(1, t)); s = 1.70158
    return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2

segments = [("hook", None, 2.2)]
for j in JOKES:
    words = len(j[2].split()) + (len(j[3].split()) if j[3] else 0)
    segments.append(("joke", j, round(1.8 + words * 0.22, 2)))
segments.append(("end", None, 2.5))
total = sum(s[2] for s in segments)

cards = {j[0]: make_card(j[1], j[2], j[3]) for j in JOKES}

def frame_hook(t):
    im = BG.copy(); d = ImageDraw.Draw(im)
    lines = wrap(d, HOOK, F_HOOK, 900)
    y0 = H // 2 - len(lines) * 115 // 2 - 60
    for i, ln in enumerate(lines):
        a = ease((t - i * 0.12) / 0.4)
        y = y0 + i * 115 + int((1 - a) * 60)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text((W // 2, y), ln, font=F_HOOK, fill=(255, 255, 255, int(255 * a)), anchor="mt")
        im.paste(layer, (0, 0), layer)
    a = ease((t - 0.8) / 0.4)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((W // 2, y0 + len(lines) * 115 + 60), "#1 is unreal", font=F_SMALL, fill=ACCENT + (int(255 * a),), anchor="mt")
    im.paste(layer, (0, 0), layer)
    return im

def frame_joke(j, t, dur):
    im = BG.copy()
    rank = j[0]
    # number pop
    s = pop(t / 0.35)
    label = f"#{rank}"
    num = Image.new("RGBA", (700, 300), (0, 0, 0, 0))
    ImageDraw.Draw(num).text((350, 150), label, font=F_NUM, fill=ACCENT, anchor="mm")
    if s > 0.01:
        n2 = num.resize((max(1, int(700 * s)), max(1, int(300 * s))))
        im.paste(n2, (W // 2 - n2.width // 2, 330 - n2.height // 2), n2)
    # card slide-up
    card = cards[rank]
    a = ease((t - 0.15) / 0.45)
    cy = 560 + int((1 - a) * 140)
    if a > 0:
        c = card.copy()
        c.putalpha(c.getchannel("A").point(lambda v: int(v * a)))
        im.paste(c, (W // 2 - c.width // 2, cy), c)
    return im

def frame_end(t):
    im = BG.copy(); d = ImageDraw.Draw(im)
    a = ease(t / 0.4)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    ld.text((W // 2, 820), "What's the best one", font=F_HOOK, fill=(255, 255, 255, int(255 * a)), anchor="mm")
    ld.text((W // 2, 940), "YOU'VE heard?", font=F_HOOK, fill=ACCENT + (int(255 * a),), anchor="mm")
    ld.text((W // 2, 1090), "Drop it in the comments", font=F_SMALL, fill=(220, 220, 230, int(255 * a)), anchor="mm")
    im.paste(layer, (0, 0), layer)
    return im

ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
    "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-f", "lavfi", "-t", str(total), "-i", "anullsrc=r=44100:cl=stereo",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "18",
    "-c:a", "aac", "-shortest", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)

elapsed = 0.0
for kind, j, dur in segments:
    for f in range(int(round(dur * FPS))):
        t = f / FPS
        im = frame_hook(t) if kind == "hook" else frame_end(t) if kind == "end" else frame_joke(j, t, dur)
        # progress bar
        d = ImageDraw.Draw(im)
        p = (elapsed + t) / total
        d.rectangle([0, H - 14, int(W * p), H], fill=ACCENT)
        ff.stdin.write(im.tobytes())
    elapsed += dur
ff.stdin.close(); ff.wait()
print("total seconds:", round(total, 1))
