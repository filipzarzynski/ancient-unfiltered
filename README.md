# Ancient Unfiltered

**Ancient Unfiltered** is a local, zero-build reading desk for ancient texts. Paste a passage, set a historical cutoff year, click a word, and inspect source-derived morphology, lexicon evidence, etymology, source sentence estimates, translations, and warnings.

The app does not choose the correct interpretation. It exposes evidence and provenance so readers can decide what to do with it.

Public demo:

```text
https://filipzarzynski.github.io/ancient-unfiltered/
```

The demo shows the v0.3 matched-pair corpus model with 16 Greek
philosophical examples, each pairing a familiar English reception with cited
Greek wording, swappable meaning paths, and example alternative renderings.

## What v0.3 Gives You

- **Greek and Latin lookup:** `Auto`, `Greek`, and `Latin` modes.
- **Clickable text processing:** alphabetic tokens become keyboard-accessible lookup targets.
- **Chronological cutoff:** negative years are BCE, for example `-399` for 399 BCE.
- **Morphological paths:** all source-reported analyses are shown with equal weight.
- **Chronological lexicon:** Latin uses Lewis & Short through CLD; Greek uses LSJ through CLD when available.
- **Source sentence estimates:** supported Greek citations such as `Pl. Ap. 18a` are retrieved from Perseus when possible.
- **Translation context:** retrieved translations are labeled as context, not interpretation.
- **Local SQLite cache:** repeated `(word, cutoff_year, language)` lookups are cached locally.
- **Matched-pair corpus explorer:** 16 Greek philosophical seed entries grouped by friendship, community, intelligence, and love.
- **Path explorer:** token-level branch choices stay visually equal and update a selected-path preview.
- **Local corpus authoring:** users can add matched pairs with required provenance, keep them in browser storage, and export JSON evidence proposals.
- **Corpus import validation:** provenance-free imports are rejected before entering the local corpus.
- **No API keys and no frontend build:** FastAPI, SQLite, static HTML/CSS/JS.

## v0.3 Corpus Model

v0.3 adds a downloadable matched-pair corpus:

- predefined English reception sentence
- cited original-language wording
- token-level grammar and meaning paths
- example selected-path alternative translation
- local user-added corpus entries
- JSON import/export for repository submission and review

The seed corpus is served at:

```text
docs/corpus/v0.3-seed.json
```

The local API exposes:

```text
GET  /api/corpus/seed
POST /api/corpus/validate
POST /api/corpus/export
POST /api/corpus/import
```

## What It Still Does Not Do

- It is not an offline corpus. First-time lookups need network access to open endpoints.
- Greek source sentence retrieval is intentionally narrow. Plato `Apology` Stephanus citations are supported first.
- Local corpus entries are browser-local until exported.
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

The static public demo is also available from the local server:

```text
http://127.0.0.1:8000/demo/
```

## Corpus Explorer Example

Recommended run:

1. Open `http://127.0.0.1:8000`.
2. Select `Corpus explorer`.
3. Choose `intelligence - Plato, Apology 21d`.
4. Click a Greek token such as `οἶδα` to populate the evidence drawer.
5. Change one or more branch choices and export local JSON after adding a local entry.

Live v0.3 local result on 2026-05-05:

- Seed corpus endpoint returned 16 entries.
- The browser explorer loaded all seed entries.
- Local entry validation rejected missing `critical_original.source_url`.
- Export/import roundtrip preserved `selected_paths`.

## Greek Smoke Example

Use [examples/plato_apology_17a.txt](examples/plato_apology_17a.txt).

Recommended run:

1. Paste the Plato passage.
2. Set language to `Greek`.
3. Set cutoff year to `-399`.
4. Click `κατηγόρων`.

Live v0.3 regression result on 2026-05-05:

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

Live v0.3 regression result on 2026-05-05:

- Status `200`.
- Language resolved to `latin`.
- Perseus Morpheus returned 15 morphology paths.
- CLD/Lewis & Short returned the `Gallia, ae, v. 1. Galli, II. A.` lexicon entry.

## Architecture

```text
.
|-- main.py                # FastAPI app, /api/query, and /api/corpus routes
|-- corpus.py              # v0.3 corpus validation/import/export
|-- database.py            # SQLite cache
|-- philology.py           # high-level orchestration
|-- sources/               # morphology, lexica, passages, etymology, chronology
|-- docs/                  # static GitHub Pages demo
|   `-- corpus/            # v0.3 seed corpus
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
python3 -m py_compile corpus.py database.py philology.py main.py sources/*.py tests/*.py
.venv/bin/python -m unittest discover
```

Validation performed for v0.3 on 2026-05-05:

- `py_compile` passed.
- Unit tests passed: 21 tests.
- Greek FastAPI smoke test passed for `κατηγόρων`.
- Latin FastAPI regression smoke test passed for `Gallia`.
- Corpus API smoke test passed for `/api/corpus/seed`.
- Invalid corpus import rejected missing provenance.
- Export/import roundtrip preserved selected path data.
- Desktop and mobile headless Chrome screenshots rendered without a frontend build step.

## License

Ancient Unfiltered is released under the GNU General Public License v3.0 or later. See [LICENSE](LICENSE).
