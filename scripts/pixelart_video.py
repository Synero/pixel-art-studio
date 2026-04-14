#!/usr/bin/env python3
"""
Pixel Art Video Generator
Generate animated pixel art videos from Pollinations + pixel animations.

Usage:
  python pixelart_video.py "a wizard casting a spell in a dark forest"
  python pixelart_video.py "a neon city street at night" --scene urban --duration 7
  python pixelart_video.py "an underwater temple" --scene underwater --seed 42
  python pixelart_video.py "a dragon over a castle" --tech snes --scene storm
"""
import argparse
import math
import os
import random
import sys
import urllib.parse
from pathlib import Path

import requests
from PIL import Image, ImageDraw

# ── Artistic styles (what the scene looks like) ─────────────────────────────

ARTISTIC_STYLES = {
    "auto":          {"desc": "Let the prompt speak for itself"},
    "cyberpunk":     {"desc": "Neon, futuristic, rain-slicked streets",      "mods": "cyberpunk neon lights, futuristic, rain-slicked, purple and cyan"},
    "medieval":      {"desc": "Castles, knights, swords, dragons",           "mods": "medieval fantasy, stone castles, torchlight, banners"},
    "anime":         {"desc": "Japanese animation, expressive characters",   "mods": "anime style, vibrant colors, expressive eyes, dynamic pose"},
    "noir":          {"desc": "Dark, moody, detective, shadows",            "mods": "film noir, dramatic shadows, dark alley, mystery"},
    "western":       {"desc": "Desert, cowboy, saloon, tumbleweed",         "mods": "wild west, dusty desert, wooden buildings, sunset"},
    "scifi":         {"desc": "Space, robots, technology, holograms",       "mods": "sci-fi, space station, holographic displays, metallic"},
    "kawaii":        {"desc": "Cute, pastel, adorable, soft",              "mods": "kawaii, pastel colors, cute, soft lighting, sparkly"},
    "steampunk":     {"desc": "Gears, brass, Victorian, airships",         "mods": "steampunk, brass gears, Victorian, steam pipes, warm"},
    "horror":        {"desc": "Dark, spooky, Gothic, eerie",               "mods": "horror, dark Gothic, eerie fog, moonlit, unsettling"},
    "underwater":    {"desc": "Ocean, coral, fish, deep sea",              "mods": "underwater, deep blue ocean, coral reef, bioluminescent, light rays"},
    "postapoc":      {"desc": "Ruins, wasteland, overgrown, survivors",    "mods": "post-apocalyptic, overgrown ruins, wasteland, dusty, desolate"},
    "retro":         {"desc": "80s/90s nostalgia, synthwave",              "mods": "retro 80s aesthetic, synthwave, neon grid, gradient sky"},
    "cozy":          {"desc": "Warm, comfortable, homey, relaxing",        "mods": "cozy atmosphere, warm lighting, comfortable, soft textures"},
}

# ── Technical styles (how the pixel art looks) ──────────────────────────────

TECH_STYLES = {
    "nes":     {"desc": "NES 8-bit, limited palette, clean",        "mod": "NES 8-bit style, limited color palette"},
    "snes":    {"desc": "SNES 16-bit, colorful, detailed",         "mod": "SNES sprite style, 16-bit retro"},
    "indie":   {"desc": "Modern indie game, polished pixel art",   "mod": "indie game screenshot, 16 bit style"},
    "arcade":  {"desc": "Bold, chunky, high contrast",             "mod": "retro arcade style, bold colors, high contrast"},
    "gameboy": {"desc": "4 green shades, extreme retro",           "mod": "Game Boy style, 4 green shades"},
    "clean":   {"desc": "Modern, detailed, high fidelity",         "mod": "clean pixel art, detailed, modern retro"},
    "gb":      {"desc": "GBA 32-bit, smooth, handheld",            "mod": "GBA style, smooth handheld, 32-bit"},
}

# ── Scene types (animation behavior for video) ──────────────────────────────

SCENES = {
    "night":       {"desc": "Stars + fireflies + falling leaves",       "mods": "nighttime, dark sky, stars"},
    "dusk":        {"desc": "Fireflies + magic sparkles",               "mods": "twilight, dusk atmosphere, warm glow"},
    "tavern":      {"desc": "Dust motes + warm sparkles",               "mods": "warm interior lighting, cozy, candlelight"},
    "indoor":      {"desc": "Dust motes + ambient glow",                "mods": "indoor scene, warm lighting, ambient"},
    "urban":       {"desc": "Neon glow + rain + sparkles",              "mods": "city street, neon lights, wet pavement, night"},
    "nature":      {"desc": "Falling leaves + fireflies",               "mods": "natural outdoor, forest, green, peaceful"},
    "magic":       {"desc": "Magic sparkles + fire particles",          "mods": "magical atmosphere, glowing energy, mystical"},
    "storm":       {"desc": "Rain + lightning flashes",                 "mods": "storm, dark clouds, dramatic lighting, rain"},
    "underwater":  {"desc": "Bubbles + light rays + particles",        "mods": "underwater, deep blue, light rays, aquatic"},
    "fire":        {"desc": "Embers + sparks + glow",                   "mods": "fire, warm embers, orange glow, smoke hints"},
    "snow":        {"desc": "Snowflakes + cold sparkles",              "mods": "snow, winter, cold atmosphere, white"},
    "desert":      {"desc": "Heat shimmer + dust + sand",              "mods": "desert, hot sun, sandy, dusty atmosphere"},
}

# ── Tech style → Pollinations resolution ────────────────────────────────────
# Pollinations generates "pixel art style" — higher res = more detail.
# 640x480 is the sweet spot for "HD pixel art" look.

TECH_POLL_RES = {
    "nes":     (640, 480),
    "snes":    (640, 480),
    "gameboy": (480, 432),
    "gb":      (640, 427),
    "indie":   (640, 480),
    "arcade":  (640, 560),
    "clean":   (640, 480),
}

DEFAULT_SCENE = "night"
DEFAULT_TECH = "nes"
DEFAULT_DURATION = 6
DEFAULT_FPS = 15
OUTPUT_DIR = os.environ.get("PIXELART_OUTPUT", "./pixelart_output")

# ── Pixel art helpers ────────────────────────────────────────────────────────

def px(draw, x, y, color, size=2):
    x, y = int(x), int(y)
    w, h = draw.im.size
    if 0 <= x < w and 0 <= y < h:
        draw.rectangle([x, y, x + size - 1, y + size - 1], fill=color)

def pixel_cross(draw, x, y, color, arm=2):
    for i in range(-arm, arm + 1):
        px(draw, int(x) + i, int(y), color, 1)
        px(draw, int(x), int(y) + i, color, 1)

def pixel_block(draw, x, y, w, h, color):
    draw.rectangle([int(x), int(y), int(x + w - 1), int(y + h - 1)], fill=color)

# ── Animation generators ────────────────────────────────────────────────────

def init_stars(rng, W, H):
    return [(rng.randint(0, W), rng.randint(0, H // 2)) for _ in range(15)]

def draw_stars(draw, stars, t, W, H):
    for i, (sx, sy) in enumerate(stars):
        if math.sin(t * 2.0 + i * 0.7) > 0.65:
            pixel_cross(draw, sx, sy, (255, 255, 220), arm=2)

def init_fireflies(rng, W, H):
    return [{"x": rng.randint(20, W-20), "y": rng.randint(H//4, H-20),
             "phase": rng.uniform(0, 6.28), "speed": rng.uniform(0.3, 0.8)}
            for _ in range(10)]

def draw_fireflies(draw, ff, t, W, H):
    for f in ff:
        if math.sin(t * 1.5 + f["phase"]) < 0.15:
            continue
        px(draw, f["x"] + math.sin(t * f["speed"] + f["phase"]) * 3,
           f["y"] + math.cos(t * f["speed"] * 0.7) * 2, (200, 255, 100), 2)

def init_leaves(rng, W, H):
    return [{"x": rng.randint(0, W), "y": rng.randint(-H, 0),
             "speed": rng.uniform(0.5, 1.5), "wobble": rng.uniform(0.02, 0.05),
             "phase": rng.uniform(0, 6.28),
             "color": rng.choice([(180, 120, 50), (160, 100, 40), (200, 140, 60)])}
            for _ in range(12)]

def draw_leaves(draw, leaves, t, W, H):
    for leaf in leaves:
        px(draw, leaf["x"] + math.sin(t * leaf["wobble"] + leaf["phase"]) * 15,
           (leaf["y"] + t * leaf["speed"] * 20) % (H + 40) - 20, leaf["color"], 2)

def init_dust_motes(rng, W, H):
    return [{"x": rng.randint(30, W-30), "y": rng.randint(30, H-30),
             "phase": rng.uniform(0, 6.28), "speed": rng.uniform(0.2, 0.5),
             "amp": rng.uniform(2, 6)} for _ in range(20)]

def draw_dust_motes(draw, motes, t, W, H):
    for m in motes:
        if math.sin(t * 2.0 + m["phase"]) > 0.3:
            px(draw, m["x"] + math.sin(t * 0.3 + m["phase"]) * m["amp"],
               m["y"] - (m["speed"] * t * 15) % H, (255, 210, 100), 1)

def init_sparkles(rng, W, H):
    return [(rng.randint(W//4, 3*W//4), rng.randint(H//4, 3*H//4),
             rng.uniform(0, 6.28), rng.choice([(180, 200, 255), (255, 220, 150), (200, 180, 255)]))
            for _ in range(10)]

def draw_sparkles(draw, sparkles, t, W, H):
    for sx, sy, phase, color in sparkles:
        if math.sin(t * 1.8 + phase) > 0.6:
            pixel_cross(draw, sx, sy, color, arm=2)

def init_rain(rng, W, H):
    return [{"x": rng.randint(0, W), "y": rng.randint(0, H),
             "speed": rng.uniform(4, 8)} for _ in range(30)]

def draw_rain(draw, rain, t, W, H):
    for r in rain:
        y = (r["y"] + t * r["speed"] * 20) % H
        px(draw, r["x"], y, (120, 150, 200), 1)
        px(draw, r["x"], y + 4, (100, 130, 180), 1)

def init_lightning(rng, W, H):
    return {"timer": 0, "flash": False}

def draw_lightning(draw, state, t, W, H):
    state["timer"] += 1
    if state["timer"] > 45 and random.random() < 0.04:
        state["flash"] = True
        state["timer"] = 0
    if state["flash"]:
        for x in range(0, W, 4):
            for y in range(0, H // 3, 3):
                if random.random() < 0.12:
                    px(draw, x, y, (255, 255, 240), 2)
        state["flash"] = False

def init_bubbles(rng, W, H):
    return [{"x": rng.randint(20, W-20), "y": rng.randint(H, H*2),
             "speed": rng.uniform(0.3, 0.8), "size": rng.choice([1, 2, 2])}
            for _ in range(15)]

def draw_bubbles(draw, bubbles, t, W, H):
    for b in bubbles:
        x = b["x"] + math.sin(t * 0.5 + b["x"]) * 3
        y = b["y"] - (t * b["speed"] * 20) % (H + 40)
        if 0 < y < H:
            px(draw, x, y, (150, 200, 255), b["size"])

def init_embers(rng, W, H):
    return [{"x": rng.randint(0, W), "y": rng.randint(0, H),
             "speed": rng.uniform(0.3, 0.9), "phase": rng.uniform(0, 6.28),
             "color": rng.choice([(255, 150, 30), (255, 100, 20), (255, 200, 50)])}
            for _ in range(18)]

def draw_embers(draw, embers, t, W, H):
    for e in embers:
        x = e["x"] + math.sin(t * 0.4 + e["phase"]) * 5
        y = e["y"] - (t * e["speed"] * 15) % H
        if math.sin(t * 2.5 + e["phase"]) > 0.2:
            px(draw, x, y, e["color"], 2)

def init_snowflakes(rng, W, H):
    return [{"x": rng.randint(0, W), "y": rng.randint(-H, 0),
             "speed": rng.uniform(0.3, 0.6), "wobble": rng.uniform(0.04, 0.09),
             "size": rng.choice([2, 2, 3])}
            for _ in range(40)]

def draw_snowflakes(draw, flakes, t, W, H):
    for f in flakes:
        x = f["x"] + math.sin(t * f["wobble"] + f["x"]) * 20
        y = (f["y"] + t * f["speed"] * 8) % (H + 20) - 10
        if f["size"] >= 3:
            pixel_cross(draw, x, y, (230, 235, 255), arm=1)
        else:
            px(draw, x, y, (230, 235, 255), 2)

def init_neon_pulse(rng, W, H):
    return [(rng.randint(0, W), rng.randint(0, H),
             rng.uniform(0, 6.28), rng.choice([(255, 0, 200), (0, 255, 255), (255, 50, 150)]))
            for _ in range(8)]

def draw_neon_pulse(draw, points, t, W, H):
    for x, y, phase, color in points:
        if math.sin(t * 2.5 + phase) > 0.5:
            pixel_cross(draw, x, y, color, arm=3)

def init_heat_shimmer(rng, W, H):
    return [{"x": rng.randint(0, W), "y": rng.randint(H//2, H),
             "phase": rng.uniform(0, 6.28)} for _ in range(12)]

def draw_heat_shimmer(draw, points, t, W, H):
    for p in points:
        x = p["x"] + math.sin(t * 0.8 + p["phase"]) * 2
        y = p["y"] + math.sin(t * 1.2 + p["phase"]) * 1
        alpha = abs(math.sin(t * 1.5 + p["phase"]))
        if alpha > 0.6:
            px(draw, x, y, (255, 200, 100), 1)

# ── Scene → animation mapping ────────────────────────────────────────────────

SCENE_ANIMATIONS = {
    "night":      [("init_stars", "draw_stars"), ("init_fireflies", "draw_fireflies"), ("init_leaves", "draw_leaves")],
    "dusk":       [("init_fireflies", "draw_fireflies"), ("init_sparkles", "draw_sparkles")],
    "tavern":     [("init_dust_motes", "draw_dust_motes"), ("init_sparkles", "draw_sparkles")],
    "indoor":     [("init_dust_motes", "draw_dust_motes")],
    "urban":      [("init_rain", "draw_rain"), ("init_neon_pulse", "draw_neon_pulse")],
    "nature":     [("init_leaves", "draw_leaves"), ("init_fireflies", "draw_fireflies")],
    "magic":      [("init_sparkles", "draw_sparkles"), ("init_fireflies", "draw_fireflies")],
    "storm":      [("init_rain", "draw_rain"), ("init_lightning", "draw_lightning")],
    "underwater": [("init_bubbles", "draw_bubbles"), ("init_sparkles", "draw_sparkles")],
    "fire":       [("init_embers", "draw_embers"), ("init_sparkles", "draw_sparkles")],
    "snow":       [("init_snowflakes", "draw_snowflakes"), ("init_sparkles", "draw_sparkles")],
    "desert":     [("init_heat_shimmer", "draw_heat_shimmer"), ("init_dust_motes", "draw_dust_motes")],
}

# ── Pollinations ─────────────────────────────────────────────────────────────

def generate_base(prompt, scene, tech_style, artistic_style, seed=None):
    """Generate base image from Pollinations."""
    import io as _io

    scene_mod = SCENES[scene]["mods"]
    tech_mod = TECH_STYLES[tech_style]["mod"]

    parts = [prompt, "pixel art", tech_mod, scene_mod]

    # Add artistic style if not auto
    if artistic_style != "auto" and artistic_style in ARTISTIC_STYLES:
        parts.append(ARTISTIC_STYLES[artistic_style]["mods"])

    full_prompt = ", ".join(parts)
    W, H = TECH_POLL_RES.get(tech_style, (640, 480))

    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(full_prompt)}?width={W}&height={H}&nologo=true"
    if seed is not None:
        url += f"&seed={seed}"

    print(f"Generating: {full_prompt[:80]}...")
    print(f"  Size: {W}x{H} | Tech: {tech_style} | Artistic: {artistic_style} | Scene: {scene}")

    resp = requests.get(url, timeout=120)
    if resp.status_code != 200 or len(resp.content) < 5000:
        print(f"  FAIL: status={resp.status_code}, size={len(resp.content)}")
        return None, W, H

    print(f"  OK: {len(resp.content) / 1024:.0f}KB")
    return Image.open(_io.BytesIO(resp.content)).convert("RGB"), W, H

# ── Video pipeline ───────────────────────────────────────────────────────────

def generate_video(prompt, scene=DEFAULT_SCENE, tech_style=DEFAULT_TECH,
                   artistic_style="auto",
                   duration=DEFAULT_DURATION, fps=DEFAULT_FPS,
                   seed=None, output=None, export_gif=False):
    """Full pipeline: Pollinations base + pixel animations → MP4 (+ optional GIF)."""

    base, W, H = generate_base(prompt, scene, tech_style, artistic_style, seed)
    if base is None:
        print("Failed to generate base image")
        return None

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    frames_dir = os.path.join(OUTPUT_DIR, "_frames")
    os.makedirs(frames_dir, exist_ok=True)

    if output is None:
        slug = "_".join(prompt.split()[:3]).lower().replace(",", "")
        art = f"_{artistic_style}" if artistic_style != "auto" else ""
        output = os.path.join(OUTPUT_DIR, f"{slug}_{tech_style}{art}_{scene}.mp4")

    rng = random.Random(seed or 42)
    anims = SCENE_ANIMATIONS.get(scene, SCENE_ANIMATIONS["night"])
    animation_states = []
    for init_name, draw_name in anims:
        init_fn = globals()[init_name]
        draw_fn = globals()[draw_name]
        state = init_fn(rng, W, H)
        animation_states.append((draw_fn, state))

    n_frames = fps * duration
    print(f"Generating {n_frames} frames ({duration}s @ {fps}fps)...")

    for frame_idx in range(n_frames):
        canvas = base.copy()
        draw = ImageDraw.Draw(canvas)
        t = frame_idx / fps
        for draw_fn, state in animation_states:
            draw_fn(draw, state, t, W, H)
        canvas.save(os.path.join(frames_dir, f"frame_{frame_idx:04d}.png"))

    print("Encoding video...")
    os.system(f"ffmpeg -y -framerate {fps} -i {frames_dir}/frame_%04d.png "
              f"-c:v libx264 -pix_fmt yuv420p -crf 18 {output}")

    # GIF export (optional)
    gif_path = None
    if export_gif:
        gif_path = output.replace(".mp4", ".gif")
        print("Encoding GIF...")
        os.system(f"ffmpeg -y -framerate {fps} -i {frames_dir}/frame_%04d.png "
                  f"-vf 'scale=320:-1:flags=neighbor,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse' "
                  f"-loop 0 {gif_path}")
        if os.path.exists(gif_path):
            gif_kb = os.path.getsize(gif_path) / 1024
            print(f"  GIF: {gif_path} ({gif_kb:.0f}KB)")

    # Cleanup frames
    for f in os.listdir(frames_dir):
        os.remove(os.path.join(frames_dir, f))
    os.rmdir(frames_dir)

    size_kb = os.path.getsize(output) / 1024
    print(f"Done: {output} ({size_kb:.0f}KB, {duration}s, {fps}fps)")
    return output, gif_path

# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Pixel Art Video Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "a wizard casting a spell in a dark forest"
  %(prog)s "a neon city street at night" --artistic cyberpunk --scene urban
  %(prog)s "a dragon over a castle" --tech snes --scene storm
  %(prog)s "an underwater temple" --scene underwater --artistic horror
  %(prog)s "a cozy cabin in the snow" --scene snow --artistic cozy
  %(prog)s "samurai duel in the rain" --scene storm --artistic anime --tech snes
""",
    )
    parser.add_argument("prompt", nargs="?", default=None, help="Scene description")
    parser.add_argument("--scene", choices=list(SCENES.keys()), default=DEFAULT_SCENE,
                        help="Animation scene type (default: night)")
    parser.add_argument("--tech", choices=list(TECH_STYLES.keys()), default=DEFAULT_TECH,
                        help="Technical pixel art style (default: nes)")
    parser.add_argument("--artistic", choices=list(ARTISTIC_STYLES.keys()), default="auto",
                        help="Artistic/visual style (default: auto)")
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION,
                        help="Video duration in seconds (default: 6)")
    parser.add_argument("--fps", type=int, default=DEFAULT_FPS,
                        help="Frames per second (default: 15)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("-o", "--output", default=None, help="Output MP4 path")
    parser.add_argument("--gif", action="store_true", help="Also export as GIF")
    parser.add_argument("--list-scenes", action="store_true", help="List scene types")
    parser.add_argument("--list-tech", action="store_true", help="List technical styles")
    parser.add_argument("--list-artistic", action="store_true", help="List artistic styles")

    args = parser.parse_args()

    if args.list_scenes:
        print("\nScene types (animation behavior):\n")
        for name, s in SCENES.items():
            print(f"  {name:14s} {s['desc']}")
        return
    if args.list_tech:
        print("\nTechnical styles (how pixels look):\n")
        for name, s in TECH_STYLES.items():
            print(f"  {name:10s} {s['desc']}")
        return
    if args.list_artistic:
        print("\nArtistic styles (what the scene looks like):\n")
        for name, s in ARTISTIC_STYLES.items():
            print(f"  {name:14s} {s['desc']}")
        return

    if not args.prompt:
        parser.error("prompt is required")

    result = generate_video(
        prompt=args.prompt, scene=args.scene, tech_style=args.tech,
        artistic_style=args.artistic,
        duration=args.duration, fps=args.fps, seed=args.seed, output=args.output,
        export_gif=args.gif,
    )
    if result is None or result[0] is None:
        sys.exit(1)

if __name__ == "__main__":
    main()
