#!/usr/bin/env python3
"""
Render the profile README's cards as animated SVGs into cards/.

Design: Warm Cream & Ember editorial system inspired by tasteskill.dev and
the user's portfolio (espresso ink #1a0e08, warm cream #f8f4ee, ember orange
#ff5b14 / #ff7a2e, burnt rust #7a2306, warm peach #ffc9a3; Instrument Serif,
Google Sans Flex, Google Sans Code).

Every card is a standalone SVG shown through <img>, so it only uses what GitHub
allows inside <img>: inline CSS animations, SMIL <animate>/<set>, and subset
WOFF fonts embedded as base64 data URIs.

Live contribution numbers come from data/contributions.json (fetch_contributions.py).
Run with STATIC=1 to emit frozen final-frame SVGs for screenshot inspection.
"""
import base64
import datetime
import json
import os
import re
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data", "contributions.json")
CODING_DATA = os.path.join(ROOT, "data", "coding_stats.json")
OUT = os.path.join(ROOT, "cards")
FONTS = os.path.join(ROOT, "fonts")
PORTRAIT = os.path.join(ROOT, "nandu-ascii.svg")

USERNAME = os.environ.get("GH_PROFILE_USER", "NandiVardhan2007")

# ---- tasteskill.dev + portfolio design tokens -------------------------------
CREAM = "#f8f4ee"
CREAM_SUNK = "#ebe3d9"
SURFACE = "#fffaf6"
INK_DEEP = "#140a05"
INK = "#1a0e08"
INK_2 = "#2a1309"
INK_SOFT = "#5b483d"
MUTED = "#7c675a"
HAIR = "#e5ddd3"
RUST = "#7a2306"
LABEL = "#c2410c"
ORANGE = "#ff5b14"
ORANGE_HOT = "#ff7a2e"
PEACH = "#ffc9a3"
CREAM_TEXT = "#fff6ef"
CREAM_SOFT = "#fff0e4"
W = 880  # full card width, GitHub's README column at 100%

SERIF = "'Instrument Serif', Georgia, serif"
SANS = "'Google Sans Flex', system-ui, -apple-system, sans-serif"
MONO = "'Google Sans Code', ui-monospace, SFMono-Regular, Menlo, monospace"

FONT_FILES = {
    "serif": ("Instrument Serif", "normal", 400, "serif-400.woff"),
    "serif-i": ("Instrument Serif", "italic", 400, "serif-italic.woff"),
    "sans": ("Google Sans Flex", "normal", 400, "gsflex-400.woff"),
    "sans-b": ("Google Sans Flex", "normal", 600, "gsflex-600.woff"),
    "mono": ("Google Sans Code", "normal", 400, "gscode-400.woff"),
}

BASE_CSS = """
@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes growx{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes pop{0%{opacity:0;transform:scale(.3)}70%{opacity:1;transform:scale(1.15)}100%{opacity:1;transform:none}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
@keyframes nudge{0%,100%{transform:none}50%{transform:translateX(4px)}}
@keyframes nudgeup{0%,100%{transform:none}50%{transform:translate(3px,-3px)}}
.r{opacity:0;animation:rise .8s cubic-bezier(.16,1,.3,1) both;transform-box:fill-box}
.f{opacity:0;animation:fade .9s ease-out both}
.g{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow .8s cubic-bezier(.16,1,.3,1) both}
.gx{transform-box:fill-box;transform-origin:left;transform:scaleX(0);animation:growx .8s cubic-bezier(.16,1,.3,1) both}
.p{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .4s ease-out both}
.live{animation:pulse 1.6s ease-in-out infinite}
.n{transform-box:fill-box;animation:nudge 1.8s ease-in-out infinite}
.nu{transform-box:fill-box;animation:nudgeup 1.8s ease-in-out infinite}
@keyframes tilein{0%{opacity:0;transform:translateY(90px) scale(.6) rotate(-9deg)}55%{opacity:1;transform:translateY(-10px) scale(1.05) rotate(2deg)}75%{transform:translateY(3px) scale(.98) rotate(-.8deg)}90%{transform:translateY(-1px) scale(1.01) rotate(.2deg)}100%{opacity:1;transform:none}}
@keyframes slidein{from{opacity:0;transform:translateX(-26px)}to{opacity:1;transform:none}}
@keyframes arrowin{0%{opacity:0;transform:translateX(-30px)}60%{opacity:1;transform:translateX(6px)}100%{opacity:1;transform:none}}
@keyframes roll{from{transform:translateY(60px)}to{transform:none}}
@keyframes sheen{0%{transform:translateX(-260px) skewX(-20deg)}22%,100%{transform:translateX(420px) skewX(-20deg)}}
@keyframes ring{0%{opacity:.7;transform:scale(.2)}100%{opacity:0;transform:scale(2.4)}}
.ti{opacity:0;transform-box:fill-box;transform-origin:50% 60%;animation:tilein 1.1s cubic-bezier(.16,1,.3,1) both}
.sl{opacity:0;transform-box:fill-box;animation:slidein .6s cubic-bezier(.16,1,.3,1) both}
.ai{opacity:0;transform-box:fill-box;animation:arrowin .7s cubic-bezier(.16,1,.3,1) both}
.ro{transform-box:fill-box;animation:roll .8s cubic-bezier(.16,1,.3,1) both}
.sh{animation:sheen 5s ease-in-out infinite}
.rg{opacity:0;transform-box:fill-box;transform-origin:center;animation:ring 1s ease-out both}
@media (prefers-reduced-motion: reduce){.r,.f,.g,.gx,.p,.live,.n,.nu,.ti,.sl,.ai,.ro,.rg{animation:none!important;opacity:1!important;transform:none!important}.sh,.rg{display:none}}
"""


def font_face(keys):
    out = []
    for k in keys:
        fam, style, weight, fn = FONT_FILES[k]
        with open(os.path.join(FONTS, fn), "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode()
        out.append(
            f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:{weight};"
            f"src:url(data:font/woff;base64,{b64}) format('woff')}}"
        )
    return "".join(out)


GAP = 12          # gap between cards, baked into the SVGs
BOTTOM = 12       # bottom padding per row, matching GAP


def svg(w, h, body, fonts, label, extra_css="", left=0, right=0, bottom=BOTTOM):
    """Card of w x h drawn at x=left inside a transparent canvas, padded so rows tile cleanly."""
    if left:
        body = f'<g transform="translate({left:.3f} 0)">{body}</g>'
    w, h = w + left + right, h + bottom
    css = font_face(fonts) + BASE_CSS + extra_css
    if os.environ.get("STATIC"):  # preview: show every animation at its end state
        css += ".r,.f,.g,.gx,.p,.live,.n,.nu,.ti,.sl,.ai,.ro{animation:none!important;opacity:1!important;transform:none!important}.sh,.rg{display:none}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.3f}" height="{h}" viewBox="0 0 {w:.3f} {h}" '
        f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
        f"<style>{css}</style>{body}</svg>"
    )


def write(name, content):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"wrote cards/{name} ({len(content) // 1024} KB)")


def d(s):  # animation delay attribute
    return f'style="animation-delay:{s:.2f}s"'


def wrap(text, n):
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > n:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line] if line else lines


def text_lines(x, y, lines, lh, attrs):
    return "".join(
        f'<text x="{x}" y="{y + i * lh}" {attrs}>{escape(l)}</text>' for i, l in enumerate(lines)
    )


ICON_STAR = (
    "M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 "
    "2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 "
    "01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z"
)


def icon_star(x, y, size, fill):
    s = size / 16.0
    return f'<path transform="translate({x:.1f},{y:.1f}) scale({s:.3f})" fill="{fill}" d="{ICON_STAR}"/>'


def icon_ne(x, y, size, stroke, cls="nu"):
    return (
        f'<g class="{cls}" transform="translate({x:.1f},{y:.1f})">'
        f'<path d="M1 {size - 1:.1f}L{size - 1:.1f} 1M{size * 0.35:.1f} 1h{size * 0.65 - 1:.1f}v{size * 0.65 - 1:.1f}" '
        f'fill="none" stroke="{stroke}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></g>'
    )


# ---- 1 · hero (tasteskill.dev ember sunrise canvas) ---------------------------
def hero():
    h = 420
    with open(PORTRAIT, encoding="utf-8") as f:
        src = f.read()
    rows = re.findall(r'<text xml:space="preserve"[^>]*\by="([\d.]+)"[^>]*>(.*?)</text>', src, re.S)
    portrait = []
    for i, (y, txt) in enumerate(rows):
        if os.environ.get("STATIC"):
            portrait.append(
                f'<text xml:space="preserve" x="20" y="{y}" fill="{PEACH}" fill-opacity="0.92" font-size="7.2" '
                f'textLength="800" lengthAdjust="spacing">{txt}</text>'
            )
        else:
            portrait.append(
                f'<text class="f" style="animation-delay:{0.25 + i * 0.018:.3f}s;animation-duration:.35s" '
                f'xml:space="preserve" x="20" y="{y}" fill="{PEACH}" fill-opacity="0.92" font-size="7.2" '
                f'textLength="800" lengthAdjust="spacing">{txt}</text>'
            )
    s = 0.465
    shine_anim = "" if os.environ.get("STATIC") else (
        '<animateTransform attributeName="gradientTransform" type="translate" values="-600 0;600 0;600 0" '
        'keyTimes="0;.45;1" dur="7s" begin="1.6s" repeatCount="indefinite"/>'
    )
    body = f"""
<defs>
  <clipPath id="hero-clip"><rect width="{W}" height="{h}" rx="14"/></clipPath>
  <linearGradient id="ember-bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{INK_DEEP}"/>
    <stop offset=".52" stop-color="{INK_2}"/>
    <stop offset=".85" stop-color="#4e1907"/>
    <stop offset="1" stop-color="{RUST}"/>
  </linearGradient>
  <radialGradient id="ember-sun" cx="68%" cy="76%" r="58%">
    <stop offset="0" stop-color="{ORANGE_HOT}" stop-opacity=".42"/>
    <stop offset=".42" stop-color="{ORANGE}" stop-opacity=".18"/>
    <stop offset="1" stop-color="{INK_DEEP}" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="600" y2="0">
    <stop offset="0" stop-color="{PEACH}"/><stop offset=".40" stop-color="{PEACH}"/>
    <stop offset=".50" stop-color="{CREAM_TEXT}"/><stop offset=".60" stop-color="{ORANGE_HOT}"/>
    <stop offset="1" stop-color="{PEACH}"/>
    {shine_anim}
  </linearGradient>
</defs>
<g clip-path="url(#hero-clip)">
  <rect width="{W}" height="{h}" rx="14" fill="url(#ember-bg)"/>
  <rect width="{W}" height="{h}" rx="14" fill="url(#ember-sun)"/>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" rx="13.5" fill="none" stroke="{PEACH}" stroke-opacity=".18"/>
  <g class="f" {d(0)}>
    <rect x="44" y="38" width="332" height="28" rx="14" fill="#ffffff" fill-opacity=".08" stroke="#ffffff" stroke-opacity=".14"/>
    <circle class="live" cx="60" cy="52" r="4" fill="{ORANGE_HOT}"/>
    <text x="73" y="56" font-family="{MONO}" font-size="11" letter-spacing="0.8" fill="{CREAM_SOFT}">SYSTEMS &amp; SOFTWARE ENGINEER</text>
  </g>
  <text class="r" {d(0.15)} x="44" y="186" font-family="{SERIF}" font-size="112" letter-spacing="-2.5" fill="{CREAM_TEXT}">Nandi</text>
  <text class="r" {d(0.3)} x="44" y="286" font-family="{SERIF}" font-style="italic" font-size="112" letter-spacing="-2.5" fill="url(#shine)">Vardhan</text>
  <g class="r" {d(0.55)}>
    {text_lines(48, 336, ["Low-latency Rust & C++ audio pipelines,", "native Android systems, and local AI tools."], 26, f'font-family="{SANS}" font-size="17" fill="{CREAM_SOFT}" fill-opacity=".88"')}
  </g>
  <g class="f" {d(0.8)}>
    <text x="48" y="396" font-family="{MONO}" font-size="12.5" fill="{PEACH}">github.com/NandiVardhan2007</text>
    {icon_ne(256, 386, 10, ORANGE_HOT)}
  </g>
  <g transform="translate(502 82) scale({s}) translate(-20 -37)" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">
    {''.join(portrait)}
  </g>
</g>
"""
    write(
        "hero.svg",
        svg(
            W,
            h,
            body,
            ["serif", "serif-i", "sans", "mono"],
            "Nandi Vardhan. Systems & Software Engineer. Low-latency Rust & C++ audio pipelines, native Android systems, and local AI tools.",
        ),
    )


# ---- 2 · world tiles (tasteskill.dev ember triad) ---------------------------
TILE_W, TILE_H = 880 / 3 - 8, 210  # 285.33: two 12px gaps across the row


def count_up(num, word, x, y, attrs, begin, dur=1.1, frames=18):
    """Number counts up from 0 with SMIL <set> frames (works inside <img>), easing out."""
    m = re.match(r"([\d.]+)(.*)", num)
    val, suf = float(m.group(1)), m.group(2)
    dec = len(m.group(1).split(".")[1]) if "." in m.group(1) else 0
    tail = f' <tspan font-style="italic">{escape(word)}</tspan>'
    if os.environ.get("STATIC"):
        return f'<text x="{x}" y="{y}" {attrs}>{escape(num)}{tail}</text>'
    out = []
    for i in range(frames + 1):
        e = 1 - (1 - i / frames) ** 3
        txt = num if i == frames else f"{val * e:.{dec}f}{suf}"
        on = begin + dur * i / frames
        off = "" if i == frames else f'<set attributeName="opacity" to="0" begin="{begin + dur * (i + 1) / frames:.3f}s"/>'
        out.append(
            f'<text x="{x}" y="{y}" {attrs} opacity="0">{escape(txt)}{tail}'
            f'<set attributeName="opacity" to="1" begin="{on:.3f}s"/>{off}</text>'
        )
    return "".join(out)


def tile(name, label, color, on, accent_arrow, num, word, blurb, delay, pos):
    lines = wrap(blurb, 34)
    blurb_svg = "".join(
        f'<text class="r" {d(delay + 0.75 + i * 0.1)} x="24" y="{150 + i * 20}" font-family="{SANS}" '
        f'font-size="13.5" fill="{on}" opacity=".90">{escape(l)}</text>'
        for i, l in enumerate(lines)
    )
    body = f"""
<defs>
  <clipPath id="card"><rect width="{TILE_W}" height="{TILE_H}" rx="14"/></clipPath>
  <clipPath id="slot"><rect x="0" y="62" width="{TILE_W}" height="62"/></clipPath>
  <linearGradient id="gl" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>
    <stop offset=".5" stop-color="#fff" stop-opacity=".30"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
</defs>
<g class="ti" {d(delay)}>
  <g clip-path="url(#card)">
    <rect width="{TILE_W}" height="{TILE_H}" fill="{color}"/>
    {f'<rect x="0.5" y="0.5" width="{TILE_W - 1}" height="{TILE_H - 1}" rx="13.5" fill="none" stroke="{PEACH}" stroke-opacity=".22"/>' if color == INK else ""}
    <circle class="rg" {d(delay + 0.5)} cx="{TILE_W - 40}" cy="{TILE_H - 40}" r="60" fill="none" stroke="{on}" stroke-opacity=".45" stroke-width="2"/>
    <rect class="sh" style="animation-delay:{delay + 1.4:.2f}s" x="0" y="-20" width="90" height="{TILE_H + 40}" fill="url(#gl)" transform="translate(-260 0)"/>
  </g>
  <text class="sl" {d(delay + 0.35)} x="24" y="38" font-family="{MONO}" font-size="11.5" letter-spacing="1.2" fill="{on}">{label}</text>
  <g class="ai" {d(delay + 0.5)}><text class="n" style="animation-delay:{delay + 1.3:.2f}s" x="250" y="38" font-family="{MONO}" font-size="14" fill="{accent_arrow}">&#8594;</text></g>
  <g clip-path="url(#slot)"><g class="ro" {d(delay + 0.45)}>
    {count_up(num, word, 22, 112, f'font-family="{SERIF}" font-size="44" fill="{on}"', delay + 0.45)}
  </g></g>
  {blurb_svg}
</g>
"""
    write(
        f"{name}.svg",
        svg(
            TILE_W,
            TILE_H,
            body,
            ["serif", "serif-i", "sans", "mono"],
            f"{label}: {num} {word}. {blurb}",
            left=4 * pos,
            right=8 - 4 * pos,
        ),
    )


# ---- 3 · activity (monthly bars on warm cream paper) -------------------------
def activity(data):
    h = 340
    monthly = data["monthly"][-12:]
    best = max(monthly, key=lambda m: m["total"])
    top = max(best["total"], 1)
    x0, x1, base, maxh, gap = 40, 600, 292, 130, 10
    bw = (x1 - x0 - gap * (len(monthly) - 1)) / len(monthly)
    bars = []
    for i, m in enumerate(monthly):
        partial = i == len(monthly) - 1
        is_best = m is best
        bh = max(4, round(m["total"] / top * maxh))
        x = x0 + i * (bw + gap)
        fill = ORANGE if is_best else ("#cfc5b9" if partial else INK)
        label = datetime.date.fromisoformat(m["month"] + "-01").strftime("%b")
        bars.append(
            f'<rect class="g" style="animation-delay:{2.2 + i * 0.07:.2f}s" x="{x:.1f}" y="{base - bh}" '
            f'width="{bw:.1f}" height="{bh}" rx="4" fill="{fill}"><title>{label}: {m["total"]:,}</title></rect>'
            f'<text class="f" style="animation-delay:{2.2 + i * 0.07:.2f}s" x="{x + bw / 2:.1f}" y="{base + 22}" '
            f'text-anchor="middle" font-family="{MONO}" font-size="11" fill="{MUTED}">{label}</text>'
        )
        if is_best:
            bars.append(
                f'<text class="p" style="animation-delay:3.2s" x="{x + bw / 2:.1f}" y="{base - bh - 10}" '
                f'text-anchor="middle" font-family="{MONO}" font-size="11" fill="{LABEL}">{m["total"]:,}</text>'
            )
    cs = data["current_streak"]["length"]
    ls = data["longest_streak"]["length"]
    streak_note = "current streak, and the longest" if cs >= ls else f"current streak, longest {ls}"
    total_days = len(data["days"])
    stats = [
        (f'{cs} <tspan font-style="italic">days</tspan>', streak_note),
        (f'{data["active_days"]}<tspan fill="{MUTED}"> / {total_days}</tspan>', "days with a commit"),
        (f'{data["best_day"]["count"]}', "on the busiest day"),
    ]
    side = []
    for i, (big, small) in enumerate(stats):
        y = 104 + i * 92
        side.append(
            f'<g class="r" {d(2.6 + i * 0.15)}>'
            f'<text x="650" y="{y}" font-family="{SERIF}" font-size="40" fill="{INK}">{big}</text>'
            f'<text x="650" y="{y + 24}" font-family="{SANS}" font-size="13" fill="{MUTED}">{small}</text></g>'
        )
        if i < 2:
            side.append(f'<rect class="f" {d(2.6)} x="650" y="{y + 44}" width="190" height="1" fill="{HAIR}"/>')
    body = f"""
<rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" rx="13.5" fill="{CREAM}" stroke="{HAIR}"/>
<text class="f" {d(1.9)} x="40" y="58" font-family="{MONO}" font-size="11.5" letter-spacing="1" fill="{LABEL}">THE LAST 12 MONTHS ON GITHUB</text>
<text class="r" {d(2.0)} x="38" y="114" font-family="{SERIF}" font-size="52" fill="{INK}">{data["total_contributions"]:,} <tspan font-style="italic" fill="{LABEL}">contributions</tspan></text>
{''.join(bars)}
{''.join(side)}
"""
    write(
        "activity.svg",
        svg(
            W,
            h,
            body,
            ["serif", "serif-i", "sans", "mono"],
            f'{data["total_contributions"]:,} contributions in the last year, {cs}-day streak',
        ),
    )


# ---- 4 · repo cards (warm cream paper + hairline ring) ----------------------
REPO_W, REPO_H = 880 / 3 - 8, 176
REPOS = [
    (
        "Smart-Apply",
        "Voice AI interview simulator and ATS resume tailoring web platform.",
        "TypeScript",
        ORANGE,
    ),
    (
        "GLOOM",
        "Desktop continuity & Dynamic Island for Windows and Android in Rust & Win32.",
        "Rust",
        LABEL,
    ),
    (
        "VISION",
        "Cross-platform multimodal workspace with unified voice, web, and CLI interfaces.",
        "Python",
        INK,
    ),
]


def repo_card(i, name, desc, lang, color, info):
    delay = 4.6 + i * 0.12
    stars = info.get("stars", 0)
    forks = info.get("forks", 0)
    lang = info.get("language") or lang
    fy = REPO_H - 24
    mx = 24
    meta_parts = [f'<text x="{mx}" y="{fy}" font-family="{MONO}" font-size="11.5" fill="{MUTED}">{escape(lang)}</text>']
    mx += len(lang) * 7.1 + 14
    if stars:
        meta_parts.append(f'<text x="{mx}" y="{fy}" font-family="{MONO}" font-size="11.5" fill="{MUTED}">·</text>')
        mx += 14
        meta_parts.append(icon_star(mx, fy - 10, 11, LABEL))
        s_txt = str(stars)
        meta_parts.append(f'<text x="{mx + 15}" y="{fy}" font-family="{MONO}" font-size="11.5" fill="{MUTED}">{s_txt}</text>')
        mx += 15 + len(s_txt) * 7.1 + 14
    if forks:
        f_txt = f"·  {forks} fork{'s' if forks != 1 else ''}"
        meta_parts.append(f'<text x="{mx}" y="{fy}" font-family="{MONO}" font-size="11.5" fill="{MUTED}">{f_txt}</text>')
    if not stars and not forks:
        meta_parts.append(f'<text x="{mx}" y="{fy}" font-family="{MONO}" font-size="11.5" fill="{MUTED}">·  live</text>')
    body = f"""
<rect x="0.5" y="0.5" width="{REPO_W - 1}" height="{REPO_H - 1}" rx="13.5" fill="{CREAM}" stroke="{HAIR}"/>
<g class="r" {d(delay)}>
  <rect x="24" y="30" width="8" height="8" rx="2" fill="{color}"/>
  <text x="40" y="39" font-family="{SANS}" font-weight="600" font-size="18" fill="{INK}">{escape(name)}</text>
  {text_lines(24, 72, wrap(desc, 34), 21, f'font-family="{SANS}" font-size="13.5" fill="{INK_SOFT}"')}
  {''.join(meta_parts)}
</g>
"""
    write(
        f"repo-{name}.svg",
        svg(
            REPO_W,
            REPO_H,
            body,
            ["sans", "sans-b", "mono"],
            f"{name}: {desc}",
            left=4 * i,
            right=8 - 4 * i,
        ),
    )


def section_title(text, italic, theme, slug="coding", delay=4.4):
    fg = CREAM_TEXT if theme == "dark" else INK
    accent = ORANGE_HOT if theme == "dark" else LABEL
    body = (
        f'<text class="r" {d(delay)} x="2" y="46" font-family="{SERIF}" font-size="34" fill="{fg}">{escape(text)} '
        f'<tspan font-style="italic" fill="{accent}">{escape(italic)}</tspan></text>'
    )
    write(f"title-{slug}-{theme}.svg", svg(W, 64, body, ["serif", "serif-i"], f"{text} {italic}", bottom=0))


# ---- 4b · coding profile cards (2x2 grid at width=50%) ----------------------
STAT_W, STAT_H = (W - GAP) / 2, 186  # 434 x 186; 6px inner margin -> 12px center gap


def stat_card(slug, label, handle, color, big_num, big_word, badge_right, mid_svg, footer_text, delay, pos):
    pad = 24
    body = f"""
<rect x="0.5" y="0.5" width="{STAT_W - 1}" height="{STAT_H - 1}" rx="13.5" fill="{CREAM}" stroke="{HAIR}"/>
<g class="r" {d(delay)}>
  <rect x="{pad}" y="28" width="8" height="8" rx="2" fill="{color}"/>
  <text x="{pad + 16}" y="36" font-family="{MONO}" font-size="11.5" letter-spacing="1" fill="{INK}">{escape(label)}</text>
  <text x="{pad + 16 + len(label) * 7.6 + 10}" y="36" font-family="{MONO}" font-size="11" fill="{MUTED}">@{escape(handle)}</text>
  {icon_ne(STAT_W - pad - 10, 26, 10, color)}
  {count_up(str(big_num), big_word, pad, 92, f'font-family="{SERIF}" font-size="46" fill="{INK}"', delay + 0.15)}
  <text x="{STAT_W - pad}" y="88" text-anchor="end" font-family="{MONO}" font-size="11.5" fill="{LABEL}">{escape(badge_right)}</text>
  {mid_svg}
  <text x="{pad}" y="{STAT_H - 22}" font-family="{MONO}" font-size="11.5" fill="{MUTED}">{escape(footer_text)}</text>
</g>
"""
    write(
        f"stats-{slug}.svg",
        svg(
            STAT_W,
            STAT_H,
            body,
            ["serif", "serif-i", "sans", "mono"],
            f"{label} (@{handle}): {big_num} {big_word}. {footer_text}",
            left=6 * pos,
            right=6 - 6 * pos,
        ),
    )


def coding_profiles(stats):
    pad = 24
    bar_w = STAT_W - 2 * pad  # 386

    # 1. LeetCode
    lc = stats.get("leetcode", {})
    solved = lc.get("solved", 0)
    easy, med, hard = lc.get("easy", 0), lc.get("medium", 0), lc.get("hard", 0)
    tot = max(easy + med + hard, 1)
    we = bar_w * (easy / tot)
    wm = bar_w * (med / tot)
    wh = max(bar_w - we - wm, 0)
    lc_bar = (
        f'<rect x="{pad}" y="118" width="{bar_w}" height="8" rx="4" fill="{CREAM_SUNK}"/>'
        f'<rect class="gx" style="animation-delay:5.35s" x="{pad}" y="118" width="{we:.1f}" height="8" rx="4" fill="{ORANGE_HOT}"/>'
        f'<rect class="gx" style="animation-delay:5.45s" x="{pad + we:.1f}" y="118" width="{wm:.1f}" height="8" rx="2" fill="{ORANGE}"/>'
        f'<rect class="gx" style="animation-delay:5.55s" x="{pad + we + wm:.1f}" y="118" width="{wh:.1f}" height="8" rx="4" fill="{RUST}"/>'
    )
    stat_card(
        "leetcode",
        "LEETCODE",
        lc.get("username", "Nandu_2007_"),
        ORANGE,
        str(solved),
        "solved",
        f'{lc.get("acceptance", "0%")} acc · {lc.get("streak", 0)}d streak',
        lc_bar,
        f'Easy {easy}  ·  Med {med}  ·  Hard {hard}  ·  Rank {lc.get("ranking", "—")}',
        5.1,
        0,
    )

    # 2. CodeChef
    cc = stats.get("codechef", {})
    rating = cc.get("rating", 0)
    cc_pct = min(max(rating / 2000.0, 0.08), 1.0)
    cc_bar = (
        f'<rect x="{pad}" y="118" width="{bar_w}" height="8" rx="4" fill="{CREAM_SUNK}"/>'
        f'<rect class="gx" style="animation-delay:5.45s" x="{pad}" y="118" width="{bar_w * cc_pct:.1f}" height="8" rx="4" fill="{INK}"/>'
        f'<circle cx="{pad + bar_w * cc_pct:.1f}" cy="122" r="4" fill="{ORANGE}"/>'
    )
    stars = cc.get("stars", 0)
    div = cc.get("division", "")
    cc_badge = f'{stars}★ · {div}' if stars and div else (f"{stars}★" if stars else div or "Rated")
    stat_card(
        "codechef",
        "CODECHEF",
        cc.get("username", "nandu_2007"),
        INK,
        str(rating),
        "rating",
        cc_badge,
        cc_bar,
        f'{cc.get("solved", 0)} solved  ·  Global {cc.get("global_rank", "—")}  ·  IN {cc.get("country_rank", "—")}',
        5.22,
        1,
    )

    # 3. HackerRank
    hr = stats.get("hackerrank", {})
    badges = hr.get("badges", [])[:3]
    pills = []
    px = pad
    pill_colors = [(PEACH, INK), (CREAM_SUNK, INK), (INK, CREAM_TEXT)]
    norm = {"Sql": "SQL"}
    for idx, b in enumerate(badges):
        b_name = norm.get(b["name"], b["name"])
        txt = f'{b_name} {b["stars"]}★' if b.get("stars") else f'{b_name} ({b.get("solved", 0)})'
        pw = max(len(txt) * 7.4 + 22, 76)
        bg, fg = pill_colors[idx % len(pill_colors)]
        pills.append(
            f'<rect class="f" style="animation-delay:{5.55 + idx * 0.08:.2f}s" x="{px:.1f}" y="110" width="{pw:.1f}" height="26" rx="13" fill="{bg}"/>'
            f'<text class="f" style="animation-delay:{5.55 + idx * 0.08:.2f}s" x="{px + pw / 2:.1f}" y="127" text-anchor="middle" font-family="{MONO}" font-size="11" fill="{fg}">{escape(txt)}</text>'
        )
        px += pw + 8
    hr_footer = "  ·  ".join(f'{norm.get(b["name"], b["name"])} ({b["solved"]})' for b in badges) or "Domain badges"
    stat_card(
        "hackerrank",
        "HACKERRANK",
        hr.get("username", "nandu_2007"),
        LABEL,
        str(hr.get("total_solved", 0)),
        "solved",
        f'{hr.get("top_stars", 0)}★ peak',
        "".join(pills),
        hr_footer,
        5.34,
        0,
    )

    # 4. GeeksforGeeks
    gfg = stats.get("gfg", {})
    g_solved = gfg.get("solved", 0)
    g_score = gfg.get("score", 0)
    g_pct = min(max(g_score / 200.0, 0.10), 1.0)
    gfg_bar = (
        f'<rect x="{pad}" y="118" width="{bar_w}" height="8" rx="4" fill="{CREAM_SUNK}"/>'
        f'<rect class="gx" style="animation-delay:5.70s" x="{pad}" y="118" width="{bar_w * g_pct:.1f}" height="8" rx="4" fill="{RUST}"/>'
        f'<circle cx="{pad + bar_w * g_pct:.1f}" cy="122" r="4" fill="{ORANGE_HOT}"/>'
    )
    stat_card(
        "gfg",
        "GEEKSFORGEEKS",
        gfg.get("username", "nandu07"),
        RUST,
        str(g_solved),
        "solved",
        f'Rank {gfg.get("institute_rank", "—")}',
        gfg_bar,
        f'Coding Score {g_score}  ·  Aditya COE',
        5.46,
        1,
    )


# ---- 5 · ember contribution graph -------------------------------------------
EMBER = [CREAM_SUNK, "#ffd4b5", "#ffa46b", ORANGE_HOT, ORANGE, LABEL]


def level_for(c):
    return 0 if c == 0 else 1 if c <= 5 else 2 if c <= 15 else 3 if c <= 30 else 4 if c <= 50 else 5


def heatmap(data):
    days = data["days"]
    first = datetime.date.fromisoformat(days[0]["date"])
    lead = (first.weekday() + 1) % 7  # sunday = 0
    cell, step, gx, gy = 12, 15, 44, 96
    cells, months, seen = [], [], set()
    for i, day in enumerate(days):
        k = i + lead
        col, row = divmod(k, 7)
        date = datetime.date.fromisoformat(day["date"])
        if date.day <= 7 and (date.year, date.month) not in seen and row == 0:
            seen.add((date.year, date.month))
            months.append((col, date.strftime("%b")))
        c = day["count"]
        delay = 1.0 + col * 0.03 + row * 0.02
        cells.append(
            f'<rect class="p" style="animation-delay:{delay:.2f}s" x="{gx + col * step}" y="{gy + row * step}" '
            f'width="{cell}" height="{cell}" rx="3" fill="{EMBER[level_for(c)]}">'
            f'<title>{day["date"]}: {c} contribution{"s" if c != 1 else ""}</title></rect>'
        )
    ncols = (len(days) + lead + 6) // 7
    right = gx + ncols * step - 3
    labels = "".join(
        f'<text x="{gx + col * step}" y="{gy + 7 * step + 18}" font-family="{MONO}" font-size="11" fill="{MUTED}">{m}</text>'
        for col, m in months if col < ncols - 1
    )
    legend_x = right - len(EMBER) * 14 - 36
    legend = "".join(
        f'<rect x="{legend_x + i * 14}" y="50" width="11" height="11" rx="2.5" fill="{c}"/>'
        for i, c in enumerate(EMBER)
    )
    h = gy + 7 * step + 44
    body = f"""
<rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" rx="13.5" fill="{CREAM}" stroke="{HAIR}"/>
<text class="r" {d(0.8)} x="42" y="62" font-family="{SERIF}" font-size="34" fill="{INK}">Every day, <tspan font-style="italic" fill="{ORANGE}">in ember</tspan></text>
<g class="f" {d(0.8)}>
  <text x="{right}" y="40" text-anchor="end" font-family="{MONO}" font-size="10.5" letter-spacing="1" fill="{MUTED}">REFRESHED DAILY</text>
  <text x="{legend_x - 8}" y="60" text-anchor="end" font-family="{MONO}" font-size="11" fill="{MUTED}">less</text>
  {legend}
  <text x="{legend_x + len(EMBER) * 14 + 2}" y="60" font-family="{MONO}" font-size="11" fill="{MUTED}">more</text>
</g>
{''.join(cells)}
<g class="f" {d(2.4)}>{labels}</g>
"""
    write(
        "heatmap.svg",
        svg(
            W,
            h,
            body,
            ["serif", "serif-i", "mono"],
            f'Contribution graph: {data["total_contributions"]:,} contributions in the last year',
        ),
    )


def fetch_github_meta():
    repo_count = 16
    repo_info = {}
    try:
        import requests

        headers = {"User-Agent": "profile-readme-bot/1.0"}
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        u = requests.get(f"https://api.github.com/users/{USERNAME}", headers=headers, timeout=10)
        if u.ok:
            repo_count = u.json().get("public_repos", repo_count)

        for name, *_ in REPOS:
            r = requests.get(f"https://api.github.com/repos/{USERNAME}/{name}", headers=headers, timeout=10)
            if r.ok:
                j = r.json()
                repo_info[name] = {
                    "stars": j.get("stargazers_count", 0),
                    "forks": j.get("forks_count", 0),
                    "language": j.get("language"),
                }
    except Exception as e:
        print(f"github meta unavailable: {e}")
    return repo_count, repo_info


if __name__ == "__main__":
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    repo_count, repo_info = fetch_github_meta()
    hero()
    tile(
        "build",
        "BUILD",
        ORANGE,
        CREAM_TEXT,
        CREAM_TEXT,
        str(repo_count),
        "repos",
        "Rust & C++ audio engines, native Android apps, and local AI tools.",
        3.1,
        0,
    )
    tile(
        "compete",
        "COMPETE",
        INK,
        CREAM_TEXT,
        ORANGE_HOT,
        "14",
        "/ 1,517",
        "Oracle SQL rank #14, #2 Project Space Hackathon, and LeetCode DSA.",
        3.35,
        1,
    )
    tile(
        "craft",
        "CRAFT",
        PEACH,
        INK,
        LABEL,
        "5",
        "live apps",
        "Shipping Harmonix (<4.2ms DSP) alongside B.Tech IT at Aditya COE.",
        3.6,
        2,
    )
    activity(data)
    for i, (name, desc, lang, color) in enumerate(REPOS):
        repo_card(i, name, desc, lang, color, repo_info.get(name, {}))
    section_title("What I'm", "building", "dark", slug="coding", delay=4.4)
    section_title("What I'm", "building", "light", slug="coding", delay=4.4)
    if os.path.exists(CODING_DATA):
        with open(CODING_DATA, encoding="utf-8") as f:
            coding_stats = json.load(f)
        section_title("Coding", "profiles", "dark", slug="profiles", delay=4.95)
        section_title("Coding", "profiles", "light", slug="profiles", delay=4.95)
        coding_profiles(coding_stats)
    heatmap(data)
