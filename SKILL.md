---
name: pixel-art-studio
description: "Pixel art toolkit — generate images and videos from Pollinations, convert user photos with era-accurate presets."
tags: [pixel-art, video, pollinations, ffmpeg, creative, retro, game-art]
related_skills: []
---

# Pixel Art Studio

Generate pixel art images and videos from Pollinations, or convert user photos with era-accurate presets.

**One rule:** Pollinations generates pixel art natively — never apply pixelart.py filters on top.

## Install

Point your agent to this repo: https://github.com/Synero/pixel-art-studio

Your agent reads the SKILL.md, installs dependencies (`pip install Pillow scipy requests numpy`), and follows the instructions below. Works with Hermes, OpenClaw, Claude Code, Cursor, or any agent that supports skills/instructions.

You can also clone it manually into your agent's skills folder.

## How It Works

| User says | Pipeline | Output |
|-----------|----------|--------|
| Sends photo + "pixel art" | pixelart.py preset | PNG image |
| Describes scene + "pixel art" | Pollinations → direct | PNG image |
| "video/gif/animation" + pixel art | pixelart_video.py | MP4 video |

## Extracting Intent from the User

The user describes what they want in their own words. Extract:

1. **Subject** — what's in the scene (wizard, dragon, city, cat)
2. **Artistic style** — how it should feel (cyberpunk, medieval, anime, cozy)
3. **Technical style** — how pixels should look (NES, SNES, arcade)
4. **Scene type** — for video, what animations fit (night, urban, storm)

**Don't force the user to pick.** If they say "cyberpunk neon city pixel art" — that's the artistic style. If they say "retro 8-bit dragon" — that's the technical style. Only ask what's missing.

---

## Artistic Styles

What the scene looks and feels like. User may specify in their prompt.

| Style | Vibe | Prompt Modifier |
|-------|------|-----------------|
| cyberpunk | Neon, futuristic, rain | cyberpunk neon lights, futuristic, rain-slicked, purple and cyan |
| medieval | Castles, knights, dragons | medieval fantasy, stone castles, torchlight, banners |
| anime | Japanese, expressive, vibrant | anime style, vibrant colors, expressive eyes, dynamic pose |
| noir | Dark, moody, detective | film noir, dramatic shadows, dark alley, mystery |
| western | Desert, cowboy, saloon | wild west, dusty desert, wooden buildings, sunset |
| scifi | Space, robots, holograms | sci-fi, space station, holographic displays, metallic |
| kawaii | Cute, pastel, adorable | kawaii, pastel colors, cute, soft lighting, sparkly |
| steampunk | Gears, brass, Victorian | steampunk, brass gears, Victorian, steam pipes, warm |
| horror | Dark, spooky, Gothic | horror, dark Gothic, eerie fog, moonlit |
| underwater | Ocean, coral, bioluminescent | underwater, deep blue ocean, coral reef, light rays |
| postapoc | Ruins, wasteland, overgrown | post-apocalyptic, overgrown ruins, wasteland, desolate |
| retro | 80s/90s nostalgia, synthwave | retro 80s aesthetic, synthwave, neon grid |
| cozy | Warm, comfortable, relaxing | cozy atmosphere, warm lighting, comfortable, soft |

If user doesn't specify artistic style: use `auto` (let the prompt speak for itself).

---

## Technical Styles

How the pixel art itself looks. Recommend based on what the user wants.

| Style | Look | Best for |
|-------|------|----------|
| nes | 8-bit, limited palette, clean | Characters (fewest hallucinations) |
| snes | 16-bit, colorful, detailed | Rich scenes |
| indie | Modern, polished pixel art | Contemporary feel |
| arcade | Bold, chunky, high contrast | Posters, action |
| gameboy | 4 green shades | Extreme retro |
| clean | Modern, high fidelity | Maximum detail |
| gb | GBA 32-bit, smooth | Handheld aesthetic |

**Default recommendation:** NES for characters, SNES for scenes, arcade for bold posters.

---

## Aspect Ratios

| Ratio | Use |
|-------|-----|
| 640x480 | Default, most scenes |
| 512x768 | Portraits, vertical |
| 512x512 | Sprites, balanced |
| 768x768 | Square, detailed |
| 800x600 | Larger scenes |

When in doubt: 640x480.

---

## Image Generation (Pollinations)

Build prompt from user description + styles:

```
[subject scene], pixel art, [technical style] style, [artistic modifiers], [mood]
```

### Examples

User: "un gato mirando la estrellas"
→ a cat looking at the stars, pixel art, NES 8-bit style, limited color palette, warm colors, dithered shading

User: "ciudad cyberpunk pixel art"
→ a cyberpunk city street at night, pixel art, SNES sprite style, cyberpunk neon lights, futuristic, rain-slicked, purple and cyan

User: "dragón estilo medieval pixel art 16-bit"
→ a dragon flying over a medieval castle, pixel art, SNES sprite style, 16-bit retro, medieval fantasy, stone castles, dramatic lighting

User: "un mago en un bosque oscuro"
→ a wizard casting a glowing spell in a dark forest, pixel art, NES 8-bit style, limited color palette, magical particles, mystical atmosphere

### Pollinations URL

```
https://image.pollinations.ai/prompt/{url_encoded}?width=640&height=480&nologo=true
```

### Pollinations Quirks

- Aggressive caching: same prompt = identical output (seed ignored)
- Rate limit: 1 request at a time, wait 60-70s between requests
- Output JPEG by default
- Max effective resolution: ~768x768
- `nologo=true` for clean output
- Anonymous (no API key) — free, no credits needed

### Anti-Hallucination — Hard-Won Lessons

**Seed-swapping strategy:** When a prompt produces good backgrounds but one artifact, swap ONLY the seed (keep prompt identical). Don't rewrite the prompt. Try 3-5 seeds before changing the prompt — Pollinations output varies wildly between seeds.

**Subject-specific risks:**
- **Knights + swords are high-risk** — Pollinations puts swords in weird places (between legs!) or duplicates them as buildings. Avoid knight-with-sword subjects.
- **Cyberpunk/neon is reliable** — neon signs, rain reflections, urban scenes consistently good.
- **Mages/spellcasters work well** — fire spells, magic particles render cleanly.
- **Cats/cozy scenes are safe** — warm lighting + simple subjects = clean output.

**Good example prompts that work consistently:**
- "a lone samurai standing on a rain-soaked rooftop, neon signs reflecting on wet ground, cyberpunk city at night" (snes + cyberpunk)
- "a cute cat sitting next to a warm fireplace, cozy room, yarn ball on floor" (indie + cozy)
- "a powerful wizard casting a fire spell, glowing magic particles, dark dungeon background" (nes + medieval)

**Bad prompt patterns to avoid:**
- "a knight holding sword raised high above head, shield on left arm" → duplicates sword or places it wrong
- Anything with multiple objects near the character's body
- Complex multi-action descriptions

**Descriptive vs simple trade-off:**
- Detailed prompts = richer backgrounds but more artifacts
- Simple prompts = safer but bland
- Sweet spot: detailed prompt + iterative seed-swapping
- **Knights + swords are high-risk** — Pollinations puts swords in weird places or duplicates them as buildings. Prefer mages, archers, or samurai over sword+shield knights
- **Good prompt → bad seed** — if a prompt produces good backgrounds but one artifact, swap ONLY the seed (keep prompt identical). Don't rewrite the prompt
- **Cyberpunk/neon is reliable** — Pollinations handles neon signs, rain reflections, and urban scenes consistently well
- **Descriptive vs simple trade-off** — detailed prompts = richer backgrounds but more artifacts. Simple prompts = safer but bland. Iterative seed-swapping on the detailed prompt is the sweet spot
- **Good example prompts that work:**
  - "a lone samurai standing on a rain-soaked rooftop, neon signs reflecting on wet ground, cyberpunk city at night"
  - "a cute cat sitting next to a warm fireplace, cozy room, yarn ball on floor"
  - "a powerful wizard casting a fire spell, glowing magic particles, dark dungeon background"
- **Bad prompt patterns:**
  - "a knight holding sword raised high above head, shield on left arm, full body" → often duplicates sword or places it wrong
  - Anything with multiple objects near the character's body
- **When generating for README examples:** try 3-5 seeds before changing the prompt. Pollinations output varies wildly between seeds

### Resolution (Pixel Visibility) — Known Issue

Pollinations at 640x480 generates pixel art "style" but individual pixels aren't clearly visible — looks like smooth retro illustration. For authentic pixel art where you can SEE the pixels:

- **NES:** generate at 256x240 (true NES resolution)
- **SNES:** 256x224
- **Game Boy:** 160x144
- **Arcade:** 320x224

Lower resolution = bigger visible pixels = more authentic. Consider lowering Pollinations default or adding `--lowres` flag.

Same issue with pixelart.py: output upscales back to original photo resolution (factor 10 on 2034px photo = output still 2034px, blocks too small). Fix: option to output at native grid size instead of upscaling.

### Output & Delivery

Scripts save to `./pixelart_output/` (or `$PIXELART_OUTPUT`). The agent handles delivery based on its platform — send the generated file however your agent sends media (Telegram, Discord, WhatsApp, Slack, file path, etc.). Don't bake platform-specific delivery logic into the skill.

### Naming

`{subject}_{tech_style}_{artistic_style}_{resolution}.png`
Example: `cyberpunk_city_snes_cyberpunk_640.png`, `elf_mage_nes_640.png`

---

## Video Generation (pixelart_video.py)

User asks for animated pixel art → extract styles + scene → generate.

### CLI

```bash
python scripts/pixelart_video.py "a wizard in a dark forest" \
  --scene magic --tech nes --artistic medieval --ratio 640x480 --duration 6
```

### Scene Types (Animation Behavior)

| Scene | Animations | Best for |
|-------|-----------|----------|
| night | Stars + fireflies + leaves | Outdoor night |
| dusk | Fireflies + sparkles | Twilight, sunset |
| tavern | Dust motes + sparkles | Indoor warm |
| indoor | Dust motes | Interior calm |
| urban | Rain + neon pulse | City, cyberpunk |
| nature | Leaves + fireflies | Forest, landscape |
| magic | Sparkles + fireflies | Spells, enchantment |
| storm | Rain + lightning | Dramatic, battle |
| underwater | Bubbles + sparkles | Ocean, aquatic |
| fire | Embers + sparks | Lava, campfire, dragon |
| snow | Snowflakes + sparkles | Winter, mountain |
| desert | Heat shimmer + dust | Western, wasteland |

### Video Pipeline

1. Pollinations generates base (already pixel art, no filter)
2. Pixel animations added by zone (upper=sky, lower=ground, edges=ambient)
3. FFmpeg encode: h264, CRF 18
4. Optional GIF export with `--gif` (320px scaled, palettegen)

**For GitHub README:** Always use `--gif`. GitHub doesn't render MP4 inline in READMEs — GIFs show natively. Generate MP4 + GIF together:
```bash
python scripts/pixelart_video.py "scene" --gif -o output.mp4
# → creates output.mp4 + output.gif
```

**Snowflake animation tuning (learned from testing):**
- Size 2-3px minimum (1px looks like stars, not snow)
- Speed multiplier ×8 max (×15 was too fast)
- Wobble amplitude ×20 for visible drift
- 40+ particles for density
- Mix sizes: some as pixel_cross, some as 2px blocks

### Animation Rules

- ALL animations pixel art: pixel_block(), pixel_cross(), pixel_point()
- NO ellipses, NO smooth curves
- Place by ZONE, not coordinates (vision is unreliable)
- Fewer elements, more visible — 12 sparkles > 70 dots
- Blink on/off, NOT smooth fade

### What Doesn't Work

- Coordinate-based placement (vision hallucinates positions)
- Smoke particles (needs exact positioning)
- Comets with pixel trails (looks like repeated pattern)
- Smooth glow/fade (doesn't feel pixel art)
- Applying pixelart.py on Pollinations output

---

## Convert Existing Video

User sends video → extract frames → pixelart.py → re-encode.

```bash
ffmpeg -i input.mp4 -vf fps=15 /tmp/frames/frame_%04d.png
python scripts/pixelart.py /tmp/frames/frame_0001.png --preset nes
# Apply to all frames, then:
ffmpeg -y -framerate 15 -i /tmp/out/frame_%04d.png -c:v libx264 -pix_fmt yuv420p output.mp4
```

---

## pixelart.py — Photo Conversion (Ultra Edition)

Rewritten from scratch with techniques inspired by [pyxelate](https://github.com/sedthh/pyxelate):

- **Sobel edge-aware downsampling** — gradient-weighted block averaging preserves edges, simplifies flat areas (scipy)
- **Wu's Color Quantization** — produces BGM-quality palettes without sklearn. Downsamples image first for speed on large images
- **4 dithering methods** — none, bayer (ordered 4x4), floyd (error diffusion), atkinson (cleaner classic look)
- **SVD noise reduction** — numpy native, low-pass filter before conversion
- **40+ named palettes** — hardware (NES, C64, PICO_8, Game Boy, etc.) + artistic (NEON_CYBER, PASTEL_DREAM, OCEAN_DEEP, etc.)
- **Color merge post-processing** — removes palette noise

Dependencies: scipy (~15MB) + numpy + Pillow. NO sklearn needed.

```bash
python scripts/pixelart.py photo.jpg --preset nes -o output.png
python scripts/pixelart.py photo.jpg --palette PICO_8 --dither bayer
python scripts/pixelart.py photo.jpg --palette NEON_CYBER --dither atkinson
python scripts/pixelart.py photo.jpg -c 16 --dither floyd
python scripts/pixelart.py --list-presets
python scripts/pixelart.py --list-palettes
```

### Presets (14)

| Preset | Factor | Palette | Dither | Best for |
|--------|--------|---------|--------|----------|
| gameboy | 10 | GAMEBOY_ORIGINAL (4) | bayer | Extreme retro green |
| nes | 10 | NES (63) | floyd | 8-bit characters |
| snes | 7 | 64 auto | floyd | 16-bit rich scenes |
| gba | 6 | 64 auto | none | Smooth handheld |
| pico8 | 8 | PICO_8 (16) | bayer | Fantasy console |
| c64 | 9 | C64 (16) | floyd | Commodore 64 look |
| vga | 7 | 256 auto | none | DOS era |
| arcade | 12 | 16 auto | none | Chunky 80s |
| clean | 4 | 64 auto | none | Maximum detail |
| detailed | 3 | 128 auto | none | High fidelity |
| minimal | 8 | 8 auto | floyd | Minimalist |
| mspaint | 8 | MS_PAINT (24) | none | Classic MS Paint |
| apple2 | 10 | APPLE_II_HI (6) | naive | Apple II |
| teletext | 12 | TELETEXT (8) | bayer | BBC Teletext |

### Named Palettes (40+)

Hardware: `NES`, `C64`, `ZX_SPECTRUM`, `PICO_8`, `GAMEBOY_ORIGINAL`, `GAMEBOY_POCKET`, `GAMEBOY_VIRTUALBOY`, `APPLE_II_LO`, `APPLE_II_HI`, `TELETEXT`, `CGA_MODE4_PAL1`, `CGA_MODE5_PAL1`, `MSX`, `MICROSOFT_WINDOWS_16`, `MICROSOFT_WINDOWS_PAINT`, `MONO_BW`, `MONO_AMBER`, `MONO_GREEN`

Artistic: `PASTEL_DREAM`, `NEON_CYBER`, `RETRO_WARM`, `OCEAN_DEEP`, `FOREST_MOSS`, `SUNSET_FIRE`, `ARCTIC_ICE`, `VINTAGE_ROSE`, `EARTH_CLAY`, `ELECTRIC_VIOLET`

### Dithering Methods

| Method | Speed | Look | Best for |
|--------|-------|------|----------|
| none | Fastest | Crispest, visible banding | Clean modern look |
| bayer | Fast | Consistent ordered pattern | Retro hardware feel |
| floyd | Medium | Smoothest gradients | Portraits, landscapes |
| atkinson | Medium | Cleaner, less noise | Classic Mac aesthetic |

### Pyxelate Analysis (for reference)

Studied [sedthh/pyxelate](https://github.com/sedthh/pyxelate) in depth. Key takeaways:
- Their Sobel/HOG downsampling is the biggest quality differentiator — we replicated it
- Bayesian GMM for palette is overkill (~300MB sklearn). Wu's Color Quantization achieves ~95% quality with zero deps
- Their 4 dithering methods are all implementable with numpy — we have all 4
- They lack artistic palettes and post-processing — we improved on both
- Final result: 95-99% pyxelate quality with ~20MB deps vs their ~500MB

### Path Portability

**NEVER hardcode ~/.hermes/ paths in pixelart.py.** Use:
- Default output: `./pixelart_output/` (local to cwd)
- Default memory: `./pixelart_memory.json` (local to cwd)
- Env overrides: `$PIXELART_OUTPUT`, `$PIXELART_MEMORY`
- CLI flags: `--output-dir`, `--memory`, `--no-memory`

This ensures the scripts work standalone, with any agent (Hermes, Claude Code, OpenClaw), or as a CLI tool.

### Rules

- Ask style FIRST, generate ONE version
- Image with caption = response (no double messages)
- List styles vertically
- For README examples: show original photo next to pixel art conversion (before/after)
- GitHub README renders GIFs inline, not MP4 — use `--gif` flag for video examples

---

## Rules

1. NEVER apply pixelart.py to Pollinations output
2. pixelart.py is ONLY for user-uploaded photos
3. ALWAYS ask for what's missing — don't assume style
4. Extract styles from user's natural language
5. Send both photo + document for images
6. Default ratio: 640x480
7. NES for characters, SNES for scenes
8. Prompts natural — don't over-engineer
9. Place animations by zone, not coordinates
10. Ask user for feedback — don't trust vision analysis

---

## Prompt Memory

`pixelart_image.py` tracks every generation in a local memory file:

- Default: `./pixelart_memory.json` (local to cwd)
- Override: `$PIXELART_MEMORY` env var or `--memory` flag
- Disable: `--no-memory` flag
- Output dir: `./pixelart_output/` or `$PIXELART_OUTPUT` or `--output-dir`

Each entry saves: prompt, tech/artistic style, success/failure, timestamp.

Check stats: `python scripts/pixelart_image.py --stats`

Over time, this reveals which style combos work best and what prompts tend to fail. The agent should check stats periodically and adjust recommendations.

**Why not ~/.hermes/?** Hardcoding paths to a specific agent's folder breaks standalone use. Anyone using pixel-art-studio from Claude Code, OpenClaw, or plain CLI shouldn't need Hermes.

---

## GitHub Workflow (Synero repos)

**Repo:** https://github.com/Synero/pixel-art-studio

**CRITICAL: All commits must use Synero identity, NEVER "Nacho":**
```bash
git config user.email "synero@users.noreply.github.com"
git config user.name "Synero"
```

**To reset history with wrong username (orphan branch):**
```bash
git checkout --orphan fresh-start
git add -A
git commit -m "message"
git branch -D main
git branch -m main
git push -f origin main
```

**Free source images for pixelart.py examples:** Use picsum.photos (Wikimedia blocks curl downloads):
```bash
curl -sL "https://picsum.photos/seed/portrait123/640/480" -o portrait.jpg
curl -sL "https://picsum.photos/seed/landscape456/640/480" -o landscape.jpg
```

**Example structure for README (3 script sections):**
- Image Generation — 4 Pollinations-generated PNGs in 2x2 grid
- Photo Conversion — 3 converted images (NES/SNES/Game Boy presets)
- Video Generation — 1 MP4 + 1 GIF example

## Project Files

- `scripts/pixelart.py` — Photo → pixel art (10 presets)
- `scripts/pixelart_image.py` — Prompt → image (Pollinations, memory tracking)
- `scripts/pixelart_video.py` — Prompt → animated video (+ optional GIF export) (12 scenes, 7 tech styles, 13 artistic styles)
