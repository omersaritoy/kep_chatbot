# backend/scraper/parse.py
import json, re
from pathlib import Path
from selectolax.parser import HTMLParser

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
OUT_FILE = Path(__file__).resolve().parents[1] / "data" / "corpus.jsonl"

def clean_text(t):
    t = re.sub(r"\s+", " ", t or "").strip()
    return t

def detect_lang(doc):
    return "en" if "?lang=en" in doc.get("url","") else "tr"

def parse_file(p: Path):
    html = p.read_text("utf-8", errors="ignore")
    tree = HTMLParser(html)
    title = clean_text(tree.css_first("title").text() if tree.css_first("title") else "")
    # sayfadaki içerik bloğunu yakala (WordPress teması genelde .entry-content/.content)
    main = tree.css_first("main") or tree.css_first(".entry-content") or tree.css_first(".content") or tree.body
    text = clean_text(main.text(separator=" ").strip()) if main else ""
    # çok kısa/boş sayfaları at
    if len(text) < 200:
        return None
    return {
        "url": p.name,         # istersen gerçek URL’yi dosya adına değil ayrı meta’da tut
        "title": title,
        "text": text,
        "lang": detect_lang({"url": p.name}),
    }

def run():
    seen = set()
    with OUT_FILE.open("w", encoding="utf-8") as out:
        for f in RAW_DIR.glob("*.html"):
            doc = parse_file(f)
            if not doc: 
                continue
            key = (doc["title"], doc["lang"])
            if key in seen: 
                continue
            seen.add(key)
            out.write(json.dumps(doc, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    run()
