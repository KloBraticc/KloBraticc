"""Generate profile stats SVGs from GitHub's public repository data."""

import argparse
import json
import os
from collections import Counter
from html import escape
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen
from xml.etree import ElementTree


ICON_DIR = Path(__file__).resolve().parents[1] / "assets" / "devicon"
ICON_FILES = {
    "Lua": "lua.svg",
    "C#": "csharp.svg",
    "Java": "java.svg",
    "Rust": "rust.svg",
    "JavaScript": "javascript.svg",
}
LANGUAGE_COLORS = {
    "Lua": "#174c9c",
    "C#": "#68217a",
    "Java": "#e76f00",
    "Rust": "#555555",
    "JavaScript": "#d9b600",
}
FONT = "Arial, Helvetica, sans-serif"
ElementTree.register_namespace("", "http://www.w3.org/2000/svg")


def get_json(url, token, allow_unavailable=False):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-stats"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urlopen(Request(url, headers=headers), timeout=20) as response:
            return json.load(response)
    except HTTPError as error:
        if allow_unavailable and error.code in (404, 409, 451):
            return None
        raise RuntimeError(f"GitHub API returned {error.code} for {url}") from error


def list_repositories(username, token):
    repos = []
    page = 1
    while True:
        batch = get_json(
            f"https://api.github.com/users/{quote(username)}/repos?type=owner&per_page=100&page={page}",
            token,
        )
        repos.extend(batch)
        if len(batch) < 100:
            return repos
        page += 1


def language_rows(languages, limit=5):
    ranked = languages.most_common()
    rows = ranked[:limit]
    if len(ranked) > limit:
        rows.append(("Other", sum(count for _, count in ranked[limit:])))
    return rows


def icon_svg(language, x, y):
    filename = ICON_FILES.get(language)
    if not filename:
        return ""
    icon = ElementTree.parse(ICON_DIR / filename).getroot()
    icon.set("x", str(x))
    icon.set("y", str(y))
    icon.set("width", "18")
    icon.set("height", "18")
    return ElementTree.tostring(icon, encoding="unicode")


def overview_svg(repos, stars, followers):
    cells = (("Original repos", repos), ("Stars earned", stars), ("Followers", followers))
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="420" height="132" viewBox="0 0 420 132" role="img" aria-label="GitHub overview stats">',
        "<title>GitHub overview stats</title>",
        '<rect x="1" y="1" width="418" height="130" fill="#ffffff" stroke="#d0d7de"/>',
        f'<text x="24" y="33" fill="#24292f" font-family="{FONT}" font-size="19" font-weight="700">GitHub</text>',
        '<path d="M140 54v58M280 54v58" stroke="#d8dee4"/>',
    ]
    for index, (label, value) in enumerate(cells):
        x = 70 + index * 140
        parts.append(
            f'<text x="{x}" y="87" text-anchor="middle" fill="#6f42c1" font-family="{FONT}" font-size="28" font-weight="700">{value:,}</text>'
        )
        parts.append(
            f'<text x="{x}" y="109" text-anchor="middle" fill="#57606a" font-family="{FONT}" font-size="13">{label}</text>'
        )
    return "\n".join(parts + ["</svg>", ""])


def languages_svg(languages):
    rows = language_rows(languages)
    height = 88 + 42 * max(1, len(rows)) + 14
    total = sum(languages.values())
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="420" height="{height}" viewBox="0 0 420 {height}" role="img" aria-label="Most used languages by code size">',
        "<title>Most used languages by available code size in public original repositories</title>",
        f'<rect x="1" y="1" width="418" height="{height - 2}" fill="#ffffff" stroke="#d0d7de"/>',
        f'<text x="24" y="34" fill="#24292f" font-family="{FONT}" font-size="19" font-weight="700">Languages</text>',
        f'<text x="24" y="56" fill="#57606a" font-family="{FONT}" font-size="12">Available code size in public original repos</text>',
        '<path d="M24 69h372" stroke="#d8dee4"/>',
    ]
    if not rows:
        parts.append(
            f'<text x="24" y="99" fill="#57606a" font-family="{FONT}" font-size="14">No language data yet</text>'
        )
    for index, (name, count) in enumerate(rows):
        y = 94 + index * 42
        ratio = count / total
        color = LANGUAGE_COLORS.get(name, "#6e7781")
        parts.extend(
            [
                icon_svg(name, 24, y - 15),
                f'<text x="50" y="{y}" fill="#24292f" font-family="{FONT}" font-size="14" font-weight="600">{escape(name)}</text>',
                f'<text x="396" y="{y}" text-anchor="end" fill="#57606a" font-family="{FONT}" font-size="13">{ratio * 100:.1f}%</text>',
                f'<rect x="50" y="{y + 9}" width="346" height="6" fill="#eaeef2"/>',
                f'<rect x="50" y="{y + 9}" width="{346 * ratio:.1f}" height="6" fill="{color}"/>',
            ]
        )
    return "\n".join(parts + ["</svg>", ""])


def self_test():
    sample = Counter({"Python": 60, "C#": 30, "A&B": 10})
    assert language_rows(sample, 2) == [("Python", 60), ("C#", 30), ("Other", 10)]
    assert "A&amp;B" in languages_svg(sample)
    ElementTree.fromstring(languages_svg(sample))
    ElementTree.fromstring(overview_svg(3, 12, 5))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("dist"))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("Profile stats self-test passed")
        return

    username = os.environ.get("PROFILE_USERNAME", "KloBraticc")
    token = os.environ.get("GITHUB_TOKEN")
    profile = get_json(f"https://api.github.com/users/{quote(username)}", token)
    repos = [repo for repo in list_repositories(username, token) if not repo.get("fork")]
    languages = Counter()
    skipped = []
    for repo in repos:
        if repo.get("language"):
            result = get_json(repo["languages_url"], token, allow_unavailable=True)
            if result is None:
                skipped.append(repo["name"])
            else:
                languages.update(result)

    stars = sum(repo.get("stargazers_count", 0) for repo in repos)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "profile-overview.svg").write_text(
        overview_svg(len(repos), stars, profile["followers"]), encoding="utf-8"
    )
    (args.output_dir / "profile-languages.svg").write_text(
        languages_svg(languages), encoding="utf-8"
    )
    print(f"Original repos: {len(repos)}, stars: {stars}, followers: {profile['followers']}")
    print("Languages: " + ", ".join(f"{name} {count}" for name, count in language_rows(languages)))
    if skipped:
        print("Unavailable language data: " + ", ".join(skipped))


if __name__ == "__main__":
    main()
