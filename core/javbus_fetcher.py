#!/usr/bin/env python3
"""JavBus data fetcher — search by code, extract actress/date/tags/cover.

Data source: https://www.javbus.com
Requires proxy (Clash Verge Allow LAN). Cookies from browser export.

Usage:
    cd /mnt/e/tools/movieTool
    python3 core/javbus_fetcher.py SSIS-280              # search + show detail
    python3 core/javbus_fetcher.py SSIS-280 --cover       # also download cover
    python3 core/javbus_fetcher.py --batch movie_codes.txt  # batch lookup
"""

import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# ── Constants ────────────────────────────────────────────────────────────

BASE_URL = "https://www.javbus.com"
COOKIE_FILE = str(Path(__file__).resolve().parent.parent / "javbus_cookies.json")
REQUEST_TIMEOUT = 15

# ── Data Models ──────────────────────────────────────────────────────────

@dataclass
class MovieInfo:
    code: str = ""
    title: str = ""
    cover_url: str = ""          # big cover from detail page
    thumb_url: str = ""          # small thumb from search results
    release_date: str = ""       # YYYY-MM-DD
    length: str = ""             # e.g. "170分鐘"
    director: str = ""
    studio: str = ""             # 製作商
    label: str = ""              # 發行商
    actresses: list[str] = field(default_factory=list)
    genres: list[str] = field(default_factory=list)
    detail_url: str = ""


# ── Session Factory ──────────────────────────────────────────────────────

def _create_session() -> requests.Session:
    """Create a requests.Session with proxy and cookies."""
    session = requests.Session()
    session.proxies = {"https": "http://172.24.144.1:7890"}
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/148.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })

    # Load cookies from file
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        for name, value in cookies.items():
            session.cookies.set(name, value, domain="www.javbus.com")

    return session


# ── Core API ─────────────────────────────────────────────────────────────

def search(code: str) -> list[MovieInfo]:
    """Search javbus by JAV code. Returns list of matching movies."""
    session = _create_session()
    url = f"{BASE_URL}/search/{code}"
    resp = session.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    for box in soup.select(".movie-box"):
        info = MovieInfo()
        info.code = code

        # Detail link
        detail_href = box.get("href", "")
        if detail_href:
            info.detail_url = urljoin(BASE_URL, detail_href)

        # Thumbnail
        img = box.select_one("img")
        if img:
            info.thumb_url = urljoin(BASE_URL, img.get("src", ""))
            info.title = img.get("title", "")

        # Date from the <date> tag
        dates = box.select("date")
        if len(dates) >= 2:
            info.release_date = dates[1].get_text(strip=True)

        results.append(info)

    return results


def get_detail(url: str, code: str = "") -> MovieInfo:
    """Fetch detail page and extract full metadata."""
    session = _create_session()
    resp = session.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    info = MovieInfo(code=code, detail_url=url)

    # Title
    title_tag = soup.find("title")
    if title_tag:
        raw = title_tag.text.strip()
        # Remove " - JavBus" suffix
        info.title = re.sub(r"\s*[-–]\s*JavBus\s*$", "", raw).strip()

    # Big cover
    big_img = soup.select_one(".bigImage img")
    if big_img:
        info.cover_url = urljoin(BASE_URL, big_img.get("src", ""))

    # Info panel — parse key:value pairs
    info_panel = soup.select_one(".info") or soup.select_one(".col-md-3")
    if info_panel:
        text = info_panel.get_text()

        patterns = {
            "code": r"識別碼:\s*(.+)",
            "release_date": r"發行日期:\s*(\d{4}-\d{2}-\d{2})",
            "length": r"長度:\s*(\d+分鐘)",
            "director": r"導演:\s*(.+)",
            "studio": r"製作商:\s*(.+)",
            "label": r"發行商:\s*(.+)",
        }
        for key, pat in patterns.items():
            m = re.search(pat, text)
            if m:
                setattr(info, key, m.group(1).strip())

    # Genres (类别)
    for a in soup.select('.genre a, a[href*="/genre/"]'):
        genre = a.get_text(strip=True)
        if genre and genre not in ("多選提交", "類別:"):
            info.genres.append(genre)

    # Actresses (演员)
    seen = set()
    for a in soup.select('#star-div a, .star-div a, a[href*="/star/"]'):
        name = a.get_text(strip=True)
        if name and name not in seen:
            info.actresses.append(name)
            seen.add(name)

    return info


def download_cover(url: str, save_dir: str, filename: str = "", referer: str = "") -> str | None:
    """Download cover image to local directory. Returns saved path."""
    session = _create_session()
    headers = {}
    if referer:
        headers["Referer"] = referer
    resp = session.get(url, timeout=REQUEST_TIMEOUT, headers=headers)
    resp.raise_for_status()

    if not filename:
        filename = os.path.basename(url.split("?")[0])
        if not filename or "." not in filename:
            filename = "cover.jpg"

    os.makedirs(save_dir, exist_ok=True)
    path = os.path.join(save_dir, filename)
    with open(path, "wb") as f:
        f.write(resp.content)
    return path


# ── CLI ──────────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="JavBus data fetcher")
    parser.add_argument("code", nargs="?", help="JAV code to search (e.g. SSIS-280)")
    parser.add_argument("--cover", action="store_true", help="Download cover image")
    parser.add_argument("--cover-dir", default="/mnt/e/电影封面",
                        help="Cover download directory")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if not args.code:
        parser.print_help()
        return

    # Search
    results = search(args.code)
    if not results:
        print(f"❌ 未找到番号 {args.code}")
        return

    # Get detail for first result
    movie = results[0]
    if movie.detail_url:
        movie = get_detail(movie.detail_url, args.code)
        time.sleep(0.5)  # polite delay

    if args.json:
        print(json.dumps({
            "code": movie.code,
            "title": movie.title,
            "actresses": movie.actresses,
            "release_date": movie.release_date,
            "length": movie.length,
            "director": movie.director,
            "studio": movie.studio,
            "label": movie.label,
            "genres": movie.genres,
            "cover_url": movie.cover_url,
            "thumb_url": movie.thumb_url,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"番号:     {movie.code}")
        print(f"标题:     {movie.title}")
        print(f"演员:     {', '.join(movie.actresses) if movie.actresses else 'N/A'}")
        print(f"发行日期: {movie.release_date}")
        print(f"时长:     {movie.length}")
        print(f"导演:     {movie.director}")
        print(f"制作商:   {movie.studio}")
        print(f"发行商:   {movie.label}")
        print(f"标签:     {', '.join(movie.genres) if movie.genres else 'N/A'}")
        print(f"封面:     {movie.cover_url}")

    # Download cover
    if args.cover and movie.cover_url:
        path = download_cover(movie.cover_url, args.cover_dir, f"{args.code}.jpg")
        if path:
            print(f"\n✅ 封面已保存: {path}")


if __name__ == "__main__":
    main()
