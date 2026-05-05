# spec.md: Ancient Unfiltered v0.2 Product Specification

## 1. Project Overview

**Name:** Ancient Unfiltered
**Release target:** v0.2
**License:** GNU General Public License v3.0 or later
**Current baseline:** v0.1 local Latin-first MVP

Ancient Unfiltered is a local, source-first reading desk for ancient texts. v0.2 expands the v0.1 Latin MVP toward Greek works while improving the interface so it feels useful and inviting to philosophy academics, classicists, students, and independent readers.

The product must never imply that there is one correct interpretation of an ancient text. It must show source data, uncertainty, variants, chronological context, and provenance so readers can do their own interpretive work.

## 2. Core Philosophy

### 2.1. Source-First, Not Authority-First

The app is not an oracle and must never present a dictionary, edition, translation, parser, institution, or model as an authority that settles meaning.

Every returned item must expose its provenance:

- source provider or edition
- retrieved form of the data
- citation, lemma, or passage anchor used
- date or date estimate when available
- confidence level for reconstructed context
- whether the chronology was verified or unverified

When sources disagree, v0.2 must display disagreement as parallel evidence. It must not collapse disagreement into a single preferred answer.

### 2.2. Ancient Words First

The central object is the ancient wording itself, or the best retrievable estimate of that wording from explicit source data.

For every clicked word, v0.2 should try to show:

- the clicked token in its local sentence
- possible lemmas and morphology
- historical meanings available before the cutoff
- etymology with provenance and chronology where possible
- citations that support dictionary senses
- estimated original source sentences behind those citations when retrievable
- translations as optional context, clearly labeled by translator/source/date

Translations are aids. They must not be displayed as interpretations that decide the ancient meaning.

### 2.3. Chronological Humility

The cutoff year is a research lens, not a truth machine. v0.2 must:

- drop lexical senses or citations that are securely later than the cutoff
- retain undated material only when it is marked `date unverified`
- show guessed dates as estimates, not facts
- keep the raw citation text visible whenever possible
- avoid paraphrasing definitions into cleaner modern claims

## 3. v0.2 Product Goals

### 3.1. Greek Works As First-Class Inputs

v0.2 must support Greek reading workflows alongside Latin. Greek cannot be treated as an afterthought or a Roman-adjacent feature.

Minimum Greek targets:

- polytonic Greek tokenization and display
- Greek language mode: `Greek`, `Latin`, and `Auto`
- Greek morphology through Perseus Morpheus or another open academic endpoint
- Greek lexicon lookup through LSJ-compatible open data where available
- Greek etymology retrieval where source data exists
- examples from at least one Greek philosophical or literary work

Suggested v0.2 smoke text:

```text
Plato, Apology 17a
Ὅτι μὲν ὑμεῖς, ὦ ἄνδρες Ἀθηναῖοι, πεπόνθατε ὑπὸ τῶν ἐμῶν κατηγόρων,
οὐκ οἶδα.
```

When using real Greek text in examples, preserve Unicode polytonic Greek in the app and tests.

### 3.2. Source Sentence Estimation

For dictionary citations such as `Plat. Ap. 17a`, `Hom. Il. 1.1`, or `Arist. Metaph. 980a`, the app should attempt to retrieve the cited passage and extract the sentence or nearest explicit context containing the cited word or lemma.

The UI label must be `Source sentence estimate`, not `Original sentence`, unless the endpoint provides a clearly identified source passage.

The backend must return:

- canonical citation string
- source provider
- retrieved passage text
- sentence or context window
- match strategy: exact token, normalized token, lemma match, citation-only context, or failed
- confidence: high, medium, low, or unavailable

If retrieval fails, the app should show the citation and a clear `source sentence unavailable` state.

### 3.3. Minimal, Appealing, Accessible UI

The v0.2 interface should feel like a quiet research desk rather than a technical demo.

Design direction:

- calm, readable typography with excellent Greek and Latin support
- restrained color palette with enough contrast for WCAG 2.2 AA
- no decorative excess, no marketing hero screen, no card-heavy clutter
- text reading area remains the first screen
- side panel becomes an evidence drawer with clean tabs or grouped sections
- preserve collapsible evidence trees, but make them easier to scan
- keep equal visual weight for competing analyses

Accessibility requirements:

- full keyboard workflow
- visible focus states
- semantic HTML landmarks
- ARIA labels only where native semantics are insufficient
- screen-reader-friendly loading and error states
- no information conveyed by color alone
- responsive layout for phones, tablets, and desktop
- reduced-motion support

## 4. Architecture

v0.2 must preserve the v0.1 local-first architecture.

```text
.
|-- main.py                # FastAPI app and routes
|-- database.py            # SQLite cache
|-- philology.py           # existing shared parsing/filter logic
|-- sources/               # v0.2 source clients and parsers
|   |-- morphology.py
|   |-- lexica.py
|   |-- passages.py
|   `-- etymology.py
|-- static/
|   |-- index.html
|   |-- style.css
|   `-- script.js
|-- tests/
|-- examples/
`-- README.md
```

No frontend build step is allowed. The frontend remains vanilla HTML, CSS, and JavaScript.

The backend remains FastAPI plus Uvicorn. The cache remains local SQLite. New dependencies are allowed only when they remove real parser fragility or are needed for robust Greek handling.

## 5. Data Model

The v0.2 response should extend, not break, the v0.1 shape.

```json
{
  "word": "logos",
  "display_word": "logos",
  "language": "greek",
  "query_year": -350,
  "local_context": {
    "sentence": "raw user sentence containing the selected token",
    "token_index": 4
  },
  "morphology": [
    {
      "path": "Path A",
      "lemma": "logos",
      "pos": "Noun",
      "details": "nominative singular masculine",
      "source": "Perseus Morpheus",
      "confidence": "source-reported"
    }
  ],
  "etymology": {
    "items": [
      {
        "text": "source-derived etymology text",
        "source": "Wiktionary or other open source",
        "date_status": "unverified"
      }
    ]
  },
  "lexicon": [
    {
      "sense": "source sense label",
      "definition": "source definition text",
      "source": "LSJ",
      "date_status": "verified",
      "citations": [
        {
          "raw": "Plat. Ap. 17a",
          "estimated_year": -399,
          "date_status": "estimated",
          "source_sentence": {
            "text": "retrieved Greek sentence or context window",
            "provider": "Perseus or other open text source",
            "match_strategy": "citation-only context",
            "confidence": "medium"
          }
        }
      ]
    }
  ],
  "translations": [
    {
      "text": "source translation excerpt",
      "source": "translator and edition",
      "passage": "Plat. Ap. 17a",
      "role": "context only"
    }
  ],
  "warnings": [
    "No single branch is selected as correct."
  ]
}
```

## 6. Backend Requirements

### 6.1. Language Detection And Routing

The API must accept:

```text
GET /api/query?word={word}&year={cutoff_year}&language={auto|latin|greek}
```

Routing rules:

- `latin` uses the existing Latin pipeline.
- `greek` uses the Greek pipeline.
- `auto` detects Unicode script first, then falls back to the selected UI language.
- mixed or ambiguous tokens must return a warning rather than a guessed certainty.

### 6.2. Greek Morphology

Implement Greek morphology as a separate source client. Preserve all returned analyses. Do not pick a preferred parse.

Required parser behavior:

- handle polytonic Unicode
- normalize for lookup without losing display form
- retain source lemma, part of speech, and inflection details
- deduplicate exact duplicates only
- expose endpoint failures as source warnings

### 6.3. Greek Lexicon

Implement LSJ-compatible lookup where open data is available. The parser must keep raw sense labels, definitions, and citations.

Chronological filtering must apply to Greek authors and works, including approximate mappings for Homer, Hesiod, Herodotus, Thucydides, Plato, Xenophon, Aristotle, the tragedians, and Hellenistic sources.

All mappings are estimates and must be labeled as such.

### 6.4. Source Sentence Retrieval

Create a passage retrieval layer that can parse common citations and try candidate open-text endpoints.

The retrieval layer must:

- never fabricate a passage
- return no passage when none is retrieved
- keep provider and citation metadata
- show match confidence
- support context windows when sentence splitting is uncertain
- preserve ancient-language text as returned by the source

### 6.5. Translations

Translations may be shown only as sourced context.

The UI must label translation blocks as:

```text
Translation context, not interpretation
```

Lexical meanings and etymologies must obey the ancient cutoff. Translation context must be tied to the same ancient passage or citation, and translation edition dates must be shown when available. If translation metadata is missing, mark `translation date unverified`.

## 7. Frontend Requirements

### 7.1. Reading Desk Layout

First viewport:

- source text input or reading pane
- compact language and cutoff controls
- process action
- evidence drawer

Evidence drawer sections:

- Word
- Morphology
- Lexicon by cutoff
- Source sentence estimates
- Etymology
- Translation context
- Source warnings

The UI must avoid ranking words, senses, translations, or analyses.

### 7.2. Accessibility

Required manual checks:

- tab through the full app without a mouse
- activate a token with Enter and Space
- use the app at 320px width
- use the app at 200% browser zoom
- verify focus indicators
- verify loading state is announced or visible text changes
- verify color contrast for text and controls

## 8. Testing Plan

### 8.1. Unit Tests

Add tests for:

- Greek tokenization
- Unicode normalization
- language detection
- Greek author date estimation
- chronology filtering for Greek citations
- source sentence retrieval fallback behavior
- equal-weight rendering data structures

### 8.2. Smoke Tests

Run one Greek work and one Latin work.

Required Greek smoke test:

- one chapter, section, or short passage from Plato, Homer, Aristotle, or another ancient Greek work
- at least one clicked Greek word
- cutoff set before and after a major cited author to verify filtering
- source sentence estimation documented in README

Required Latin regression smoke test:

- repeat the v0.1 Caesar `Gallia` example
- confirm Latin behavior still works

### 8.3. UI Tests

At minimum:

- desktop screenshot review
- mobile screenshot review
- keyboard-only lookup flow
- no overlapping text at narrow widths
- no frontend dependency or build tool introduced

## 9. Release Criteria For v0.2

v0.2 is ready only when:

- Greek lookup works for at least one real Greek passage.
- Latin v0.1 behavior still passes.
- every displayed data item has provenance or an explicit warning.
- source sentence estimates are labeled as estimates.
- no UI element suggests the correct interpretation.
- all tests pass.
- README documents Greek and Latin examples with real outcomes.
- the app still runs with `pip install -r requirements.txt && uvicorn main:app --reload`.
