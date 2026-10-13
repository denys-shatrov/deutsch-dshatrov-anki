# deutsch-dshatrov — Anki deck from a handwritten notebook

The user writes German words with Russian translations in a paper notebook, photographs the pages and drops the photos into this folder. When they say something like "залил фото" / "новые фото", do the whole pipeline below without asking what they want. Talk to the user in Russian.

## Pipeline for new photos

1. **Find new photos**: image files (`*.JPG`, `*.jpeg`, `*.png`, `*.HEIC`, …) in the project root. Already-processed photos live in `photos/` (gitignored), never re-read those.
2. **Read them**: resize first (`sips -Z 1800 <img> --out <scratchpad>/<img>`; HEIC → add `-s format jpeg`), then Read the resized copy.
3. **Transcribe** only entries not already in `words.tsv` (match by the German side).
4. **Append rows to `words.tsv`** — tab-separated, header `deutsch russisch notiz beispiel tags`, no quotes, no tabs inside values.
   - `deutsch`: word/phrase as written; add the correct article to nouns if the user omitted it.
   - `russisch`: the user's translation, keep their wording.
   - `notiz`: extra explanations (etymology "образовано от…", definitions, word breakdowns, plural/singular notes).
   - `beispiel`: usage examples ("Änderungen verfolgen — отслеживать изменения").
   - `tags`: notebook batch — `heft1` so far; keep using it unless the user starts a new notebook.
   - If an entry has only an explanation and no translation, derive a short translation from the user's own words and mention it.
5. **Move processed photos** into `photos/`.
6. **Push to Anki**: `python3 sync.py` (adds new notes, updates changed ones, then triggers AnkiWeb sync so the phone can pull). Use `--dry-run` to preview. If it says AnkiConnect is unavailable, ask the user to start Anki.
7. **Commit and push to git — one commit per day.** Commit message is ONLY the date (YYYY-MM-DD) — no description, no Co-Authored-By trailer.
   - If the latest commit's message is not today's date (`git log -1 --format=%s` ≠ `$(date +%F)`): `git add -A && git commit -m "$(date +%F)" && git push`.
   - If it already is today's date: fold changes into it — `git add -A && git commit --amend --no-edit && git push --force-with-lease`. The user explicitly wants this (force-push of today's commit only); if the permission prompt/classifier blocks it, ask the user to run the push with `! git push --force-with-lease`.
8. **Report briefly**: how many words added, list anything hard to read or ambiguous, and any corrections/articles you added.

## Setup facts

- **Git identity**: this repo uses a DIFFERENT identity than the global one (`Denys Shatrov <denys.shatrov@gmail.com>`, GitHub `denys-shatrov`), set in local `.git/config`. Never use `--global`, never change it. Remote: `https://denys-shatrov@github.com/denys-shatrov/deutsch-dshatrov-anki.git`.
- **Anki**: desktop Anki with the AnkiConnect add-on (2055492159) on `127.0.0.1:8765`. Profile «1-й пользователь», synced with AnkiWeb; the user syncs the phone from AnkiWeb.
- **Deck** `Deutsch DShatrov` (the user's only deck), **note type** `deutsch-dshatrov` with fields Deutsch / Russisch / Notiz / Beispiel, one card per note: DE → RU only (user's choice — no reverse cards).
- `sync.py` matches notes by the `Deutsch` field and never deletes anything from Anki; it only prints notes that exist in Anki but not in `words.tsv`.

## Gotchas seen before

- Right after `sync.py` triggers the AnkiWeb sync, AnkiConnect returns "Collection lifecycle operation is active" for a while — wait, don't treat it as failure.
- If AnkiWeb sync needs a one-way full sync, Anki shows an Upload/Download dialog the user must answer. Desktop has the fresh data → tell them **Upload** on desktop, **Download** on phone.
- Sync error «Используйте функцию "Проверить базу данных"…» → run `guiCheckDatabase` via AnkiConnect, then sync again; if it persists, the user forces a one-way sync (Settings → Синхронизация) and uploads.
- Deleting decks or other destructive Anki changes: only when the user asks.
