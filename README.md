# Ancient Unfiltered

**Ancient Unfiltered** is a local, zero-build reading desk for ancient texts. Paste a passage, set a historical cutoff year, click a word, and inspect source-derived morphology, lexicon evidence, etymology, source sentence estimates, translations, and warnings.

The app does not choose the correct interpretation. It exposes evidence and provenance so readers can decide what to do with it.

Public demo:

```text
https://filipzarzynski.github.io/ancient-unfiltered/
```

The demo shows four Greek philosophical examples in English first, then beside
the source Greek and multiple grammar-respecting renderings.

## What v0.2 Gives You

- **Greek and Latin lookup:** `Auto`, `Greek`, and `Latin` modes.
- **Clickable text processing:** alphabetic tokens become keyboard-accessible lookup targets.
- **Chronological cutoff:** negative years are BCE, for example `-399` for 399 BCE.
- **Morphological paths:** all source-reported analyses are shown with equal weight.
- **Chronological lexicon:** Latin uses Lewis & Short through CLD; Greek uses LSJ through CLD when available.
- **Source sentence estimates:** supported Greek citations such as `Pl. Ap. 18a` are retrieved from Perseus when possible.
- **Translation context:** retrieved translations are labeled as context, not interpretation.
- **Local SQLite cache:** repeated `(word, cutoff_year, language)` lookups are cached locally.
- **No API keys and no frontend build:** FastAPI, SQLite, static HTML/CSS/JS.

## What It Still Does Not Do

- It is not an offline corpus. First-time lookups need network access to open endpoints.
- Greek source sentence retrieval is intentionally narrow in v0.2. Plato `Apology` Stephanus citations are supported first.
- Chronological dates are estimates when derived from author/work mappings.
- Undated evidence is retained only with an unverified-date label.
- Dense dictionary prose can still contain source abbreviations that are not fully parsed.

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

## Greek Smoke Example

Use [examples/plato_apology_17a.txt](examples/plato_apology_17a.txt).

Recommended run:

1. Paste the Plato passage.
2. Set language to `Greek`.
3. Set cutoff year to `-399`.
4. Click `κατηγόρων`.

Live v0.2 result on 2026-05-05:

- Status `200`.
- Language resolved to `greek`.
- Perseus Morpheus returned 8 morphology paths for `κατηγόρων`.
- CLD/LSJ returned one lexicon entry for `κατήγορος`.
- Chronology kept pre-cutoff estimated citations including `Hdt. 3.71`, `And. 4.16`, and `Pl. Ap. 18a`.
- Later evidence such as `Apoc. 12.10` and `PFlor. 6.6 (iii AD)` was stripped from the displayed definition.
- The `Pl. Ap. 18a` citation returned a Perseus Greek source sentence estimate.
- Perseus English translation context was attached and labeled as context, not interpretation.

## Latin Regression Example

Use [examples/caesar_bellum_gallicum_1_1.txt](examples/caesar_bellum_gallicum_1_1.txt).

Recommended run:

1. Paste the Caesar passage.
2. Set language to `Latin`.
3. Set cutoff year to `-50`.
4. Click `Gallia`.

Live v0.2 regression result on 2026-05-05:

- Status `200`.
- Language resolved to `latin`.
- Perseus Morpheus returned 15 morphology paths.
- CLD/Lewis & Short returned the `Gallia, ae, v. 1. Galli, II. A.` lexicon entry.

## Architecture

```text
.
|-- main.py                # FastAPI app and /api/query route
|-- database.py            # SQLite cache
|-- philology.py           # high-level orchestration
|-- sources/               # morphology, lexica, passages, etymology, chronology
|-- docs/                  # static GitHub Pages demo
|-- mempalace.md           # project memory index, not a second spec
|-- requirements.txt
|-- static/
|   |-- index.html
|   |-- style.css
|   `-- script.js
|-- tests/
`-- examples/
```

## Project Memory And SSOT

The project scaffold uses a strict single source of truth model. [spec.md](spec.md) is the normative source for product and architecture decisions; [agents.md](agents.md) is the execution plan derived from it; [mempalace.md](mempalace.md) is only a navigation index.

Ancient texts and examples are evidence inputs with their own provenance. They are not used as project governance.

## Testing

```bash
python3 -m py_compile database.py philology.py main.py sources/*.py tests/*.py
.venv/bin/python -m unittest discover
```

Validation performed for v0.2 on 2026-05-05:

- `py_compile` passed.
- Unit tests passed: 14 tests.
- Greek FastAPI smoke test passed for `κατηγόρων`.
- Latin FastAPI regression smoke test passed for `Gallia`.
- Desktop and mobile headless Chrome screenshots rendered without a frontend build step.

## License

Ancient Unfiltered is released under the GNU General Public License v3.0 or later. See [LICENSE](LICENSE).
