"""Generate assets/tools.svg — grouped "Tools I use" card.

Edit GROUPS below and run `python scripts/tools.py` to regenerate.
Brand icons come from simple-icons (scripts/icons.json); tools without one
get a simple generic glyph.
"""
import json
import os
from html import escape

HERE = os.path.dirname(__file__)
ICONS = json.load(open(os.path.join(HERE, "icons.json")))
OUT = os.environ.get("OUT_FILE", os.path.join(HERE, "..", "assets", "tools.svg"))

# Generic glyphs (24x24) for tools simple-icons doesn't ship
GLYPHS = {
    "db": '<ellipse cx="12" cy="5" rx="8" ry="3" fill="none" stroke="{c}" stroke-width="2"/>'
          '<path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3" fill="none" stroke="{c}" stroke-width="2"/>',
    "plus": '<path d="M11 2h2v7h-2zM11 15h2v7h-2zM2 11h7v2H2zM15 11h7v2h-7z" fill="{c}"/>'
            '<path d="M10.5 9h3v6h-3zM9 10.5h6v3H9z" fill="{c}"/>',
    "bars": '<rect x="3" y="12" width="5" height="10" rx="1.5" fill="{c}" opacity=".55"/>'
            '<rect x="9.5" y="7" width="5" height="15" rx="1.5" fill="{c}" opacity=".8"/>'
            '<rect x="16" y="2" width="5" height="20" rx="1.5" fill="{c}"/>',
    "pie": '<circle cx="12" cy="12" r="9" fill="none" stroke="{c}" stroke-width="2"/>'
           '<path d="M12 12V3a9 9 0 0 1 8.5 6z" fill="{c}"/><path d="M12 12l-6.4 6.4A9 9 0 0 1 3 12z" fill="{c}" opacity=".6"/>',
    "wave": '<path d="M2 15c3-6 5-6 7 0s4 6 7 0 4-6 6-2" fill="none" stroke="{c}" stroke-width="2.4" stroke-linecap="round"/>'
            '<path d="M2 20h20" stroke="{c}" stroke-width="2" stroke-linecap="round" opacity=".5"/>',
    "sheet": '<rect x="2" y="2" width="20" height="20" rx="4" fill="{c}"/>'
             '<path d="M7.5 7l9 10M16.5 7l-9 10" stroke="#0d1117" stroke-width="2.4" stroke-linecap="round"/>',
    "code": '<path d="M8 6l-6 6 6 6M16 6l6 6-6 6" fill="none" stroke="{c}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>',
}

# (label, simple-icons title or glyph key, color tuned for a dark background)
GROUPS = [
    ("LANGUAGES & DATABASES", [
        ("Python", "Python", "#4b8bbe"),
        ("PostgreSQL", "PostgreSQL", "#6b8ff0"),
    ]),
    ("DATA & MACHINE LEARNING", [
        ("Pandas", "pandas", "#e70488"),
        ("NumPy", "NumPy", "#4dabcf"),
        ("scikit-learn", "scikit-learn", "#f7931e"),
        ("Jupyter", "Jupyter", "#f37626"),
    ]),
    ("VISUALIZATION, BI & SPREADSHEETS", [
        ("Tableau", "plus", "#e97627"),
        ("Power BI", "bars", "#f2c811"),
        ("Plotly", "Plotly", "#7a76ff"),
        ("Matplotlib", "pie", "#4c9be8"),
        ("Seaborn", "wave", "#6d9eeb"),
        ("Excel", "sheet", "#21a366"),
    ]),
    ("TOOLS", [
        ("Git", "Git", "#f05032"),
        ("VS Code", "code", "#3ea6ff"),
        ("Postman", "Postman", "#ff6c37"),
    ]),
]

W, PAD = 860, 32
BG, BORDER, MUTED, TEXT, PILL = "#0d1117", "#21262d", "#7d8590", "#e6edf3", "#161b22"
PH, GAP, ICON = 36, 10, 16

# Rough text widths for 13px semibold sans (wide side, so text never overflows)
NARROW, WIDE = set("ijlt.I '|f-r"), set("mwMWQGOD@&")


def text_w(s):
    return sum(4.2 if ch in NARROW else 11 if ch in WIDE else 7.6 for ch in s)


body, y = [], 44
n = 0
for gi, (label, items) in enumerate(GROUPS):
    body.append(f'<text x="{PAD}" y="{y}" fill="{MUTED}" font-size="11" font-weight="700" letter-spacing="1.6">{escape(label)}</text>')
    y += 14
    x = PAD
    for name, icon, color in items:
        w = 14 + ICON + 9 + text_w(name) + 14
        if x + w > W - PAD:
            x, y = PAD, y + PH + GAP
        body.append(f'<g class="p" style="animation-delay:{n*0.04:.2f}s">')
        body.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{PH}" rx="9" fill="{PILL}" stroke="#30363d"/>')
        ix, iy = x + 14, y + (PH - ICON) / 2
        s = ICON / 24
        if icon in ICONS:
            body.append(f'<path transform="translate({ix:.1f} {iy:.1f}) scale({s:.4f})" d="{ICONS[icon]}" fill="{color}"/>')
        else:
            body.append(f'<g transform="translate({ix:.1f} {iy:.1f}) scale({s:.4f})">{GLYPHS[icon].format(c=color)}</g>')
        body.append(f'<text x="{ix + ICON + 9:.1f}" y="{y + PH/2 + 4.5}" fill="{TEXT}" font-size="13" font-weight="600">{escape(name)}</text>')
        body.append('</g>')
        x += w + GAP
        n += 1
    y += PH + (34 if gi < len(GROUPS) - 1 else 26)

H = y
svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="-apple-system,BlinkMacSystemFont,\'Segoe UI\',Helvetica,Arial,sans-serif">',
    "<style>@keyframes rise{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}"
    ".p{animation:rise .5s ease-out both}</style>",
    '<defs><linearGradient id="glow" x1="0" x2="1"><stop offset="0" stop-color="#1f6feb" stop-opacity="0"/>'
    '<stop offset=".5" stop-color="#1f6feb" stop-opacity=".55"/><stop offset="1" stop-color="#1f6feb" stop-opacity="0"/></linearGradient></defs>',
    f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12" fill="{BG}" stroke="{BORDER}"/>',
    f'<rect x="1" y="1" width="{W-2}" height="2" fill="url(#glow)"/>',
    *body,
    "</svg>",
]
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w").write("\n".join(svg))
print("wrote", OUT, f"{W}x{H}")
