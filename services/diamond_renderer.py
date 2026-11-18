import io
import os
import random
from PIL import Image, ImageDraw, ImageFont

# High-contrast modern casino color palette matching Duel.com
COLOR_CANVAS_BG = (11, 16, 27, 255)         # Deepest dark navy (#0b101b)
COLOR_BOARD_BG = (15, 23, 42, 255)          # Dark slate container (#0f172a)
COLOR_BOARD_BORDER = (30, 41, 59, 255)      # Slate frame outline

# Tile styling for unrevealed tiles
COLOR_TILE_UNREVEALED = (22, 33, 56, 255)   # Rich deep sapphire navy
COLOR_TILE_BORDER = (45, 66, 107, 255)      # Vibrant slate blue border
COLOR_TILE_GLOSS = (35, 52, 86, 255)        # Top glossy sheen

# Hit styling (Duel.com sparkling diamond with emerald neon halo)
COLOR_TILE_HIT_BG = (6, 50, 36, 255)        # Radiant emerald glow
COLOR_TILE_HIT_BORDER = (16, 185, 129, 255) # Radiant neon green border
COLOR_TILE_HIT_GLOW = (16, 185, 129, 90)    # Outer neon green halo

# Numbers styling
COLOR_TEXT_WHITE = (255, 255, 255, 255)
COLOR_TEXT_SHADOW = (10, 15, 26, 220)

# Full pool of 10 available hazards
ALL_HAZARDS = [
    "fiery_blast",
    "frag_grenade",
    "tnt_dynamite",
    "naval_mine",
    "c4_explosive",
    "molotov",
    "toxic_canister",
    "cartoon_bomb",
    "landmine",
    "atomic_blast"
]

# Themed styling and neon halo colors for each hazard
HAZARD_STYLES = {
    "fiery_blast": {
        "bg": (35, 14, 18, 255),
        "border": (239, 68, 68, 255),
        "glow": (239, 68, 68, 90)
    },
    "atomic_blast": {
        "bg": (38, 20, 10, 255),
        "border": (245, 158, 11, 255),
        "glow": (245, 158, 11, 90)
    },
    "frag_grenade": {
        "bg": (20, 26, 38, 255),
        "border": (148, 163, 184, 255),
        "glow": (148, 163, 184, 90)
    },
    "tnt_dynamite": {
        "bg": (38, 12, 16, 255),
        "border": (220, 38, 38, 255),
        "glow": (220, 38, 38, 90)
    },
    "naval_mine": {
        "bg": (30, 15, 24, 255),
        "border": (244, 63, 94, 255),
        "glow": (244, 63, 94, 90)
    },
    "c4_explosive": {
        "bg": (28, 16, 20, 255),
        "border": (239, 68, 68, 255),
        "glow": (239, 68, 68, 90)
    },
    "molotov": {
        "bg": (36, 18, 12, 255),
        "border": (249, 115, 22, 255),
        "glow": (249, 115, 22, 90)
    },
    "toxic_canister": {
        "bg": (18, 34, 14, 255),
        "border": (132, 204, 22, 255),
        "glow": (132, 204, 22, 90)
    },
    "cartoon_bomb": {
        "bg": (26, 16, 38, 255),
        "border": (168, 85, 247, 255),
        "glow": (168, 85, 247, 90)
    },
    "landmine": {
        "bg": (22, 30, 16, 255),
        "border": (101, 163, 13, 255),
        "glow": (101, 163, 13, 90)
    }
}

# Resolve assets directory relative to project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "diamond")
HAZARDS_DIR = os.path.join(ASSETS_DIR, "hazards")

# Preload & pre-scale assets for sub-millisecond renders
_PRESCALED_ASSETS = {}

def _init_assets(tile_size: int = 118):
    global _PRESCALED_ASSETS
    if _PRESCALED_ASSETS:
        return

    # Pre-scale diamond (aspect-fit strictly within tile_size * 0.76)
    dia_path = os.path.join(ASSETS_DIR, "diamond_gem.png")
    if os.path.exists(dia_path):
        raw_dia = Image.open(dia_path).convert("RGBA")
        max_dim = int(tile_size * 0.76)
        scale = min(max_dim / raw_dia.width, max_dim / raw_dia.height)
        dw = int(raw_dia.width * scale)
        dh = int(raw_dia.height * scale)
        _PRESCALED_ASSETS["diamond"] = raw_dia.resize((dw, dh), Image.LANCZOS)

    # Pre-scale all hazards (aspect-fit strictly inside tile box)
    if os.path.exists(HAZARDS_DIR):
        for fname in os.listdir(HAZARDS_DIR):
            if fname.endswith(".png"):
                h_key = fname[:-4]
                fpath = os.path.join(HAZARDS_DIR, fname)
                try:
                    raw_h = Image.open(fpath).convert("RGBA")
                    # Blasts fill up to 84% of tile, other items fill up to 72% to guarantee generous inner margins
                    max_dim = int(tile_size * 0.84) if "blast" in h_key else int(tile_size * 0.72)
                    scale = min(max_dim / raw_h.width, max_dim / raw_h.height)
                    hw = int(raw_h.width * scale)
                    hh = int(raw_h.height * scale)
                    _PRESCALED_ASSETS[h_key] = raw_h.resize((hw, hh), Image.LANCZOS)
                except Exception:
                    continue

def get_font(size: int, bold: bool = True):
    font_paths = [
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/SFProText-Bold.ttf" if bold else "/System/Library/Fonts/SFProText-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf"
    ]
    for p in font_paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()

# Preload font
_TILE_FONT = get_font(38, bold=True)

def generate_diamond_board(match) -> io.BytesIO:
    """
    Renders a stunning 580x580 high-resolution Duel.com style casino board.
    - 4x4 Grid of 16 glossy rounded tiles
    - Unrevealed tiles show numbers 1-16 with glossy gradient and subtle drop shadow
    - Missed tiles reveal the match's specific randomly-selected hazard items
    - Winning tile shows a radiant 3D sparkling crystal diamond with glowing neon emerald halo
    """
    _init_assets(tile_size=118)

    d_data = match.diamond_data
    revealed = d_data.get("revealed", {})
    is_finished = d_data.get("is_finished", False)
    winner_tile = d_data.get("winner_tile", None)
    tile_hazards = d_data.get("tile_hazards", {})

    width, height = 580, 580
    img = Image.new("RGBA", (width, height), COLOR_CANVAS_BG)
    draw = ImageDraw.Draw(img)

    # Outer container border
    draw.rounded_rectangle([10, 10, width - 10, height - 10], radius=24, fill=COLOR_BOARD_BG, outline=COLOR_BOARD_BORDER, width=2)

    cols, rows = 4, 4
    tile_size = 118
    gap = 16
    total_w = cols * tile_size + (cols - 1) * gap
    total_h = rows * tile_size + (rows - 1) * gap
    start_x = (width - total_w) // 2
    start_y = (height - total_h) // 2

    dia_img = _PRESCALED_ASSETS.get("diamond")

    for r in range(rows):
        for c in range(cols):
            tile_num = r * cols + c + 1
            tx0 = start_x + c * (tile_size + gap)
            ty0 = start_y + r * (tile_size + gap)
            tx1 = tx0 + tile_size
            ty1 = ty0 + tile_size
            cx = (tx0 + tx1) / 2
            cy = (ty0 + ty1) / 2

            if tile_num in revealed:
                is_hit = revealed[tile_num]
                if is_hit:
                    # Winning Diamond tile with radiant Emerald glow
                    draw.rounded_rectangle([tx0 - 2, ty0 - 2, tx1 + 2, ty1 + 2], radius=20, outline=COLOR_TILE_HIT_GLOW, width=2)
                    draw.rounded_rectangle([tx0, ty0, tx1, ty1], radius=18, fill=COLOR_TILE_HIT_BG, outline=COLOR_TILE_HIT_BORDER, width=3)
                    if dia_img:
                        img.paste(dia_img, (int(cx - dia_img.width / 2), int(cy - dia_img.height / 2)), dia_img)
                else:
                    # Missed tile: lookup this tile's specific hazard
                    h_name = tile_hazards.get(tile_num, "fiery_blast")
                    h_style = HAZARD_STYLES.get(h_name, HAZARD_STYLES["fiery_blast"])
                    draw.rounded_rectangle([tx0 - 2, ty0 - 2, tx1 + 2, ty1 + 2], radius=20, outline=h_style["glow"], width=2)
                    draw.rounded_rectangle([tx0, ty0, tx1, ty1], radius=18, fill=h_style["bg"], outline=h_style["border"], width=3)
                    h_img = _PRESCALED_ASSETS.get(h_name, _PRESCALED_ASSETS.get("fiery_blast"))
                    if h_img:
                        img.paste(h_img, (int(cx - h_img.width / 2), int(cy - h_img.height / 2)), h_img)
            else:
                # Unrevealed Tile (Clean dark sapphire tile with glossy top and center number)
                draw.rounded_rectangle([tx0, ty0, tx1, ty1], radius=18, fill=COLOR_TILE_UNREVEALED, outline=COLOR_TILE_BORDER, width=2)
                # Glossy top highlight
                draw.rounded_rectangle([tx0 + 2, ty0 + 2, tx1 - 2, ty0 + tile_size * 0.40], radius=14, fill=COLOR_TILE_GLOSS)

                # Centered number text with subtle drop shadow
                num_str = str(tile_num)
                bbox = _TILE_FONT.getbbox(num_str)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                draw.text((cx - tw / 2 + 1, cy - th / 2 + 1), num_str, font=_TILE_FONT, fill=COLOR_TEXT_SHADOW)
                draw.text((cx - tw / 2, cy - th / 2), num_str, font=_TILE_FONT, fill=COLOR_TEXT_WHITE)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
