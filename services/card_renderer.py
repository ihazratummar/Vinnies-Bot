import io
import math
from PIL import Image, ImageDraw, ImageFont

# Colors
COLOR_BG_DARK = (15, 23, 42, 255)         # Dark slate
COLOR_BG_FELT = (10, 36, 26, 255)         # Deep casino green felt
COLOR_BORDER = (30, 70, 52, 255)          # Table border
COLOR_GOLD = (234, 179, 8, 255)           # Golden accent
COLOR_RED_SUIT = (220, 38, 38, 255)       # Hearts / Diamonds
COLOR_BLACK_SUIT = (30, 41, 59, 255)      # Spades / Clubs
COLOR_CARD_BG = (255, 255, 255, 255)      # Crisp card white
COLOR_CARD_BORDER = (203, 213, 225, 255)  # Card outline
COLOR_CARD_BACK = (153, 27, 27, 255)      # Crimson card back
COLOR_TEXT_WHITE = (248, 250, 252, 255)   # White text
COLOR_TEXT_MUTED = (148, 163, 184, 255)   # Muted silver text
COLOR_BADGE_BG = (30, 41, 59, 230)        # Dark pill badge
COLOR_SUCCESS = (34, 197, 94, 255)        # Green
COLOR_DANGER = (239, 68, 68, 255)         # Red

CARD_W = 120
CARD_H = 170

def get_font(size: int, bold: bool = False):
    try:
        # Standard cross-platform fallback font locations
        font_paths = [
            "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf"
        ]
        for p in font_paths:
            try:
                return ImageFont.truetype(p, size)
            except:
                continue
        return ImageFont.load_default()
    except:
        return ImageFont.load_default()

def draw_diamond_suit(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, fill: tuple):
    half_w = size * 0.75
    draw.polygon([(cx, cy - size), (cx + half_w, cy), (cx, cy + size), (cx - half_w, cy)], fill=fill)

def draw_heart_suit(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, fill: tuple):
    r = size * 0.5
    draw.ellipse([cx - size * 0.85, cy - size * 0.85, cx, cy], fill=fill)
    draw.ellipse([cx, cy - size * 0.85, cx + size * 0.85, cy], fill=fill)
    draw.polygon([(cx - size * 0.88, cy - size * 0.35), (cx + size * 0.88, cy - size * 0.35), (cx, cy + size)], fill=fill)

def draw_spade_suit(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, fill: tuple):
    # Inverted heart + stem
    r = size * 0.5
    draw.ellipse([cx - size * 0.85, cy, cx, cy + size * 0.85], fill=fill)
    draw.ellipse([cx, cy, cx + size * 0.85, cy + size * 0.85], fill=fill)
    draw.polygon([(cx - size * 0.88, cy + size * 0.35), (cx + size * 0.88, cy + size * 0.35), (cx, cy - size * 0.9)], fill=fill)
    # Stem
    draw.polygon([(cx - size * 0.3, cy + size * 1.1), (cx + size * 0.3, cy + size * 1.1), (cx, cy + size * 0.2)], fill=fill)

def draw_club_suit(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, fill: tuple):
    r = size * 0.45
    # Top circle
    draw.ellipse([cx - r, cy - size * 0.9, cx + r, cy - size * 0.9 + 2 * r], fill=fill)
    # Left circle
    draw.ellipse([cx - size * 0.85, cy - r * 0.3, cx - size * 0.85 + 2 * r, cy - r * 0.3 + 2 * r], fill=fill)
    # Right circle
    draw.ellipse([cx + size * 0.85 - 2 * r, cy - r * 0.3, cx + size * 0.85, cy - r * 0.3 + 2 * r], fill=fill)
    # Center fill
    draw.ellipse([cx - r * 0.6, cy - r * 0.6, cx + r * 0.6, cy + r * 0.6], fill=fill)
    # Stem
    draw.polygon([(cx - size * 0.3, cy + size * 1.05), (cx + size * 0.3, cy + size * 1.05), (cx, cy + size * 0.1)], fill=fill)

def draw_suit_shape(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, suit: str, fill: tuple):
    clean_s = suit.replace("️", "").strip()
    if clean_s in ("♥", "♥️", "hearts", "heart", "h"):
        draw_heart_suit(draw, cx, cy, size, fill)
    elif clean_s in ("♦", "♦️", "diamonds", "diamond", "d"):
        draw_diamond_suit(draw, cx, cy, size, fill)
    elif clean_s in ("♠", "♠️", "spades", "spade", "s"):
        draw_spade_suit(draw, cx, cy, size, fill)
    else:
        draw_club_suit(draw, cx, cy, size, fill)

def is_red_suit(suit: str) -> bool:
    clean_s = suit.replace("️", "").strip()
    return clean_s in ("♥", "♥️", "♦", "♦️", "hearts", "diamonds", "h", "d")

def render_single_card(rank: str, suit: str, is_hidden: bool = False) -> Image.Image:
    """Renders a single playing card with 2x supersampling and drop shadow for crisp edges."""
    scale = 2
    w = CARD_W * scale
    h = CARD_H * scale
    card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)

    radius = 12 * scale
    card_bounds = [2 * scale, 2 * scale, w - 2 * scale, h - 2 * scale]

    if is_hidden:
        # Luxury casino card back
        draw.rounded_rectangle(card_bounds, radius=radius, fill=COLOR_CARD_BACK, outline=COLOR_GOLD, width=3 * scale)
        inner = [8 * scale, 8 * scale, w - 8 * scale, h - 8 * scale]
        draw.rounded_rectangle(inner, radius=6 * scale, fill=(120, 15, 15, 255), outline=(190, 40, 40, 255), width=2 * scale)
        cx, cy = w // 2, h // 2
        draw_diamond_suit(draw, cx, cy, 24 * scale, COLOR_GOLD)
        # Inner corner gold accents
        draw_diamond_suit(draw, 18 * scale, 18 * scale, 6 * scale, COLOR_GOLD)
        draw_diamond_suit(draw, w - 18 * scale, 18 * scale, 6 * scale, COLOR_GOLD)
        draw_diamond_suit(draw, 18 * scale, h - 18 * scale, 6 * scale, COLOR_GOLD)
        draw_diamond_suit(draw, w - 18 * scale, h - 18 * scale, 6 * scale, COLOR_GOLD)
    else:
        # Face-up card
        draw.rounded_rectangle(card_bounds, radius=radius, fill=COLOR_CARD_BG, outline=COLOR_CARD_BORDER, width=2 * scale)
        color = COLOR_RED_SUIT if is_red_suit(suit) else COLOR_BLACK_SUIT

        font_corner = get_font(20 * scale, bold=True)
        # Top-left rank
        draw.text((12 * scale, 8 * scale), rank, fill=color, font=font_corner)
        # Top-left mini suit
        draw_suit_shape(draw, 20 * scale, 40 * scale, 9 * scale, suit, color)

        cx, cy = w // 2, h // 2
        if rank in ("J", "Q", "K"):
            font_face = get_font(44 * scale, bold=True)
            bbox = draw.textbbox((0, 0), rank, font=font_face)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            draw.text((cx - tw // 2, cy - th // 2 - 10 * scale), rank, fill=color, font=font_face)
            draw_suit_shape(draw, cx, cy + 32 * scale, 16 * scale, suit, color)
        else:
            # Main central suit
            draw_suit_shape(draw, cx, cy, 28 * scale, suit, color)

        # Bottom-right inverted rank & mini suit
        draw_suit_shape(draw, w - 20 * scale, h - 40 * scale, 9 * scale, suit, color)
        bbox = draw.textbbox((0, 0), rank, font=font_corner)
        tw = bbox[2] - bbox[0]
        draw.text((w - 12 * scale - tw, h - 34 * scale), rank, fill=color, font=font_corner)

    return card.resize((CARD_W, CARD_H), Image.Resampling.LANCZOS)

def draw_player_section(
    img: Image.Image,
    x: int,
    y: int,
    player_name: str,
    score: int,
    target_score: int,
    hand: list,
    is_turn: bool,
    reveal: bool,
    total_val: int,
    status_label: str = None
):
    draw = ImageDraw.Draw(img)
    font_name = get_font(18, bold=True)
    font_badge = get_font(14, bold=True)
    font_total = get_font(15, bold=True)

    # Active turn marker
    text_x = x
    max_name_w = 155 if is_turn else 175
    if is_turn:
        # Green glowing indicator circle
        draw.ellipse([x, y + 4, x + 12, y + 16], fill=COLOR_SUCCESS, outline=(187, 247, 208, 255), width=2)
        text_x = x + 20

    display_name = player_name
    while len(display_name) > 3 and draw.textlength(display_name, font=font_name) > max_name_w:
        display_name = display_name[:-2] + "…"

    draw.text((text_x, y), display_name, fill=COLOR_TEXT_WHITE if is_turn else COLOR_TEXT_MUTED, font=font_name)

    # Score Badge
    score_text = f"Wins: {score}/{target_score}"
    draw.rounded_rectangle([x + 225, y - 2, x + 345, y + 24], radius=6, fill=COLOR_BADGE_BG, outline=COLOR_BORDER)
    draw.text((x + 236, y + 3), score_text, fill=COLOR_GOLD, font=font_badge)

    # Total / Status Badge
    if not reveal and len(hand) >= 2:
        c1_val = 10 if hand[0][0] in ("J", "Q", "K") else (11 if hand[0][0] == "A" else int(hand[0][0]))
        total_text = f"Total: {c1_val} + ?"
        bg_col = COLOR_BADGE_BG
        txt_col = COLOR_GOLD
    elif status_label:
        clean_label = status_label.replace("✨", "").replace("💥", "").strip()
        total_text = clean_label
        bg_col = (79, 14, 14, 255) if "BUST" in status_label else (14, 79, 36, 255)
        txt_col = COLOR_DANGER if "BUST" in status_label else COLOR_SUCCESS
    else:
        total_text = f"Total: {total_val}"
        bg_col = (14, 79, 36, 255) if total_val == 21 else COLOR_BADGE_BG
        txt_col = COLOR_SUCCESS if total_val == 21 else COLOR_TEXT_WHITE

    bbox = draw.textbbox((0, 0), total_text, font=font_total)
    badge_w = (bbox[2] - bbox[0]) + 24
    draw.rounded_rectangle([x + 365, y - 2, x + 365 + badge_w, y + 24], radius=6, fill=bg_col, outline=txt_col)
    draw.text((x + 377, y + 2), total_text, fill=txt_col, font=font_total)

    # Render Cards with dynamic spacing to prevent awkward overlap
    card_y = y + 36
    num_cards = len(hand)
    if num_cards <= 3:
        card_spacing = 135
    elif num_cards == 4:
        card_spacing = 115
    else:
        card_spacing = 95

    for idx, card_tuple in enumerate(hand):
        rank, suit = card_tuple
        hide_card = (not reveal and idx > 0)
        card_img = render_single_card(rank, suit, is_hidden=hide_card)
        cx = x + (idx * card_spacing)
        
        # Subtle drop shadow behind card
        shadow = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 80))
        img.paste(shadow, (cx + 4, card_y + 4), card_img)
        img.paste(card_img, (cx, card_y), card_img)


def generate_blackjack_table(
    challenger_name: str,
    opponent_name: str,
    challenger_score: int,
    opponent_score: int,
    target_score: int,
    challenger_hand: list,
    opponent_hand: list,
    c_total: int,
    o_total: int,
    current_turn_id: int,
    challenger_id: int,
    opponent_id: int,
    reveal_challenger: bool,
    reveal_opponent: bool,
    c_status: str = None,
    o_status: str = None,
    banner_note: str = None
) -> io.BytesIO:
    """Generates a complete, beautiful 1v1 Blackjack table graphic."""
    width, height = 820, 520
    img = Image.new("RGBA", (width, height), COLOR_BG_DARK)
    draw = ImageDraw.Draw(img)

    # Casino Felt Mat with rounded corners
    mat_margin = 15
    draw.rounded_rectangle(
        [mat_margin, mat_margin, width - mat_margin, height - mat_margin],
        radius=20,
        fill=COLOR_BG_FELT,
        outline=COLOR_BORDER,
        width=3
    )

    # Header Title
    font_title = get_font(18, bold=True)
    draw.text((35, 28), "♠ ♥  1V1 BLACKJACK  ♦ ♣", fill=COLOR_GOLD, font=font_title)

    if banner_note:
        font_note = get_font(14, bold=True)
        draw.text((width - 35 - draw.textlength(banner_note, font=font_note), 30), banner_note, fill=COLOR_TEXT_WHITE, font=font_note)

    # Top Section: Opponent (Player 2)
    is_o_turn = (current_turn_id == opponent_id)
    draw_player_section(
        img=img,
        x=45,
        y=68,
        player_name=opponent_name,
        score=opponent_score,
        target_score=target_score,
        hand=opponent_hand,
        is_turn=is_o_turn,
        reveal=reveal_opponent,
        total_val=o_total,
        status_label=o_status
    )

    # Center Table Divider Line
    div_y = 285
    draw.line([(35, div_y), (width - 35, div_y)], fill=COLOR_BORDER, width=2)
    draw_diamond_suit(draw, width // 2, div_y, 8, COLOR_GOLD)

    # Bottom Section: Challenger (Player 1)
    is_c_turn = (current_turn_id == challenger_id)
    draw_player_section(
        img=img,
        x=45,
        y=300,
        player_name=challenger_name,
        score=challenger_score,
        target_score=target_score,
        hand=challenger_hand,
        is_turn=is_c_turn,
        reveal=reveal_challenger,
        total_val=c_total,
        status_label=c_status
    )

    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)
    return buffer
