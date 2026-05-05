# Ancient Unfiltered

**Ancient Unfiltered** is a local, zero-build diachronic philology MVP for reading ancient texts with a historical cutoff. Paste a passage, set a year, click a word, and the app opens a collapsible directory tree of source-derived morphology, etymology, and lexicon data.

The project is intentionally modest in v0.1: it is Latin-first, local-first, and evidence-first. It does not choose the "right" parsing, does not translate the passage, and does not invent definitions.

## What You Get

- **Clickable text processing:** paste a passage, press **Process**, and every alphabetic token becomes clickable while punctuation is preserved.
- **Historical cutoff year:** use negative years for BCE, for example `-50` for 50 BCE.
- **Morphological paths:** fetched from the Perseus morphology endpoint and rendered as equal-weight alternatives.
- **Chronological lexicon:** fetched from CLD's Lewis & Short data, then filtered against the cutoff year when citations can be dated.
- **Etymology branch:** fetched from Wiktionary when a Latin etymology section is available.
- **Local SQLite cache:** repeated `(word, cutoff_year)` lookups are stored in `cache.db`.
- **No frontend build:** static HTML, CSS, and vanilla JavaScript served by FastAPI.
- **No API keys:** the MVP uses open web endpoints.

## What It Does Not Do Yet

- It does not run offline for first-time lookups; external endpoints are required until data is cached.
- It does not support Greek parsing as a first-class workflow yet.
- It keeps undated or ambiguous citations and marks them as `date unverified`.
- Dense dictionary entries can still be rough. The filter removes known future author anchors, but v0.1 is not a complete scholarly citation parser.

## Quick Start

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open:

```text
http://127.0.0.1:8000
```

## Try The Caesar Example

The repo includes [examples/caesar_bellum_gallicum_1_1.txt](examples/caesar_bellum_gallicum_1_1.txt), Julius Caesar's *Commentarii de Bello Gallico* 1.1.

Recommended first run:

1. Paste the chapter into the source text box.
2. Set the cutoff year to `-50`.
3. Press **Process**.
4. Click `Gallia`.

Expected shape of the result:

```json
{
  "word": "gallia",
  "query_year": -50,
  "morphology": [
    {"path": "Path A", "pos": "Noun", "lemma": "Gallia", "details": "form: gallia, case: voc, number: sg, gender: fem"},
    {"path": "Path B", "pos": "Noun", "lemma": "Gallia", "details": "form: gallia, case: nom, number: sg, gender: fem"}
  ],
  "etymology": {
    "root": "",
    "literal_meaning": ""
  },
  "lexicon": [
    {
      "sense": "Gallia / CLD JSON / Lewis Short / Sense 1",
      "definition": "Gallia, ae, v. 1. Galli, II. A.",
      "citations": ["No dated citation parsed (date unverified)"]
    }
  ]
}
```

The actual live test returned 15 morphology paths for `Gallia`, including noun and adjective possibilities. The README snippet is shortened so it stays readable.

## Testing

Run the local test suite:

```bash
.venv/bin/python -m unittest discover
```

Validation performed for v0.1 on 2026-05-05:

- `python3 -m py_compile database.py philology.py main.py tests/test_chronology.py` passed.
- `.venv/bin/python -m unittest discover` passed: 7 tests.
- FastAPI smoke test passed with status `200` for `GET /api/query?word=Gallia&year=-50`.
- Live Perseus morphology returned 15 paths for `Gallia`.
- Live CLD Lewis & Short lookup returned the `Gallia, ae, v. 1. Galli, II. A.` dictionary entry.
- Rich lookup `rivalem` returned 3 morphology paths and kept pre-50 BCE citation anchors such as Plautus, Catullus, Naevius, Terence, and Cicero while stripping known later anchors from the citation list.

## Architecture

```text
.
|-- main.py                # FastAPI app and /api/query route
|-- database.py            # SQLite cache
|-- philology.py           # external fetch, parsing, and chronological filter
|-- mempalace.md           # project memory index, not a second spec
|-- requirements.txt
|-- static/
|   |-- index.html
|   |-- style.css
|   `-- script.js
|-- tests/
|   `-- test_chronology.py
`-- examples/
    `-- caesar_bellum_gallicum_1_1.txt
```

## Data Sources

- Perseus Digital Library morphology endpoint.
- CLD/BBAW dictionary API for Lewis & Short descriptions.
- Wiktionary parse API for Latin etymology text when available.

All displayed definitions and citations are passed through from external source data. The app adds only structural labels, chronological filtering, and `date unverified` flags.

## Project Memory

The project scaffold uses a strict single source of truth model. [spec.md](spec.md) is the normative source for product and architecture decisions; [agents.md](agents.md) is the execution plan derived from it; [mempalace.md](mempalace.md) is only a navigation index for project memory.

Ancient texts and examples are evidence inputs with their own provenance. They are not used as the project's governance source of truth.

## License

Ancient Unfiltered is released under the GNU General Public License v3.0 or later. See [LICENSE](LICENSE).
