#!/usr/bin/env python3
"""
Pixel Art Image Generator
Generate pixel art images from Pollinations with style extraction.

Usage:
  python pixelart_image.py "a wizard in a dark forest"
  python pixelart_image.py "cyberpunk city at night" --artistic cyberpunk --tech snes
  python pixelart_image.py "cute cat on rooftop" --ratio 512x768
  python pixelart_image.py "dragon over castle" --artistic medieval --seed 42
  python pixelart_image.py --list-artistic
  python pixelart_image.py --list-tech
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
from datetime import datetime
from pathlib import Path

import requests

# ── Artistic styles ──────────────────────────────────────────────────────────

ARTISTIC_STYLES = {
    "auto":        {"desc": "Let the prompt speak for itself"},
    "cyberpunk":   {"desc": "Neon, futuristic, rain",         "mods": "cyberpunk neon lights, futuristic, rain-slicked, purple and cyan"},
    "medieval":    {"desc": "Castles, knights, dragons",      "mods": "medieval fantasy, stone castles, torchlight, banners"},
    "anime":       {"desc": "Japanese, expressive, vibrant",  "mods": "anime style, vibrant colors, expressive eyes, dynamic pose"},
    "noir":        {"desc": "Dark, moody, detective",         "mods": "film noir, dramatic shadows, dark alley, mystery"},
    "western":     {"desc": "Desert, cowboy, saloon",         "mods": "wild west, dusty desert, wooden buildings, sunset"},
    "scifi":       {"desc": "Space, robots, holograms",       "mods": "sci-fi, space station, holographic displays, metallic"},
    "kawaii":      {"desc": "Cute, pastel, adorable",         "mods": "kawaii, pastel colors, cute, soft lighting, sparkly"},
    "steampunk":   {"desc": "Gears, brass, Victorian",       "mods": "steampunk, brass gears, Victorian, steam pipes, warm"},
    "horror":      {"desc": "Dark, spooky, Gothic",           "mods": "horror, dark Gothic, eerie fog, moonlit"},
    "underwater":  {"desc": "Ocean, coral, bioluminescent",   "mods": "underwater, deep blue ocean, coral reef, light rays"},
    "postapoc":    {"desc": "Ruins, wasteland, overgrown",    "mods": "post-apocalyptic, overgrown ruins, wasteland, desolate"},
    "retro":       {"desc": "80s/90s nostalgia, synthwave",   "mods": "retro 80s aesthetic, synthwave, neon grid"},
    "cozy":        {"desc": "Warm, comfortable, relaxing",    "mods": "cozy atmosphere, warm lighting, comfortable, soft"},
}

# ── Technical styles ─────────────────────────────────────────────────────────

TECH_STYLES = {
    "nes":     {"desc": "NES 8-bit, limited palette",     "mod": "NES 8-bit style, limited color palette"},
    "snes":    {"desc": "SNES 16-bit, colorful",          "mod": "SNES sprite style, 16-bit retro"},
    "indie":   {"desc": "Modern indie, polished",         "mod": "indie game screenshot, 16 bit style"},
    "arcade":  {"desc": "Bold, chunky, high contrast",    "mod": "retro arcade style, bold colors, high contrast"},
    "gameboy": {"desc": "4 green shades",                 "mod": "Game Boy style, 4 green shades"},
    "clean":   {"desc": "Modern, high fidelity",          "mod": "clean pixel art, detailed, modern retro"},
    "gb":      {"desc": "GBA 32-bit, smooth",             "mod": "GBA style, smooth handheld, 32-bit"},
}

# ── Tech style → Pollinations resolution ────────────────────────────────────
# Pollinations generates "pixel art style" at whatever res you ask.
# Higher res = more detail = "HD pixel art" look. Native res is too low
# and makes it look crude. 640x480 is the sweet spot.

TECH_POLL_RES = {
    "nes":     (640, 480),
    "snes":    (640, 480),
    "gameboy": (480, 432),
    "gb":      (640, 427),
    "indie":   (640, 480),
    "arcade":  (640, 560),
    "clean":   (640, 480),
}

DEFAULT_TECH = "nes"
OUTPUT_DIR = os.environ.get("PIXELART_OUTPUT", "./pixelart_output")
MEMORY_FILE = os.environ.get("PIXELART_MEMORY", "./pixelart_memory.json")

# ── Prompt memory ────────────────────────────────────────────────────────────

def load_memory():
    """Load prompt memory."""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE) as f:
            return json.load(f)
    return {"prompts": [], "stats": {}}

def save_memory(memory):
    """Save prompt memory."""
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)

def record_prompt(memory, prompt, tech, artistic, file_path, success=True):
    """Record a prompt for learning."""
    entry = {
        "prompt": prompt,
        "tech": tech,
        "artistic": artistic,
        "file": file_path,
        "success": success,
        "timestamp": datetime.now().isoformat(),
    }
    memory["prompts"].append(entry)

    # Update stats
    key = f"{tech}_{artistic}"
    if key not in memory["stats"]:
        memory["stats"][key] = {"count": 0, "success": 0}
    memory["stats"][key]["count"] += 1
    if success:
        memory["stats"][key]["success"] += 1

    # Keep last 100 entries
    if len(memory["prompts"]) > 100:
        memory["prompts"] = memory["prompts"][-100:]

    save_memory(memory)

def get_best_combos(memory, limit=5):
    """Get the most successful style combinations."""
    combos = []
    for key, stats in memory.get("stats", {}).items():
        if stats["count"] >= 2:
            rate = stats["success"] / stats["count"]
            combos.append((key, rate, stats["count"]))
    combos.sort(key=lambda x: (x[1], x[2]), reverse=True)
    return combos[:limit]

# ── Generation ───────────────────────────────────────────────────────────────

def generate(prompt, tech_style=DEFAULT_TECH, artistic_style="auto",
             seed=None, output=None):
    """Generate a pixel art image from Pollinations.

    Pollinations generates pixel art style natively — no post-processing needed.
    """
    tech_mod = TECH_STYLES[tech_style]["mod"]
    parts = [prompt, "pixel art", tech_mod]

    if artistic_style != "auto" and artistic_style in ARTISTIC_STYLES:
        parts.append(ARTISTIC_STYLES[artistic_style]["mods"])

    full_prompt = ", ".join(parts)
    W, H = TECH_POLL_RES.get(tech_style, (640, 480))

    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(full_prompt)}?width={W}&height={H}&nologo=true"
    if seed is not None:
        url += f"&seed={seed}"

    print(f"Prompt: {full_prompt[:80]}...")
    print(f"  Size: {W}x{H} | Tech: {tech_style} | Artistic: {artistic_style}")

    resp = requests.get(url, timeout=120)
    if resp.status_code != 200 or len(resp.content) < 5000:
        print(f"  FAIL: status={resp.status_code}, size={len(resp.content)}")
        return None

    # Output — raw Pollinations, no processing
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if output is None:
        slug = "_".join(prompt.split()[:3]).lower().replace(",", "").replace("'", "")
        art = f"_{artistic_style}" if artistic_style != "auto" else ""
        output = os.path.join(OUTPUT_DIR, f"{slug}_{tech_style}{art}_{W}x{H}.png")

    with open(output, "wb") as f:
        f.write(resp.content)

    kb = len(resp.content) / 1024
    print(f"  OK: {output} ({kb:.0f}KB)")
    return output

# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Pixel Art Image Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "a wizard in a dark forest"
  %(prog)s "cyberpunk city" --artistic cyberpunk --tech snes
  %(prog)s "cute cat" --tech gameboy --scale 3
  %(prog)s "dragon" --artistic medieval --seed 42
  %(prog)s --stats
""",
    )
    parser.add_argument("prompt", nargs="?", default=None, help="Scene description")
    parser.add_argument("--tech", choices=list(TECH_STYLES.keys()), default=DEFAULT_TECH,
                        help="Technical style (default: nes)")
    parser.add_argument("--artistic", choices=list(ARTISTIC_STYLES.keys()), default="auto",
                        help="Artistic style (default: auto)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("-o", "--output", default=None, help="Output PNG path")
    parser.add_argument("--list-tech", action="store_true", help="List technical styles")
    parser.add_argument("--list-artistic", action="store_true", help="List artistic styles")
    parser.add_argument("--stats", action="store_true", help="Show prompt stats")
    parser.add_argument("--failed", action="store_true", help="Mark last generation as failed")

    args = parser.parse_args()

    if args.list_tech:
        print("\nTechnical styles:\n")
        for name, s in TECH_STYLES.items():
            print(f"  {name:10s} {s['desc']}")
        return

    if args.list_artistic:
        print("\nArtistic styles:\n")
        for name, s in ARTISTIC_STYLES.items():
            print(f"  {name:14s} {s['desc']}")
        return

    if args.stats:
        memory = load_memory()
        combos = get_best_combos(memory)
        if combos:
            print("\nBest style combos:\n")
            for key, rate, count in combos:
                print(f"  {key}: {rate:.0%} success ({count} uses)")
        else:
            print("No data yet.")
        recent = memory.get("prompts", [])[-5:]
        if recent:
            print("\nRecent prompts:\n")
            for p in recent:
                status = "OK" if p.get("success") else "FAIL"
                print(f"  [{status}] {p['prompt'][:50]}... ({p['tech']}, {p['artistic']})")
        return

    if not args.prompt:
        parser.error("prompt is required")

    memory = load_memory()

    result = generate(
        prompt=args.prompt, tech_style=args.tech, artistic_style=args.artistic,
        seed=args.seed, output=args.output,
    )

    if result:
        record_prompt(memory, args.prompt, args.tech, args.artistic, result, success=True)
        sys.exit(0)
    else:
        record_prompt(memory, args.prompt, args.tech, args.artistic, None, success=False)
        sys.exit(1)

if __name__ == "__main__":
    main()
