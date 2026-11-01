import base64
import io
import json
import math
import os
import urllib.request
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")
README = os.path.join(HERE, "..", "README.md")
USER = "KloBraticc"
TOKEN = os.environ.get("GITHUB_TOKEN", "")

F = "Segoe UI, Roboto, Helvetica, Arial, sans-serif"

T = {
    "dark": {
        "card": "#1C1B20", "surface": "#26252C", "surface2": "#33323B",
        "outline": "#45444E", "on_bg": "#EAE7F0", "on_var": "#C6C2D0",
        "primary": "#D0BCFF", "primary_dim": "#4F378B", "accent": "#8AD8CE",
        "muted": "#8F8B99",
        "heat": ["#3B3A49", "#57567A", "#7B7FC0", "#9BA0E8", "#C3C6F6"],
        "heat_txt": ["#C6C2D0", "#E8E6F2", "#14131C", "#14131C", "#14131C"],
        "heat_empty": "#3B3A49",
        "fluff": "#2A2836",
    },
    "light": {
        "card": "#FCFAFF", "surface": "#F1EDF6", "surface2": "#E6E0EE",
        "outline": "#C9C3D2", "on_bg": "#1B1820", "on_var": "#4A4552",
        "primary": "#6F55B8", "primary_dim": "#E5DAFF", "accent": "#2E8C80",
        "muted": "#79747E",
        "heat": ["#E7E4EE", "#C9CCF4", "#A3A8EC", "#7B80DC", "#5C61C4"],
        "heat_txt": ["#4A4552", "#26243A", "#1B1A2E", "#14131C", "#FFFFFF"],
        "heat_empty": "#E7E4EE",
        "fluff": "#E9E3F5",
    },
}

LANG_COLORS = {
    "C#": "#7FB069", "Rust": "#E09B6A", "Python": "#5B9BD5", "C++": "#E06C9F",
    "C": "#8C8C8C", "JavaScript": "#E8D44D", "TypeScript": "#4E9FD4",
    "Java": "#C97B4A", "Go": "#4ACAD8", "Shell": "#89e051", "HTML": "#E37E4F",
    "CSS": "#7C5CC4", "Kotlin": "#A97BFF", "Lua": "#4A6FB5",
}
BAR_FALLBACK = ["#D0BCFF", "#8AD8CE", "#F0A8A0", "#B692FF", "#8F8B99"]

TAGLINES = ["i build tools because existing ones annoy me",
            "yes im a bum", "if the tool i need doesnt exist i write it",
            "uncredited work? dm my discord, it gets credited"]
CHIPS = [("tool", "tool author"), ("moon", "no sleep"), ("grass", "Touching Grass..")]

PINNED_FALLBACK = [
    ("Voidstrap", "Bloxstrap fork with extra Roblox customization", "C#"),
    ("virtualdisplay", "virtual 240Hz display mirroring the main screen", "Rust"),
    ("RiDepth", "depth model made for Roblox", "Python"),
    ("Kiln", "ahead of time native compilation for WPF UI", "Rust"),
]


def http(url, token=""):
    req = urllib.request.Request(url, headers={
        "User-Agent": "profile-generator",
        "Accept": "application/vnd.github+json",
    })
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def graphql(query, token):
    body = json.dumps({"query": query}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "User-Agent": "profile-generator",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fetch_avatar_b64():
    try:
        req = urllib.request.Request(f"https://github.com/{USER}.png",
                                     headers={"User-Agent": "profile-generator"})
        raw = urllib.request.urlopen(req, timeout=30).read()
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(raw)).convert("RGB").resize((200, 200), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, "PNG", optimize=True)
            raw = buf.getvalue()
        except ImportError:
            pass
        return "data:image/png;base64," + base64.b64encode(raw).decode()
    except Exception:
        return ""


def fetch_pinned():
    if not TOKEN:
        return PINNED_FALLBACK
    q = """
    query { viewer {
      pinnedItems(first: 6, types: REPOSITORY) {
        nodes { ... on Repository { name description primaryLanguage { name } url stargazerCount } }
      }
    } }
    """
    try:
        nodes = graphql(q, TOKEN)["data"]["viewer"]["pinnedItems"]["nodes"]
        out = []
        for n in nodes:
            lang = (n.get("primaryLanguage") or {}).get("name") or "Code"
            out.append((n["name"], n.get("description") or "", lang, n["url"], n.get("stargazerCount", 0)))
        if out:
            return out
    except Exception:
        pass
    return PINNED_FALLBACK


def fetch_data():
    d = {"followers": 102, "repos": 73, "stars": 41,
         "contribs": None, "days": [], "langs": [],
         "cur_streak": 1, "longest_streak": 26}
    try:
        u = http(f"https://api.github.com/users/{USER}")
        d["followers"] = u.get("followers", 0)
        d["repos"] = u.get("public_repos", 0)
        repos = http(f"https://api.github.com/users/{USER}/repos?per_page=100&sort=updated")
        d["stars"] = sum(r.get("stargazers_count", 0) for r in repos)
        by = {}
        for r in repos:
            lang = r.get("language")
            if lang:
                by[lang] = by.get(lang, 0) + max(r.get("size", 0), 1)
        total = sum(by.values()) or 1
        d["langs"] = sorted(by.items(), key=lambda kv: -kv[1])[:6]
    except Exception:
        d["langs"] = [("C#", 45000), ("Rust", 20000), ("Python", 12000)]
    def streaks(counts):
        cur = 0
        for i in range(len(counts) - 1, -1, -1):
            if counts[i] > 0:
                cur += 1
            elif i == len(counts) - 1:
                continue
            else:
                break
        best = run = 0
        for c in counts:
            run = run + 1 if c > 0 else 0
            best = max(best, run)
        return cur, max(best, cur)

    got = False
    if TOKEN:
        q = """
        query { viewer {
          contributionsCollection { contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } } }
        } }
        """
        try:
            cc = graphql(q, TOKEN)["data"]["viewer"]["contributionsCollection"]["contributionCalendar"]
            d["contribs"] = cc["totalContributions"]
            days = []
            for w in cc["weeks"]:
                for day in w["contributionDays"]:
                    days.append((day["date"], day["contributionCount"]))
            d["days"] = days[-27:]
            d["cur_streak"], d["longest_streak"] = streaks([c for _, c in days])
            got = True
        except Exception:
            pass
    if not got:
        try:
            yr = date.today().year
            cal = http(f"https://github-contributions-api.jogruber.de/v4/{USER}?y={yr}")["contributions"]
            d["contribs"] = sum(c["count"] for c in cal)
            d["days"] = [(c["date"], c["count"]) for c in cal][-27:]
            d["cur_streak"], d["longest_streak"] = streaks([c["count"] for c in cal])
        except Exception:
            pass
    return d


def blob_path(cx, cy, r, seed_shift=0):
    import math
    pts = []
    for i in range(10):
        ang = 2 * math.pi * i / 10 + seed_shift
        rr = r * (0.82 + 0.18 * ((i * 37 + seed_shift * 13) % 7) / 7)
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f} "
    for i in range(1, len(pts) + 1):
        p0 = pts[i - 1]
        p1 = pts[i % len(pts)]
        mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
        d += f"Q {p0[0]:.1f} {p0[1]:.1f} {mid[0]:.1f} {mid[1]:.1f} "
    return d + "Z"


def hero(c, avatar_b64):
    ax, ay = 160, 150
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="840" height="300" viewBox="0 0 840 300">']
    parts.append(f"""<style>
.ttl{{opacity:0;transform:translateY(16px);animation:up .9s cubic-bezier(.05,.7,.1,1) .05s both}}
.t1,.t2,.t3,.t4{{opacity:0;animation:cycle 16s linear infinite}}
.t2{{animation-delay:-4s}}.t3{{animation-delay:-8s}}.t4{{animation-delay:-12s}}
@keyframes cycle{{0%{{opacity:0;transform:translateY(6px)}}4%{{opacity:1;transform:translateY(0)}}21%{{opacity:1;transform:translateY(0)}}26%{{opacity:0;transform:translateY(-6px)}}100%{{opacity:0}}}}
.b1{{animation:spin 46s linear infinite;transform-box:fill-box;transform-origin:center}}
.b2{{animation:bob 8s ease-in-out infinite;transform-box:fill-box;transform-origin:center}}
.b3{{animation:drift 12s ease-in-out infinite alternate;transform-box:fill-box;transform-origin:center}}
@keyframes up{{from{{opacity:0;transform:translateY(16px)}}to{{opacity:1;transform:none}}}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
@keyframes bob{{0%,100%{{transform:translateY(0) rotate(0)}}50%{{transform:translateY(-9px) rotate(7deg)}}}}
@keyframes drift{{from{{transform:translate(0,0)}}to{{transform:translate(-12px,6px)}}}}
.row{{opacity:0;transform:translateY(12px);animation:up .8s cubic-bezier(.05,.7,.1,1) both}}
.c1{{animation-delay:.5s}}.c2{{animation-delay:.62s}}.c3{{animation-delay:.74s}}
@media (prefers-reduced-motion:reduce){{.ttl,.t1,.t2,.t3,.row{{animation:none;opacity:1;transform:none}}.b1,.b2,.b3{{animation:none}}}}
</style>""")
    parts.append('<clipPath id="cardclip"><rect width="840" height="300" rx="30"/></clipPath>')
    parts.append('<g clip-path="url(#cardclip)">')
    parts.append(f'<rect width="840" height="300" rx="30" fill="{c["card"]}"/>')
    parts.append(f'<path class="b1" d="{blob_path(810, 40, 150)}" fill="{c["primary_dim"]}" opacity="0.55"/>')
    parts.append(f'<path class="b2" d="{blob_path(840, 320, 110, 2)}" fill="{c["primary"]}" opacity="0.22"/>')
    parts.append(f'<path class="b3" d="{blob_path(700, 300, 60, 4)}" fill="{c["accent"]}" opacity="0.18"/>')
    parts.append(avatar_frame(c, ax, ay, avatar_b64))
    tx = 300
    parts.append(f'<text class="ttl" x="{tx}" y="116" font-family="{F}" font-size="62" font-weight="800" fill="{c["on_bg"]}">KloBratic</text>')
    for i, tag in enumerate(TAGLINES):
        parts.append(f'<text class="t{i+1}" x="{tx}" y="156" font-family="{F}" font-size="20" fill="{c["on_var"]}">{esc(tag)}</text>')
    x = tx
    GRASS = ('<path d="M2.5 13 C1.5 9 2.5 5.5 5.5 3 C4.5 7 4.5 10 5.5 13 Z" fill="#7CC24B"/>'
             '<path d="M5 13 C5 7 7 3.5 10.5 1.5 C8.5 6 8 10 8.5 13 Z" fill="#8FD14F"/>'
             '<path d="M8.5 13 C9.5 9 11.5 6.5 14 5.5 C12.5 9 12 11 11.5 13 Z" fill="#6BB83E"/>')
    for i, (ic, label) in enumerate(CHIPS):
        if ic == "grass":
            icon = f'<g transform="translate({x + 16:.0f},213) scale(1.05)">{GRASS}</g>'
        else:
            icon = f'<g transform="translate({x + 16:.0f},212.5) scale(0.625)"><path d="{ICONS[ic]}" fill="{c["primary"]}"/></g>'
        w = 16 + 15 + 7 + len(label) * 8.4 + 16
        parts.append(f'<g class="row c{i+1}"><rect x="{x:.0f}" y="198" width="{w:.0f}" height="44" rx="22" fill="{c["surface2"]}"/>'
                     f'{icon}'
                     f'<text x="{x + 38:.0f}" y="226" font-family="{F}" font-size="15" font-weight="600" fill="{c["on_var"]}">{esc(label)}</text></g>')
        x += w + 10
    parts.append("</g>")
    parts.append("</svg>")
    return "".join(parts)


GITHUB_24 = "M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"
YT_24 = "M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"

ICONS = {
    "star": "M12 2l2.9 6.26 6.6.72-4.9 4.47 1.36 6.5L12 16.7l-5.96 3.25 1.36-6.5-4.9-4.47 6.6-.72L12 2Z",
    "fire": "M13.5.67s.74 2.65.74 4.8c0 2.06-1.35 3.73-3.41 3.73-2.07 0-3.63-1.67-3.63-3.73l.03-.36C5.21 7.51 4 10.62 4 14c0 4.42 3.58 8 8 8s8-3.58 8-8C20 8.61 17.41 3.8 13.5.67zM11.71 19c-1.78 0-3.22-1.4-3.22-3.14 0-1.62 1.05-2.76 2.81-3.12 1.77-.36 3.6-1.21 4.62-2.58.39 1.29.59 2.65.59 4.04 0 2.65-2.15 4.8-4.8 4.8z",
    "book": "M21 5c-1.11-.35-2.33-.5-3.5-.5-1.95 0-4.05.4-5.5 1.5-1.45-1.1-3.55-1.5-5.5-1.5S2.45 4.9 1 6v14.65c0 .25.25.5.5.5.1 0 .15-.05.25-.05C3.1 20.45 5.05 20 6.5 20c1.95 0 4.05.4 5.5 1.5 1.35-.85 3.8-1.5 5.5-1.5 1.65 0 3.35.3 4.75 1.05.1.05.15.05.25.05.25 0 .5-.25.5-.5V6c-.6-.45-1.25-.75-2-1zm0 13.5c-1.1-.35-2.3-.5-3.5-.5-1.7 0-4.15.65-5.5 1.5V8c1.35-.85 3.8-1.5 5.5-1.5 1.2 0 2.4.15 3.5.5v11.5z",
    "people": "M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5s-3 1.34-3 3 1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z",
    "chart": "M5 9.2h3V19H5V9.2zm5.6-4.2h2.8v14h-2.8V5zm5.6 8H19v6h-2.8v-6z",
    "trophy": "M19 5h-2V3H7v2H5c-1.1 0-2 .9-2 2v1c0 2.55 1.92 4.63 4.39 4.94.63 1.5 1.98 2.63 3.61 2.96V19H7v2h10v-2h-4v-3.1c1.63-.33 2.98-1.46 3.61-2.96C19.08 12.63 21 10.55 21 8V7c0-1.1-.9-2-2-2zM5 8V7h2v3.82C5.84 10.4 5 9.3 5 8zm14 0c0 1.3-.84 2.4-2 2.82V7h2v1z",
    "tool": "M22.7 19l-9.1-9.1c.9-2.3.4-5-1.5-6.9-2-2-5-2.4-7.4-1.3L9 6 6 9 1.6 4.7C.4 7.1.9 10.1 2.9 12.1c1.9 1.9 4.6 2.4 6.9 1.5l9.1 9.1c.4.4 1 .4 1.4 0l2.3-2.3c.5-.4.5-1.1.1-1.4z",
    "moon": "M12.34 2.02C6.59 1.82 2 6.42 2 12c0 5.52 4.48 10 10 10 3.71 0 6.93-2.02 8.66-5.02-7.51-.25-12.09-8.43-8.32-14.96z",
    "trend": "M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6z",
}


def fmt(n):
    return f"{n:,}"


def heat_color(count, c):
    if count <= 0:
        return c["heat_empty"], c["heat_txt"][0]
    idx = min(4, (1 if count <= 2 else 2 if count <= 5 else 3 if count <= 8 else 4))
    return c["heat"][idx], c["heat_txt"][idx]


def activity_card(c, d):
    W, H = 840, 470
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
    parts.append(f"""<style>
.tile{{opacity:0;transform:translateY(12px);animation:up .9s cubic-bezier(.05,.7,.1,1) both}}
.tA{{animation-delay:.1s}}.tB{{animation-delay:.2s}}.tC{{animation-delay:.3s}}.tD{{animation-delay:.4s}}
@keyframes up{{from{{opacity:0;transform:translateY(12px)}}to{{opacity:1;transform:none}}}}
.bar{{transform:scaleX(0);transform-box:fill-box;transform-origin:left center;animation:bgrow 1.1s cubic-bezier(.2,0,0,1) both}}
@keyframes bgrow{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
.ring{{animation:pulse 2.4s ease-in-out infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
@media (prefers-reduced-motion:reduce){{.tile{{animation:none;opacity:1;transform:none}}.bar{{animation:none;transform:none}}.ring{{animation:none}}}}
</style>""")
    parts.append(f'<rect width="{W}" height="{H}" rx="30" fill="{c["card"]}"/>')
    parts.append(f'<path d="{scallop(51, 49, 24)}" fill="#5C61C4"/>')
    parts.append(f'<g transform="translate(40,38)"><path d="{ICONS["trend"]}" fill="#FFFFFF"/></g>')
    parts.append(f'<text x="90" y="58" font-family="{F}" font-size="24" font-weight="700" fill="{c["on_bg"]}">GitHub activity</text>')

    tiles = [("star", fmt(d["stars"]), "Stars earned"),
             ("fire", fmt(d["contribs"]) if d["contribs"] is not None else "…", "Contributions"),
             ("book", fmt(d["repos"]), "Public repos"),
             ("people", fmt(d["followers"]), "Followers")]
    for i, (ic, val, lab) in enumerate(tiles):
        tx = 28 + (i % 2) * 216
        ty = 96 + (i // 2) * 116
        cls = ".tABCD"[i + 1]
        parts.append(f'<g class="tile {cls}">')
        parts.append(f'<rect x="{tx}" y="{ty}" width="200" height="100" rx="24" fill="{c["surface"]}"/>')
        parts.append(f'<rect x="{tx+16}" y="{ty+16}" width="34" height="34" rx="10" fill="{c["primary_dim"]}"/>')
        parts.append(f'<g transform="translate({tx+21},{ty+21})"><path d="{ICONS[ic]}" fill="{c["primary"]}"/></g>')
        vs = "34" if len(val) <= 6 else "27"
        parts.append(f'<text x="{tx+62}" y="{ty+45}" font-family="{F}" font-size="{vs}" font-weight="800" fill="{c["on_bg"]}">{val}</text>')
        lab2 = lab if len(lab) <= 21 else lab[:20] + "…"
        parts.append(f'<text x="{tx+62}" y="{ty+72}" font-family="{F}" font-size="14" fill="{c["on_var"]}">{esc(lab2)}</text>')
        parts.append("</g>")

    parts.append(f'<text x="484" y="114" font-family="{F}" font-size="17" font-weight="700" fill="{c["on_bg"]}">Last 21 days</text>')
    today = date.today()
    days_map = {ds: cnt for ds, cnt in d["days"]}
    start = today - timedelta(days=20)
    start -= timedelta(days=(start.weekday() + 1) % 7)
    real = []
    dt = start
    while dt <= today:
        real.append((dt, days_map.get(dt.isoformat(), -1)))
        dt += timedelta(days=1)
    rows = -(-len(real) // 7)
    future = rows * 7 - len(real)
    letters = ["S", "M", "T", "W", "T", "F", "S"]
    gx = 484
    for col in range(7):
        parts.append(f'<text x="{gx + col*44 + 16}" y="140" font-family="{F}" font-size="12" fill="{c["muted"]}" text-anchor="middle">{letters[col]}</text>')
    for i, (dt, cnt) in enumerate(real):
        col = i % 7
        row = i // 7
        x = gx + col * 44
        y = 150 + row * 52
        fill, txt = heat_color(cnt, c)
        parts.append(f'<rect x="{x}" y="{y}" width="38" height="46" rx="12" fill="{fill}"/>')
        parts.append(f'<text x="{x+19}" y="{y+29}" font-family="{F}" font-size="14" font-weight="600" fill="{txt if cnt >= 0 else c["muted"]}" text-anchor="middle">{dt.day}</text>')
        if dt == today:
            parts.append(f'<rect class="ring" x="{x-2.5}" y="{y-2.5}" width="43" height="51" rx="14" fill="none" stroke="{c["primary"]}" stroke-width="2"/>')
    for j in range(future):
        i = len(real) + j
        col = i % 7
        row = i // 7
        x = gx + col * 44
        y = 150 + row * 52
        parts.append(f'<rect x="{x}" y="{y}" width="38" height="46" rx="12" fill="none" stroke="{c["outline"]}" stroke-width="1.5" stroke-dasharray="4 5"/>')

    parts.append(f'<text x="28" y="368" font-family="{F}" font-size="17" font-weight="700" fill="{c["on_bg"]}">Languages across my repositories</text>')
    langs = d["langs"][:6]
    total = sum(v for _, v in langs) or 1
    bx, bw = 28, 784
    x = bx
    for i, (name, v) in enumerate(langs):
        w = bw * v / total
        color = LANG_COLORS.get(name, BAR_FALLBACK[i % len(BAR_FALLBACK)])
        parts.append(f'<g class="bar" style="animation-delay:{0.5 + i * 0.09:.2f}s"><rect x="{x:.1f}" y="382" width="{max(w-3,2):.1f}" height="16" rx="8" fill="{color}"/></g>')
        x += w
    x = bx
    legend = []
    for i, (name, v) in enumerate(langs):
        pct = v * 100.0 / total
        color = LANG_COLORS.get(name, BAR_FALLBACK[i % len(BAR_FALLBACK)])
        legend.append((name, pct, color))
    lx = bx
    ly = 424
    for name, pct, color in legend:
        item = f'<circle cx="{lx+6}" cy="{ly-5}" r="6" fill="{color}"/><text x="{lx+18}" y="{ly}" font-family="{F}" font-size="13.5" fill="{c["on_var"]}">{esc(name)} {pct:.1f}%</text>'
        w = 44 + len(name) * 8.2 + (len(f"{pct:.1f}%")) * 8
        parts.append(item)
        lx += w
        if lx > 640:
            ly += 26
            lx = bx
    parts.append("</svg>")
    return "".join(parts)


def pill_btn(x, y, w, h, fill, label, txt_color, fs=17, stroke=None):
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2}" fill="{fill}"'
    if stroke:
        s += f' stroke="{stroke}" stroke-width="1.5"'
    s += "/>"
    ty = y + h / 2 + fs * 0.36
    return s + (f'<text x="{x + w/2}" y="{ty}" font-family="{F}" font-size="{fs}" '
                f'font-weight="700" fill="{txt_color}" text-anchor="middle">{label}</text>')


def projects_card(c, pinned):
    rows = [(n, de, l, LANG_COLORS.get(l, BAR_FALLBACK[i % len(BAR_FALLBACK)]))
            for i, (n, de, l, *_rest) in enumerate(pinned)]
    H = 24 + len(rows) * 100 + 12
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="840" height="{H}" viewBox="0 0 840 {H}">']
    parts.append(f"""<style>
.pr{{opacity:0;transform:translateY(14px);animation:up .9s cubic-bezier(.05,.7,.1,1) both}}
@keyframes up{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
@media (prefers-reduced-motion:reduce){{.pr{{animation:none;opacity:1;transform:none}}}}
</style>""")
    parts.append(f'<rect width="840" height="{H}" rx="30" fill="{c["card"]}"/>')
    y = 24
    for i, (name, desc, lang, col) in enumerate(rows):
        parts.append(f'<g class="pr" style="animation-delay:{0.1 + i*0.12:.2f}s">')
        parts.append(f'<rect x="24" y="{y}" width="792" height="88" rx="24" fill="{c["surface"]}"/>')
        parts.append(f'<text x="56" y="{y+40}" font-family="{F}" font-size="24" font-weight="700" fill="{c["on_bg"]}">{esc(name)}</text>')
        dd = desc if len(desc) <= 55 else desc[:54] + "…"
        parts.append(f'<text x="56" y="{y+66}" font-family="{F}" font-size="17" fill="{c["on_var"]}">{esc(dd)}</text>')
        lw = 40 + len(lang) * 11
        parts.append(pill_btn(792 - lw - 24, y + 24, lw, 40, c["surface2"], esc(lang), c["primary"], 17, c["outline"]))
        parts.append("</g>")
        y += 100
    parts.append("</svg>")
    return "".join(parts)


def smooth_blob(cx, cy, R, lobes, amp, phase):
    n = lobes * 8
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        rr = R * (1 + amp * math.cos(lobes * (t - phase)))
        pts.append((cx + rr * math.cos(t), cy + rr * math.sin(t)))
    d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f} "
    for i in range(n):
        p0 = pts[(i - 1) % n]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f"C {c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f} "
    return d + "Z"


def avatar_frame(c, ax, ay, avatar_b64):
    AV = smooth_blob(ax, ay, 89, 9, 0.10, math.pi / 9)
    parts = [f"""<style>
.spin{{animation:spin 60s linear infinite;transform-origin:{ax}px {ay}px}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
@media (prefers-reduced-motion:reduce){{.spin{{animation:none}}}}
</style>"""]
    parts.append(f'<g class="spin"><path d="{smooth_blob(ax, ay, 112, 9, 0.12, 0)}" '
                 f'fill="#7B74C9" stroke="#14131A" stroke-width="3"/></g>')
    parts.append(f'<clipPath id="av"><path d="{AV}"/></clipPath>')
    if avatar_b64:
        parts.append(f'<image x="{ax-100}" y="{ay-100}" width="200" height="200" '
                     f'clip-path="url(#av)" xlink:href="{avatar_b64}" href="{avatar_b64}"/>')
    else:
        parts.append(f'<path d="{AV}" fill="{c["surface2"]}"/>')
    parts.append(f'<path d="{AV}" fill="none" stroke="#14131A" stroke-width="3"/>')
    return "".join(parts)


def scallop(cx, cy, r, lobes=9):
    pts = []
    for i in range(lobes * 2):
        a = 2 * math.pi * i / (lobes * 2) - math.pi / 2
        rr = r * (1.0 if i % 2 == 0 else 0.88)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f} "
    for i in range(1, len(pts) + 1):
        p = pts[i % len(pts)]
        prev = pts[i - 1]
        mx, my = (p[0] + prev[0]) / 2, (p[1] + prev[1]) / 2
        vx, vy = mx - cx, my - cy
        vl = (vx * vx + vy * vy) ** 0.5 or 1
        bump = r * 0.16
        d += f"Q {mx + vx / vl * bump:.1f} {my + vy / vl * bump:.1f} {p[0]:.1f} {p[1]:.1f} "
    return d + "Z"


def streak_card(c, d):
    W, H = 840, 228
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
    parts.append(f"""<style>
.tile{{opacity:0;transform:translateY(12px);animation:up .9s cubic-bezier(.05,.7,.1,1) both}}
.tA{{animation-delay:.15s}}.tB{{animation-delay:.3s}}
@keyframes up{{from{{opacity:0;transform:translateY(12px)}}to{{opacity:1;transform:none}}}}
.ros{{animation:spin 42s linear infinite;transform-box:fill-box;transform-origin:center}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
@media (prefers-reduced-motion:reduce){{.tile{{animation:none;opacity:1;transform:none}}.ros{{animation:none}}}}
</style>""")
    parts.append(f'<rect width="{W}" height="{H}" rx="30" fill="{c["card"]}"/>')
    parts.append(f'<path d="{scallop(51, 49, 24)}" fill="#5C61C4"/>')
    parts.append(f'<g transform="translate(40,38)"><path d="{ICONS["fire"]}" fill="#FFFFFF"/></g>')
    parts.append(f'<text x="90" y="58" font-family="{F}" font-size="24" font-weight="700" fill="{c["on_bg"]}">Streak</text>')

    tiles = [
        (28, 396, "#5C61C4", "#A8A2E8", "#2B2A6E", "fire", str(d["cur_streak"]), "Current streak", "#FFFFFF", "#DDD9F2"),
        (440, 372, c["surface"], c["surface2"], "#EAE7F0", "trophy", str(d["longest_streak"]), "Longest this year", c["on_bg"], c["on_var"]),
    ]
    for i, (tx, tw, bg, badge, glyph_fill, ic, val, lab, vcol, lcol) in enumerate(tiles):
        cls = "tA" if i == 0 else "tB"
        parts.append(f'<g class="tile {cls}">')
        parts.append(f'<rect x="{tx}" y="100" width="{tw}" height="104" rx="26" fill="{bg}"/>')
        parts.append(f'<path class="ros" d="{scallop(tx + 56, 152, 36)}" fill="{badge}"/>')
        parts.append(f'<g transform="translate({tx + 44},{140})"><path d="{ICONS[ic]}" fill="{glyph_fill}"/></g>')
        parts.append(f'<text x="{tx + 112}" y="158" font-family="{F}" font-size="42" font-weight="800" fill="{vcol}">{val}</text>')
        parts.append(f'<text x="{tx + 116 + len(val) * 26}" y="156" font-family="{F}" font-size="17" font-weight="600" fill="{vcol}">days</text>')
        parts.append(f'<text x="{tx + 112}" y="184" font-family="{F}" font-size="15" fill="{lcol}">{lab}</text>')
        parts.append("</g>")
    parts.append("</svg>")
    return "".join(parts)


def wave_footer(c):
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="840" height="120" viewBox="0 0 840 120" preserveAspectRatio="none">']
    parts.append("""<style>
.wv{animation:wmove linear infinite}
@keyframes wmove{from{transform:translateX(0)}to{transform:translateX(-420px)}}
@media (prefers-reduced-motion:reduce){.wv{animation:none}}
</style>""")
    parts.append(f'<defs><linearGradient id="wg" x1="0" y1="0" x2="1" y2="0">'
                 f'<stop offset="0" stop-color="{c["primary_dim"]}"/>'
                 f'<stop offset="1" stop-color="{c["primary"]}"/></linearGradient></defs>')
    parts.append('<clipPath id="wclip"><rect width="840" height="120" rx="30"/></clipPath>')
    parts.append('<g clip-path="url(#wclip)">')
    parts.append(f'<rect width="840" height="120" fill="{c["card"]}"/>')
    for op, dur in [(0.35, "11s"), (0.7, "7.5s")]:
        parts.append(f'<g opacity="{op}"><path class="wv" style="animation-duration:{dur}" d="M0 60 Q 105 20 210 60 T 420 60 T 630 60 T 840 60 T 1050 60 T 1260 60 V 120 H 0 Z" fill="url(#wg)"/></g>')
    parts.append("</g>")
    parts.append("</svg>")
    return "".join(parts)


START = "<!-- PROFILE:START -->"
END = "<!-- PROFILE:END -->"

def update_readme():
    with open(README, encoding="utf-8") as f:
        content = f.read()
    if START not in content or END not in content:
        print("readme markers missing, skipping")
        return
    block = f"""{START}
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/activity-dark.svg"/>
  <img src="assets/activity-light.svg" width="100%" alt="GitHub activity"/>
</picture>

<br/>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/streak-dark.svg"/>
  <img src="assets/streak-light.svg" width="100%" alt="Streak"/>
</picture>

<br/>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/projects-dark.svg"/>
  <img src="assets/projects-light.svg" width="100%" alt="Projects"/>
</picture>
{END}"""
    with open(README, "w", encoding="utf-8", newline="\n") as f:
        f.write(content[:content.index(START)] + block + content[content.index(END) + len(END):])
    print("readme updated")


def main():
    os.makedirs(ASSETS, exist_ok=True)
    avatar = fetch_avatar_b64()
    data = fetch_data()
    pinned = fetch_pinned()
    for mode, c in T.items():
        with open(os.path.join(ASSETS, f"hero-{mode}.svg"), "w", encoding="utf-8") as f:
            f.write(hero(c, avatar))
        with open(os.path.join(ASSETS, f"activity-{mode}.svg"), "w", encoding="utf-8") as f:
            f.write(activity_card(c, data))
        with open(os.path.join(ASSETS, f"streak-{mode}.svg"), "w", encoding="utf-8") as f:
            f.write(streak_card(c, data))
        with open(os.path.join(ASSETS, f"projects-{mode}.svg"), "w", encoding="utf-8") as f:
            f.write(projects_card(c, pinned))
        with open(os.path.join(ASSETS, f"wave-{mode}.svg"), "w", encoding="utf-8") as f:
            f.write(wave_footer(c))
        with open(os.path.join(ASSETS, f"credit-{mode}.svg"), "w", encoding="utf-8") as f:
            f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="380" height="30" viewBox="0 0 380 30">'
                    f'<text x="190" y="20" font-family="{F}" font-size="14" fill="{c["muted"]}" '
                    f'text-anchor="middle">inspiration from expressive profile (mally)</text></svg>')
    update_readme()
    for old in ("stats-dark.svg", "stats-light.svg", "pill-github-dark.svg", "pill-github-light.svg",
                "pill-youtube-dark.svg", "pill-youtube-light.svg", "pill-website-dark.svg",
                "pill-website-light.svg", "btn-github-dark.svg", "btn-github-light.svg",
                "btn-youtube-dark.svg", "btn-youtube-light.svg", "btn-website-dark.svg",
                "btn-website-light.svg"):
        p = os.path.join(ASSETS, old)
        if os.path.exists(p):
            os.remove(p)
    print("done", {k: v for k, v in data.items() if k != "days"})


if __name__ == "__main__":
    main()
