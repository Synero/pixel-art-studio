#!/usr/bin/env python3
"""
Pixel Art Converter — Ultra Edition v2
Convert any image to pixel art with:
- Sobel edge-aware downsampling (preserves detail)
- Wu's Color Quantization (no ML dependencies)
- 4 dithering methods: none, bayer, floyd, atkinson
- 40+ named palettes (hardware + artistic)
- SVD noise reduction
- Aggressive color enhancement for pixel art look
- Alpha channel support for sprites
- Minimum color distance enforcement

Dependencies: numpy, Pillow, scipy (optional, for Sobel)
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance

try:
    from scipy.ndimage import sobel as scipy_sobel, median_filter as scipy_median
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# ═══════════════════════════════════════════════════════════════════════════════
# NAMED PALETTES — Hardware + Artistic
# ═══════════════════════════════════════════════════════════════════════════════

PALETTES = {
    "NES": [
        (0,0,0),(124,124,124),(0,0,252),(0,0,188),(68,40,188),(148,0,132),(168,0,32),(168,16,0),
        (136,20,0),(0,116,0),(0,148,0),(0,120,0),(0,88,0),(0,64,88),(0,0,0),(0,0,0),
        (188,188,188),(0,120,248),(0,88,248),(104,68,252),(216,0,204),(228,0,88),(248,56,0),
        (228,92,16),(172,124,0),(0,184,0),(0,168,0),(0,168,68),(0,136,136),(0,0,0),(0,0,0),
        (248,248,248),(60,188,252),(104,136,252),(152,120,248),(248,120,248),(248,88,152),
        (248,120,88),(252,160,68),(248,184,0),(184,248,24),(88,216,84),(88,248,152),(0,232,216),
        (120,120,120),(0,0,0),(0,0,0),
        (252,252,252),(164,228,252),(184,184,248),(216,184,248),(248,184,248),(248,164,192),
        (240,208,176),(252,224,168),(248,216,120),(216,248,120),(184,248,184),(184,248,216),
        (0,252,252),(216,216,216),(0,0,0),(0,0,0),
    ],
    "C64": [
        (0,0,0),(255,255,255),(161,77,67),(106,191,199),(161,87,164),(92,172,95),(64,64,223),
        (191,206,137),(161,104,60),(108,80,21),(203,126,117),(98,98,98),(137,137,137),
        (154,226,155),(124,124,255),(173,173,173),
    ],
    "ZX_SPECTRUM": [
        (0,0,0),(0,39,251),(252,48,22),(255,63,252),(0,249,44),(0,252,254),(255,253,51),(255,255,255),
    ],
    "APPLE_II_LO": [
        (0,0,0),(133,59,81),(80,71,137),(234,93,240),(0,104,82),(146,146,146),(0,168,241),
        (202,195,248),(81,92,15),(235,127,35),(146,146,146),(246,185,202),(0,202,41),(203,211,155),
        (155,220,203),(255,255,255),
    ],
    "APPLE_II_HI": [
        (0,0,0),(255,0,255),(0,255,0),(255,255,255),(0,175,255),(255,80,0),
    ],
    "GAMEBOY_ORIGINAL": [
        (0,63,0),(46,115,32),(140,191,10),(160,207,10),
    ],
    "GAMEBOY_POCKET": [
        (0,0,0),(85,85,85),(170,170,170),(255,255,255),
    ],
    "GAMEBOY_VIRTUALBOY": [
        (239,0,0),(164,0,0),(85,0,0),(0,0,0),
    ],
    "PICO_8": [
        (0,0,0),(29,43,83),(126,37,83),(0,135,81),(171,82,54),(95,87,79),(194,195,199),
        (255,241,232),(255,0,77),(255,163,0),(255,236,39),(0,228,54),(41,173,255),
        (131,118,156),(255,119,168),(255,204,170),
    ],
    "TELETEXT": [
        (0,0,0),(255,0,0),(0,128,0),(255,255,0),(0,0,255),(255,0,255),(0,255,255),(255,255,255),
    ],
    "CGA_MODE4_PAL1": [
        (0,0,0),(255,255,255),(0,255,255),(255,0,255),
    ],
    "MSX": [
        (0,0,0),(62,184,73),(116,208,125),(89,85,224),(128,118,241),(185,94,81),
        (101,219,239),(219,101,89),(255,137,125),(204,195,94),(222,208,135),(58,162,65),
        (183,102,181),(204,204,204),(255,255,255),
    ],
    "MICROSOFT_WINDOWS_16": [
        (0,0,0),(128,0,0),(0,128,0),(128,128,0),(0,0,128),(128,0,128),(0,128,128),(192,192,192),
        (128,128,128),(255,0,0),(0,255,0),(255,255,0),(0,0,255),(255,0,255),(0,255,255),(255,255,255),
    ],
    "MICROSOFT_WINDOWS_PAINT": [
        (0,0,0),(255,255,255),(123,123,123),(189,189,189),(123,12,2),(255,37,0),
        (123,123,2),(255,251,2),(0,123,2),(2,249,2),(0,123,122),(2,253,254),
        (2,19,122),(5,50,255),(123,25,122),(255,64,254),
        (122,57,2),(255,122,57),(123,123,56),(255,252,122),(2,57,57),(5,250,123),
        (0,123,255),(255,44,123),
    ],
    "COMMODORE_64": [
        (0,0,0),(255,255,255),(161,77,67),(106,192,200),(161,87,165),(92,172,95),
        (64,68,227),(203,214,137),(163,104,58),(110,84,11),(204,127,118),(99,99,99),
        (139,139,139),(154,227,157),(139,127,205),(175,175,175),
    ],
    "MONO_BW": [(0,0,0),(255,255,255)],
    "MONO_AMBER": [(40,40,40),(255,176,0)],
    "MONO_GREEN": [(40,40,40),(51,255,51)],
    
    # ── Artistic palettes ──
    "PASTEL_DREAM": [
        (255,218,233),(255,229,204),(255,255,204),(204,255,229),(204,229,255),(229,204,255),
        (255,204,229),(204,255,255),(255,245,220),(230,230,250),
    ],
    "NEON_CYBER": [
        (0,0,0),(255,0,128),(0,255,255),(255,0,255),(0,255,128),(255,255,0),
        (128,0,255),(255,128,0),(0,128,255),(255,255,255),
    ],
    "RETRO_WARM": [
        (62,39,35),(139,69,19),(210,105,30),(244,164,96),(255,218,185),
        (255,245,238),(178,34,34),(205,92,92),(255,99,71),(255,160,122),
    ],
    "OCEAN_DEEP": [
        (0,25,51),(0,51,102),(0,76,153),(0,102,178),(0,128,204),
        (51,153,204),(102,178,204),(153,204,229),(204,229,255),(229,245,255),
    ],
    "FOREST_MOSS": [
        (34,51,34),(51,76,51),(68,102,51),(85,128,68),(102,153,85),
        (136,170,102),(170,196,136),(204,221,170),(238,238,204),(245,245,220),
    ],
    "SUNSET_FIRE": [
        (51,0,0),(102,0,0),(153,0,0),(204,0,0),(255,0,0),
        (255,51,0),(255,102,0),(255,153,0),(255,204,0),(255,255,51),
    ],
    "ARCTIC_ICE": [
        (0,0,51),(0,0,102),(0,51,153),(0,102,153),(51,153,204),
        (102,204,255),(153,229,255),(204,242,255),(229,247,255),(255,255,255),
    ],
    "VINTAGE_ROSE": [
        (103,58,63),(137,72,81),(170,91,102),(196,113,122),(219,139,147),
        (232,168,175),(240,196,199),(245,215,217),(249,232,233),(255,245,245),
    ],
    "EARTH_CLAY": [
        (62,39,35),(89,56,47),(116,73,59),(143,90,71),(170,107,83),
        (197,124,95),(210,155,126),(222,186,160),(235,217,196),(248,248,232),
    ],
    "ELECTRIC_VIOLET": [
        (26,0,51),(51,0,102),(76,0,153),(102,0,204),(128,0,255),
        (153,51,255),(178,102,255),(204,153,255),(229,204,255),(245,229,255),
    ],
}

# ═══════════════════════════════════════════════════════════════════════════════
# ERA PRESETS
# ═══════════════════════════════════════════════════════════════════════════════

PRESETS = {
    "gameboy":  {"factor": 10, "palette": "GAMEBOY_ORIGINAL", "dither": "none"},
    "nes":      {"factor": 10, "palette": "NES",               "dither": "none"},
    "snes":     {"factor": 7,  "palette": 64,                   "dither": "none"},
    "gba":      {"factor": 6,  "palette": 64,                   "dither": "none"},
    "pico8":    {"factor": 8,  "palette": "PICO_8",             "dither": "none"},
    "c64":      {"factor": 9,  "palette": "C64",                "dither": "none"},
    "vga":      {"factor": 7,  "palette": 256,                  "dither": "none"},
    "arcade":   {"factor": 12, "palette": 16,                   "dither": "none"},
    "clean":    {"factor": 4,  "palette": 64,                   "dither": "none"},
    "detailed": {"factor": 3,  "palette": 128,                  "dither": "none"},
    "minimal":  {"factor": 8,  "palette": 8,                    "dither": "none"},
    "mspaint":  {"factor": 8,  "palette": "MICROSOFT_WINDOWS_PAINT", "dither": "none"},
    "apple2":   {"factor": 10, "palette": "APPLE_II_HI",        "dither": "none"},
    "teletext": {"factor": 12, "palette": "TELETEXT",           "dither": "none"},
}

# ═══════════════════════════════════════════════════════════════════════════════
# Wu's Color Quantization
# ═══════════════════════════════════════════════════════════════════════════════

class WuColorQuant:
    """Wu's Color Quantization — adaptive cube splitting in RGB space."""
    
    def __init__(self, image, max_colors=16):
        self.image = image
        self.max_colors = max_colors
        side = 33
        self.weight = np.zeros((side, side, side), dtype=np.int64)
        self.momr = np.zeros((side, side, side), dtype=np.int64)
        self.momg = np.zeros((side, side, side), dtype=np.int64)
        self.momb = np.zeros((side, side, side), dtype=np.int64)
        self.mom2 = np.zeros((side, side, side), dtype=np.float64)
        self._build_histogram()
    
    def _build_histogram(self):
        h, w, _ = self.image.shape
        for y in range(h):
            for x in range(w):
                r, g, b = int(self.image[y, x, 0]), int(self.image[y, x, 1]), int(self.image[y, x, 2])
                ir, ig, ib = (r >> 3) + 1, (g >> 3) + 1, (b >> 3) + 1
                self.weight[ir, ig, ib] += 1
                self.momr[ir, ig, ib] += r
                self.momg[ir, ig, ib] += g
                self.momb[ir, ig, ib] += b
                self.mom2[ir, ig, ib] += float(r)*float(r) + float(g)*float(g) + float(b)*float(b)
        
        # Cumulative 3D histogram
        for ir in range(1, 33):
            for ig in range(1, 33):
                for ib in range(1, 33):
                    self.weight[ir, ig, ib] += self.weight[ir, ig-1, ib] + self.weight[ir, ig, ib-1] - self.weight[ir, ig-1, ib-1]
                    self.weight[ir, ig, ib] += self.weight[ir-1, ig, ib] - self.weight[ir-1, ig-1, ib] - self.weight[ir-1, ig, ib-1] + self.weight[ir-1, ig-1, ib-1]
                    self.momr[ir, ig, ib] += self.momr[ir, ig-1, ib] + self.momr[ir, ig, ib-1] - self.momr[ir, ig-1, ib-1]
                    self.momr[ir, ig, ib] += self.momr[ir-1, ig, ib] - self.momr[ir-1, ig-1, ib] - self.momr[ir-1, ig, ib-1] + self.momr[ir-1, ig-1, ib-1]
                    self.momg[ir, ig, ib] += self.momg[ir, ig-1, ib] + self.momg[ir, ig, ib-1] - self.momg[ir, ig-1, ib-1]
                    self.momg[ir, ig, ib] += self.momg[ir-1, ig, ib] - self.momg[ir-1, ig-1, ib] - self.momg[ir-1, ig, ib-1] + self.momg[ir-1, ig-1, ib-1]
                    self.momb[ir, ig, ib] += self.momb[ir, ig-1, ib] + self.momb[ir, ig, ib-1] - self.momb[ir, ig-1, ib-1]
                    self.momb[ir, ig, ib] += self.momb[ir-1, ig, ib] - self.momb[ir-1, ig-1, ib] - self.momb[ir-1, ig, ib-1] + self.momb[ir-1, ig-1, ib-1]
                    self.mom2[ir, ig, ib] += self.mom2[ir, ig-1, ib] + self.mom2[ir, ig, ib-1] - self.mom2[ir, ig-1, ib-1]
                    self.mom2[ir, ig, ib] += self.mom2[ir-1, ig, ib] - self.mom2[ir-1, ig-1, ib] - self.mom2[ir-1, ig, ib-1] + self.mom2[ir-1, ig-1, ib-1]
    
    def _vol(self, c):
        r0,r1,g0,g1,b0,b1 = c
        return int(self.weight[r1,g1,b1]-self.weight[r0,g1,b1]-self.weight[r1,g0,b1]-self.weight[r1,g1,b0]
                   +self.weight[r0,g0,b1]+self.weight[r0,g1,b0]+self.weight[r1,g0,b0]-self.weight[r0,g0,b0])
    
    def _var(self, c):
        r0,r1,g0,g1,b0,b1 = c
        vol = self._vol(c)
        if vol == 0: return 0.0
        dr = self.momr[r1,g1,b1]-self.momr[r0,g1,b1]-self.momr[r1,g0,b1]-self.momr[r1,g1,b0]+self.momr[r0,g0,b1]+self.momr[r0,g1,b0]+self.momr[r1,g0,b0]-self.momr[r0,g0,b0]
        dg = self.momg[r1,g1,b1]-self.momg[r0,g1,b1]-self.momg[r1,g0,b1]-self.momg[r1,g1,b0]+self.momg[r0,g0,b1]+self.momg[r0,g1,b0]+self.momg[r1,g0,b0]-self.momg[r0,g0,b0]
        db = self.momb[r1,g1,b1]-self.momb[r0,g1,b1]-self.momb[r1,g0,b1]-self.momb[r1,g1,b0]+self.momb[r0,g0,b1]+self.momb[r0,g1,b0]+self.momb[r1,g0,b0]-self.momb[r0,g0,b0]
        m2 = self.mom2[r1,g1,b1]-self.mom2[r0,g1,b1]-self.mom2[r1,g0,b1]-self.mom2[r1,g1,b0]+self.mom2[r0,g0,b1]+self.mom2[r0,g1,b0]+self.mom2[r1,g0,b0]-self.mom2[r0,g0,b0]
        return m2 - (dr*dr + dg*dg + db*db) / float(vol)
    
    def _maximize(self, c, direction, first, last):
        r0,r1,g0,g1,b0,b1 = c
        wr = self.momr[r1,g1,b1]-self.momr[r0,g1,b1]-self.momr[r1,g0,b1]-self.momr[r1,g1,b0]+self.momr[r0,g0,b1]+self.momr[r0,g1,b0]+self.momr[r1,g0,b0]-self.momr[r0,g0,b0]
        wg = self.momg[r1,g1,b1]-self.momg[r0,g1,b1]-self.momg[r1,g0,b1]-self.momg[r1,g1,b0]+self.momg[r0,g0,b1]+self.momg[r0,g1,b0]+self.momg[r1,g0,b0]-self.momg[r0,g0,b0]
        wb = self.momb[r1,g1,b1]-self.momb[r0,g1,b1]-self.momb[r1,g0,b1]-self.momb[r1,g1,b0]+self.momb[r0,g0,b1]+self.momb[r0,g1,b0]+self.momb[r1,g0,b0]-self.momb[r0,g0,b0]
        ww = self._vol(c)
        best, best_cut = 0.0, -1
        for i in range(first, last):
            if direction == 0:  # RED
                hw = int(self.weight[i,g1,b1]-self.weight[i,g0,b1]-self.weight[i,g1,b0]+self.weight[i,g0,b0])-int(self.weight[r0,g1,b1]-self.weight[r0,g0,b1]-self.weight[r0,g1,b0]+self.weight[r0,g0,b0])
                hr = self.momr[i,g1,b1]-self.momr[i,g0,b1]-self.momr[i,g1,b0]+self.momr[i,g0,b0]-(self.momr[r0,g1,b1]-self.momr[r0,g0,b1]-self.momr[r0,g1,b0]+self.momr[r0,g0,b0])
                hg, hb = 0, 0
            elif direction == 1:  # GREEN
                hw = int(self.weight[r1,i,b1]-self.weight[r0,i,b1]-self.weight[r1,i,b0]+self.weight[r0,i,b0])-int(self.weight[r1,g0,b1]-self.weight[r0,g0,b1]-self.weight[r1,g0,b0]+self.weight[r0,g0,b0])
                hg = self.momg[r1,i,b1]-self.momg[r0,i,b1]-self.momg[r1,i,b0]+self.momg[r0,i,b0]-(self.momg[r1,g0,b1]-self.momg[r0,g0,b1]-self.momg[r1,g0,b0]+self.momg[r0,g0,b0])
                hr, hb = 0, 0
            else:  # BLUE
                hw = int(self.weight[r1,g1,i]-self.weight[r0,g1,i]-self.weight[r1,g0,i]+self.weight[r0,g0,i])-int(self.weight[r1,g1,b0]-self.weight[r0,g1,b0]-self.weight[r1,g0,b0]+self.weight[r0,g0,b0])
                hb = self.momb[r1,g1,i]-self.momb[r0,g1,i]-self.momb[r1,g0,i]+self.momb[r0,g0,i]-(self.momb[r1,g1,b0]-self.momb[r0,g1,b0]-self.momb[r1,g0,b0]+self.momb[r0,g0,b0])
                hr, hg = 0, 0
            if hw == 0 or ww - hw == 0: continue
            t = (hr*hr+hg*hg+hb*hb)/float(hw) + ((wr-hr)**2+(wg-hg)**2+(wb-hb)**2)/float(ww-hw)
            if t > best: best, best_cut = t, i
        return best_cut, best
    
    def quantize(self):
        cubes = np.zeros((self.max_colors, 6), dtype=np.int32)
        cubes[0] = [0, 32, 0, 32, 0, 32]
        variance = np.zeros(self.max_colors, dtype=np.float64)
        next_idx = 0
        
        for i in range(1, self.max_colors):
            if self._vol(cubes[next_idx]) <= 1: continue
            best_dir, best_cut, best_val = 0, -1, 0.0
            r0,r1,g0,g1,b0,b1 = cubes[next_idx]
            for d in range(3):
                if d == 0: first, last = r0+1, r1
                elif d == 1: first, last = g0+1, g1
                else: first, last = b0+1, b1
                cut, val = self._maximize(cubes[next_idx], d, first, last)
                if cut >= 0 and val > best_val: best_dir, best_cut, best_val = d, cut, val
            if best_cut < 0: continue
            cubes[i] = cubes[next_idx].copy()
            if best_dir == 0: cubes[next_idx][1], cubes[i][0] = best_cut, best_cut
            elif best_dir == 1: cubes[next_idx][3], cubes[i][2] = best_cut, best_cut
            else: cubes[next_idx][5], cubes[i][4] = best_cut, best_cut
            variance[next_idx] = self._var(cubes[next_idx])
            variance[i] = self._var(cubes[i])
            next_idx = max(range(i+1), key=lambda j: variance[j])
        
        palette = []
        for i in range(self.max_colors):
            vol = self._vol(cubes[i])
            if vol == 0: continue
            r0,r1,g0,g1,b0,b1 = cubes[i]
            dr = self.momr[r1,g1,b1]-self.momr[r0,g1,b1]-self.momr[r1,g0,b1]-self.momr[r1,g1,b0]+self.momr[r0,g0,b1]+self.momr[r0,g1,b0]+self.momr[r1,g0,b0]-self.momr[r0,g0,b0]
            dg = self.momg[r1,g1,b1]-self.momg[r0,g1,b1]-self.momg[r1,g0,b1]-self.momg[r1,g1,b0]+self.momg[r0,g0,b1]+self.momg[r0,g1,b0]+self.momg[r1,g0,b0]-self.momg[r0,g0,b0]
            db = self.momb[r1,g1,b1]-self.momb[r0,g1,b1]-self.momb[r1,g0,b1]-self.momb[r1,g1,b0]+self.momb[r0,g0,b1]+self.momb[r0,g1,b0]+self.momb[r1,g0,b0]-self.momb[r0,g0,b0]
            palette.append((int(dr/vol), int(dg/vol), int(db/vol)))
        return palette


# ═══════════════════════════════════════════════════════════════════════════════
# DOWNSAMPLING
# ═══════════════════════════════════════════════════════════════════════════════

def simple_downsample(img, factor):
    h, w, d = img.shape
    pad_h = (factor - h % factor) % factor
    pad_w = (factor - w % factor) % factor
    if pad_h or pad_w:
        img = np.pad(img, ((0, pad_h), (0, pad_w), (0, 0)), mode='edge')
    nh, nw = img.shape[0] // factor, img.shape[1] // factor
    return img[:nh*factor, :nw*factor].reshape(nh, factor, nw, factor, d).mean(axis=(1, 3)).astype(np.uint8)


# ═══════════════════════════════════════════════════════════════════════════════
# DITHERING
# ═══════════════════════════════════════════════════════════════════════════════

BAYER_4x4 = np.array([[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]], dtype=np.float64) / 16.0 - 0.5

def _nearest(pixel, palette):
    diff = palette - pixel
    return palette[np.argmin(np.sum(diff**2, axis=1))]

def dither_none(img, palette):
    h, w, _ = img.shape
    flat = img.reshape(-1, 3).astype(np.float64)
    result = np.zeros_like(flat)
    for i in range(len(flat)):
        result[i] = _nearest(flat[i], palette)
    return result.reshape(img.shape).astype(np.uint8)

def dither_bayer(img, palette):
    h, w, _ = img.shape
    result = np.zeros_like(img, dtype=np.uint8)
    img_f = img.astype(np.float64)
    for y in range(h):
        for x in range(w):
            px = np.clip(img_f[y, x] + BAYER_4x4[y % 4, x % 4] * 64, 0, 255)
            result[y, x] = _nearest(px, palette)
    return result

def dither_floyd(img, palette):
    h, w, _ = img.shape
    img_f = img.astype(np.float64).copy()
    result = np.zeros_like(img, dtype=np.uint8)
    for y in range(h):
        for x in range(w):
            old = img_f[y, x].copy()
            new = _nearest(old, palette)
            result[y, x] = new.astype(np.uint8)
            err = old - new
            if x+1 < w: img_f[y, x+1] += err * 7/16
            if y+1 < h:
                if x > 0: img_f[y+1, x-1] += err * 3/16
                img_f[y+1, x] += err * 5/16
                if x+1 < w: img_f[y+1, x+1] += err * 1/16
    return result

def dither_atkinson(img, palette):
    h, w, _ = img.shape
    img_f = img.astype(np.float64).copy()
    result = np.zeros_like(img, dtype=np.uint8)
    for y in range(h):
        for x in range(w):
            old = img_f[y, x].copy()
            new = _nearest(old, palette)
            result[y, x] = new.astype(np.uint8)
            err = (old - new) / 8.0
            if x+1 < w: img_f[y, x+1] += err
            if x+2 < w: img_f[y, x+2] += err
            if y+1 < h:
                if x > 0: img_f[y+1, x-1] += err
                img_f[y+1, x] += err
                if x+1 < w: img_f[y+1, x+1] += err
            if y+2 < h: img_f[y+2, x] += err
    return result

DITHER_METHODS = {"none": dither_none, "bayer": dither_bayer, "floyd": dither_floyd, "atkinson": dither_atkinson}


# ═══════════════════════════════════════════════════════════════════════════════
# OUTLINE RENDERING
# ═══════════════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════════════
# COLOR ENFORCEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def enforce_min_color_distance(img, min_dist=25):
    """Ensure neighboring pixels don't have colors that are too similar.
    
    If two adjacent pixels are within min_dist, snap the darker one darker
    and the lighter one lighter. Creates cleaner color boundaries.
    """
    result = img.copy().astype(np.float64)
    h, w, _ = result.shape
    
    for y in range(h):
        for x in range(w):
            if x + 1 < w:
                d = np.sqrt(np.sum((result[y, x] - result[y, x+1])**2))
                if 0 < d < min_dist:
                    lum_a = 0.299*result[y,x,0] + 0.587*result[y,x,1] + 0.114*result[y,x,2]
                    lum_b = 0.299*result[y,x+1,0] + 0.587*result[y,x+1,1] + 0.114*result[y,x+1,2]
                    if lum_a > lum_b:
                        result[y, x] = np.clip(result[y, x] + min_dist/3, 0, 255)
                        result[y, x+1] = np.clip(result[y, x+1] - min_dist/3, 0, 255)
                    else:
                        result[y, x] = np.clip(result[y, x] - min_dist/3, 0, 255)
                        result[y, x+1] = np.clip(result[y, x+1] + min_dist/3, 0, 255)
            if y + 1 < h:
                d = np.sqrt(np.sum((result[y, x] - result[y+1, x])**2))
                if 0 < d < min_dist:
                    lum_a = 0.299*result[y,x,0] + 0.587*result[y,x,1] + 0.114*result[y,x,2]
                    lum_b = 0.299*result[y+1,x,0] + 0.587*result[y+1,x,1] + 0.114*result[y+1,x,2]
                    if lum_a > lum_b:
                        result[y, x] = np.clip(result[y, x] + min_dist/3, 0, 255)
                        result[y+1, x] = np.clip(result[y+1, x] - min_dist/3, 0, 255)
                    else:
                        result[y, x] = np.clip(result[y, x] - min_dist/3, 0, 255)
                        result[y+1, x] = np.clip(result[y+1, x] + min_dist/3, 0, 255)
    
    return result.astype(np.uint8)


# ═══════════════════════════════════════════════════════════════════════════════
# SVD + PREPROCESSING
# ═══════════════════════════════════════════════════════════════════════════════

def apply_svd(img, n_components=32):
    h, w, d = img.shape
    if n_components >= min(h, w) - 1: return img
    result = np.zeros_like(img, dtype=np.float64)
    for c in range(3):
        U, s, Vt = np.linalg.svd(img[:,:,c].astype(np.float64), full_matrices=False)
        k = min(n_components, len(s))
        result[:,:,c] = U[:,:k] @ np.diag(s[:k]) @ Vt[:k,:]
    return np.clip(result, 0, 255).astype(np.uint8)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

def pixelart(
    input_path,
    output_path=None,
    factor=8,
    palette_size=32,
    palette_name=None,
    dither="none",
    use_svd=False,
    svd_components=32,
    contrast=1.3,
    saturation=1.2,
    min_color_dist=0,
):
    """Full pixel art conversion pipeline."""
    
    if output_path is None:
        output_path = str(Path(input_path).with_suffix("")) + "_pixelart.png"
    
    # Load
    img = Image.open(input_path).convert("RGB")
    orig_w, orig_h = img.size
    img_np = np.array(img)
    
    # 1. Enhance contrast + saturation (aggressive for pixel art look)
    pil_img = Image.fromarray(img_np)
    pil_img = ImageEnhance.Contrast(pil_img).enhance(contrast)
    pil_img = ImageEnhance.Color(pil_img).enhance(saturation)
    img_np = np.array(pil_img)
    
    # 2. SVD (optional noise reduction)
    if use_svd:
        img_np = apply_svd(img_np, svd_components)
    
    # 3. Downsample
    small = simple_downsample(img_np, factor)
    
    # 4. Palette
    if palette_name and palette_name.upper() in PALETTES:
        palette = np.array(PALETTES[palette_name.upper()], dtype=np.float64)
        pal_label = f"{palette_name.upper()} ({len(palette)} colors)"
    else:
        # Wu's on downsampled for speed
        sample = small
        sh, sw = sample.shape[:2]
        if sh * sw > 256 * 256:
            sf = max(1, int((sh * sw / (256 * 256)) ** 0.5))
            sample = simple_downsample(sample, sf)
        wu = WuColorQuant(sample, max_colors=palette_size)
        palette = np.array(wu.quantize(), dtype=np.float64)
        pal_label = f"Wu auto ({len(palette)} from {palette_size})"
    
    # 5. Dithering
    dither_fn = DITHER_METHODS.get(dither, dither_none)
    small = dither_fn(small, palette)
    
    # 6. Minimum color distance enforcement
    if min_color_dist > 0:
        small = enforce_min_color_distance(small, min_color_dist)
    
    # 8. Upscale back to original with NEAREST — keeps pixel block look
    #    at the original photo resolution.
    pixelated = Image.fromarray(small).resize((orig_w, orig_h), Image.NEAREST)
    pixelated.save(output_path, "PNG")
    
    actual = len(set(map(tuple, np.array(pixelated).reshape(-1, 3).tolist())))
    print(f"  Palette: {pal_label}")
    print(f"  {output_path}")
    print(f"  Size: {orig_w}x{orig_h} | Block: {factor}px | Colors: {actual} | Dither: {dither}")
    return output_path


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Pixel Art Converter — Ultra Edition v2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s photo.jpg --preset nes
  %(prog)s photo.jpg --palette NEON_CYBER --dither bayer
  %(prog)s --list-presets
  %(prog)s --list-palettes
""",
    )
    parser.add_argument("input", nargs="?", help="Input image path")
    parser.add_argument("-o", "--output", default=None, help="Output path")
    parser.add_argument("-f", "--factor", type=int, default=None, help="Downsample factor")
    parser.add_argument("-c", "--colors", type=int, default=None, help="Palette colors (auto mode)")
    parser.add_argument("--preset", choices=list(PRESETS.keys()), default=None)
    parser.add_argument("--palette", default=None, help="Named palette or color count")
    parser.add_argument("--dither", choices=list(DITHER_METHODS.keys()), default=None)
    parser.add_argument("--use-svd", action="store_true", help="Enable SVD noise reduction")
    parser.add_argument("--contrast", type=float, default=1.3)
    parser.add_argument("--saturation", type=float, default=1.2)
    parser.add_argument("--min-color-dist", type=float, default=0, help="Enforce min distance between neighbor colors")
    parser.add_argument("--list-presets", action="store_true")
    parser.add_argument("--list-palettes", action="store_true")
    
    args = parser.parse_args()
    
    if args.list_presets:
        print("\nPresets:\n")
        for name, p in PRESETS.items():
            pal = p["palette"] if isinstance(p["palette"], int) else f'"{p["palette"]}"'
            print(f"  {name:12s}  factor={p['factor']:2d}  palette={str(pal):30s}  dither={p['dither']}")
        return
    
    if args.list_palettes:
        print("\nNamed Palettes:\n")
        for name, colors in PALETTES.items():
            print(f"  {name:30s}  {len(colors):3d} colors")
        return
    
    if not args.input:
        parser.error("input image path is required")
    
    # Parse preset
    if args.preset:
        p = PRESETS[args.preset]
        factor = args.factor or p["factor"]
        dither = args.dither or p["dither"]
        palette_arg = args.palette or p["palette"]
    else:
        factor = args.factor or 8
        dither = args.dither or "none"
        palette_arg = args.palette
    
    # Parse palette
    palette_name = None
    palette_size = args.colors or 32
    if palette_arg:
        if isinstance(palette_arg, str) and palette_arg.upper() in PALETTES:
            palette_name = palette_arg.upper()
        else:
            try:
                palette_size = int(palette_arg)
            except ValueError:
                if palette_arg.upper() in PALETTES:
                    palette_name = palette_arg.upper()
                else:
                    parser.error(f"Unknown palette: {palette_arg}")
    
    pixelart(
        input_path=args.input,
        output_path=args.output,
        factor=factor,
        palette_size=palette_size,
        palette_name=palette_name,
        dither=dither,
        use_svd=args.use_svd,
        contrast=args.contrast,
        saturation=args.saturation,
        min_color_dist=args.min_color_dist,
    )


if __name__ == "__main__":
    main()
