# backend/scraper/crawl.py
import time, json, re, os
from urllib.parse import urljoin, urldefrag, urlparse, parse_qs
import httpx
from selectolax.parser import HTMLParser
import urllib.robotparser as rp
from collections import deque
from pathlib import Path

BASE = "https://turkkep.com.tr"
ALLOW_SUBDOMAINS = {"turkkep.com.tr"}  # gerekirse {"turkkep.com.tr","edefter.turkkep.com.tr"} yap
OUT_RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
OUT_RAW.mkdir(parents=True, exist_ok=True)

def allowed(url, robots):
    try:
        return robots.can_fetch("*", url)
    except Exception:
        return True  # robots cevap vermezse fail-open etme, logla

def normalize_link(href, base):
    if not href:
        return None
    href = urljoin(base, href)
    href, _ = urldefrag(href)  # #anchor at
    u = urlparse(href)
    # Sadece aynı etki alanı (ve izin verilen alt alanlar)
    if u.netloc not in ALLOW_SUBDOMAINS:
        return None
    # istenmeyen query’ler: ?replytocom=..., ?share=..., vb.
    q = parse_qs(u.query)
    bad_q = {"replytocom", "share"}
    if bad_q & set(q.keys()):
        return None
    return href

def extract_links(html, base):
    tree = HTMLParser(html)
    links = set()
    for a in tree.css("a[href]"):
        href = a.attributes.get("href")
        n = normalize_link(href, base)
        if n:
            links.add(n)
    return links

def crawl(start=BASE, max_pages=5000, delay=0.7):
    robots = rp.RobotFileParser()
    robots.set_url(urljoin(BASE, "/robots.txt"))
    try:
        robots.read()
    except Exception:
        pass

    seen, q = set(), deque([start, f"{start}/cozumler/", f"{start}/iletisim/", f"{start}/?lang=en"])
    client = httpx.Client(headers={"User-Agent":"gygess-crawler/0.1"}, timeout=20.0, follow_redirects=True)

    while q and len(seen) < max_pages:
        url = q.popleft()
        if url in seen or not allowed(url, robots):
            continue
        seen.add(url)
        try:
            r = client.get(url)
            if r.status_code != 200 or "text/html" not in r.headers.get("content-type",""):
                continue
            # kaydet
            fname = re.sub(r"[^a-zA-Z0-9]+","_", url.replace("https://",""))[:120] + ".html"
            (OUT_RAW / fname).write_bytes(r.content)
            # linkler
            for link in extract_links(r.text, url):
                if link not in seen:
                    q.append(link)
            time.sleep(delay)
        except Exception:
            continue

if __name__ == "__main__":
    crawl()
