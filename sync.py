#!/usr/bin/env python3
"""Sync words.tsv into the local Anki app via AnkiConnect, then sync to AnkiWeb.

Requires Anki running with the AnkiConnect add-on (code 2055492159).
Notes are matched by the "Deutsch" field: new rows are added, changed rows
are updated in place (review history is kept). Nothing is ever deleted.

Usage: python3 sync.py [--no-web-sync] [--dry-run]
"""
import csv
import json
import sys
import urllib.request
from pathlib import Path

DECK = "Deutsch DShatrov"
MODEL = "deutsch-dshatrov"
FIELDS = ["Deutsch", "Russisch", "Notiz", "Beispiel"]
TSV = Path(__file__).with_name("words.tsv")
URL = "http://127.0.0.1:8765"

CSS = """
.card { font-family: -apple-system, Helvetica, sans-serif; font-size: 24px;
        text-align: center; color: #222; background: #fff; }
.de { font-size: 30px; font-weight: 600; }
.extra { font-size: 18px; color: #666; margin-top: 14px; }
.ex { font-size: 18px; font-style: italic; margin-top: 8px; }
.nightMode .card, .night_mode .card { color: #eee; background: #1e1e1e; }
.nightMode .extra, .night_mode .extra { color: #aaa; }
"""
EXTRA = (
    '{{#Notiz}}<div class="extra">{{Notiz}}</div>{{/Notiz}}'
    '{{#Beispiel}}<div class="ex">{{Beispiel}}</div>{{/Beispiel}}'
)
TEMPLATES = [
    {
        "Name": "DE → RU",
        "Front": '<div class="de">{{Deutsch}}</div>',
        "Back": '{{FrontSide}}<hr id="answer"><div>{{Russisch}}</div>' + EXTRA,
    },
]


def anki(action, **params):
    req = json.dumps({"action": action, "version": 6, "params": params}).encode()
    try:
        with urllib.request.urlopen(URL, req, timeout=60) as resp:
            out = json.load(resp)
    except OSError as e:
        sys.exit(f"AnkiConnect недоступен ({e}). Запусти Anki и установи AnkiConnect (2055492159).")
    if out.get("error"):
        raise RuntimeError(f"{action}: {out['error']}")
    return out["result"]


def html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def load_rows():
    with TSV.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))
    seen = set()
    for r in rows:
        key = r["deutsch"].strip()
        if key in seen:
            sys.exit(f"Дубликат в words.tsv: {key}")
        seen.add(key)
    return rows


def ensure_model():
    if MODEL in anki("modelNames"):
        anki("updateModelStyling", model={"name": MODEL, "css": CSS})
        anki("updateModelTemplates", model={
            "name": MODEL,
            "templates": {t["Name"]: {"Front": t["Front"], "Back": t["Back"]} for t in TEMPLATES},
        })
        return
    anki("createModel", modelName=MODEL, inOrderFields=FIELDS, css=CSS, cardTemplates=TEMPLATES)


def main():
    dry = "--dry-run" in sys.argv
    rows = load_rows()

    if not dry:
        ensure_model()
        anki("createDeck", deck=DECK)

    ids = anki("findNotes", query=f'"deck:{DECK}" "note:{MODEL}"')
    existing = {n["fields"]["Deutsch"]["value"]: n for n in anki("notesInfo", notes=ids)}

    added = updated = 0
    for r in rows:
        fields = {
            "Deutsch": html(r["deutsch"].strip()),
            "Russisch": html(r["russisch"].strip()),
            "Notiz": html(r["notiz"].strip()),
            "Beispiel": html(r["beispiel"].strip()),
        }
        tags = r["tags"].split()
        note = existing.pop(fields["Deutsch"], None)
        if note is None:
            print(f"+ {r['deutsch']}")
            added += 1
            if not dry:
                anki("addNote", note={"deckName": DECK, "modelName": MODEL, "fields": fields,
                                      "tags": tags, "options": {"allowDuplicate": False}})
            continue
        cur = {k: v["value"] for k, v in note["fields"].items()}
        if cur != fields or sorted(note["tags"]) != sorted(tags):
            print(f"~ {r['deutsch']}")
            updated += 1
            if not dry:
                anki("updateNote", note={"id": note["noteId"], "fields": fields, "tags": tags})

    for key in existing:
        print(f"? в Anki есть, в words.tsv нет: {key}")

    print(f"Добавлено: {added}, обновлено: {updated}, всего в файле: {len(rows)}")
    if not dry and "--no-web-sync" not in sys.argv:
        anki("sync")
        print("Синхронизировано с AnkiWeb.")


if __name__ == "__main__":
    main()
