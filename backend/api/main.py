from fastapi import FastAPI
from pydantic import BaseModel
import json, difflib
from pathlib import Path

app = FastAPI()
CORPUS = [json.loads(l) for l in (Path(__file__).resolve().parents[1] / "data" / "corpus.jsonl").read_text(encoding="utf-8").splitlines()]

class Ask(BaseModel):
    question: str
    lang: str | None = None

@app.post("/ask")
def ask(q: Ask):
    # çok basit: başlıklarda yakın eşleşme, yoksa metin içinde arama
    titles = [d["title"] for d in CORPUS if (q.lang is None or d["lang"]==q.lang)]
    match = difflib.get_close_matches(q.question, titles, n=1, cutoff=0.5)
    if match:
        doc = next(d for d in CORPUS if d["title"]==match[0])
        return {"answer": doc["text"][:800], "source": doc["title"]}
    # fallback: kelime içeriyorsa
    for d in CORPUS:
        if all(w.lower() in d["text"].lower() for w in q.question.split()[:3]):
            return {"answer": d["text"][:800], "source": d["title"]}
    return {"answer":"Bununla ilgili içerik bulamadım. Soruyu biraz daha açabilir misin?","source":None}
