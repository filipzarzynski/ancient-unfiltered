# spec.md: Local Diachronic Philology Engine

## 1. Project Overview
**Name:** Local Diachronic Philology Engine  
**License:** GNU General Public License v3.0 (GPL-3)  
**Objective:** Build a minimalist, locally-hosted, text-agnostic tool for empirical ancient language study. The application must process user-provided text, allow the user to set a historical "cutoff date," and dynamically fetch morphological, etymological, and temporally-bounded lexical data for any clicked word using external academic APIs.
**Core Philosophy:** Zero editorializing, zero human curation. The tool presents raw empirical data (ambiguous grammatical paths, etymological roots, and historical usages) bounded strictly by the user's timeline.

---

## 2. System Architecture & Tech Stack
The application must be a lightweight, easily distributable local web server bundle with no complex build steps (no Node.js/Webpack required for the frontend).

*   **Backend:** Python 3.10+, FastAPI (for async API handling), Uvicorn (local server).
*   **Frontend:** Vanilla HTML5, CSS3, and Vanilla JavaScript. (Tailwind CSS via CDN is acceptable for rapid UI styling).
*   **Database/Caching:** Local SQLite (`cache.db`) accessed via Python's built-in `sqlite3` or `SQLAlchemy`.
*   **External APIs:** Perseus Digital Library API / Logeion API (for morphology and lexicon) and standard Wiktionary parsers (for etymology).

### 2.1. Target File Structure
```text
/diachronic-engine
├── main.py               # FastAPI server application and API routes
├── requirements.txt      # Python dependencies (fastapi, uvicorn, httpx, etc.)
├── database.py           # SQLite caching logic
├── /static
│   ├── index.html        # Main UI
│   ├── style.css         # Styling for the text and directory tree
│   └── script.js         # Client-side logic (text wrapping, fetch requests, UI state)
└── README.md             # Setup and run instructions (GPL-3 notice)
```

---

## 3. Core Requirements & Logic Flow

### 3.1. Initialization & UI Setup
*   **Input Area:** The frontend must provide a `textarea` for the user to paste any text (ancient or translated) and a `number` input field for the **Cutoff Year** (e.g., `-50` for 50 BCE, `150` for 150 CE).
*   **Render Action:** A "Process Text" button that takes the input string, tokenizes it by whitespace/punctuation, and wraps every word in a clickable HTML `<span>` with a distinct class (e.g., `<span class="interactive-word">rivalem</span>`).

### 3.2. Query Execution (Frontend -> Backend)
*   When a user clicks an `.interactive-word`, the JS extracts the inner text, normalizes it (removes punctuation, converts to lowercase), and sends an HTTP GET request to the local backend: `GET /api/query?word={word}&year={cutoff_year}`.
*   The frontend displays a loading state on the UI side-panel while waiting.

### 3.3. Backend Processing & API Orchestration (Python)
1.  **Cache Check:** Query the local SQLite database for the tuple `(word, cutoff_year)`. If valid JSON exists, return it immediately.
2.  **Morphology Fetch:** Hit the Perseus/Logeion morphological analyzer endpoint to retrieve all possible lemmas and grammatical parsings.
3.  **Lexicon Fetch:** Iterate through the retrieved lemmas and hit the lexicon endpoints (e.g., Lewis & Short for Latin, LSJ for Greek) to retrieve full definitions and citations.
4.  **Etymology Fetch:** Query available etymology endpoints to extract root words and literal constructions.
5.  **Chronological Filter (Crucial):** Parse the citation dates from the lexicon payload. **Strictly remove** any sense, definition, or citation that is chronologically dated *after* the `cutoff_year` provided by the user.
6.  **Data Formatting:** Structure the surviving data into the standardized JSON response format.
7.  **Cache & Return:** Save the structured JSON to SQLite and return it to the frontend.

### 3.4. Target JSON Response Schema
```json
{
  "word": "rivalem",
  "query_year": -50,
  "morphology": [
    {"path": "Path A", "pos": "Noun", "lemma": "rivalis", "details": "Accusative, Singular, Masculine"},
    {"path": "Path B", "pos": "Adjective", "lemma": "rivalis", "details": "Accusative, Singular"}
  ],
  "etymology": {
    "root": "rivus",
    "literal_meaning": "pertaining to the same stream/brook"
  },
  "lexicon": [
    {
      "sense": "Sense I: Literal",
      "definition": "One who uses the same brook or water source.",
      "citations": ["Ulpian, Digest (Historical anchor)"]
    },
    {
      "sense": "Sense II: Transferred (Social/Economic)",
      "definition": "A competitor, one who strives for the same objective.",
      "citations": ["Plautus, Stichus - 200 BCE"]
    }
  ]
}
```

---

## 4. UI/UX Specifications: The Empirical Directory Tree

The parsed data must be rendered in a side-panel or floating modal using a collapsible **Directory Tree (Accordion)** structure. This prevents information overload and reflects the raw, relational nature of the data.

### 4.1. Tree Structure Layout
*   **Root Node:** `▾ [Selected Word]`
    *   **Branch 1:** `▾ 1. Morphological Paths`
        *   `▸ [Path A Data]`
        *   `▸ [Path B Data]`
    *   **Branch 2:** `▾ 2. Etymological Topology`
        *   `▪ Root: [Root Data]`
        *   `▪ Literal: [Literal Meaning]`
    *   **Branch 3:** `▾ 3. Chronological Lexicon (pre-[Year])`
        *   `▾ Sense I: [Definition]`
            *   `▸ Citations`
        *   `▾ Sense II: [Definition]`
            *   `▸ Citations`

### 4.2. Interaction Rules
*   Branches must be individually collapsible/expandable via vanilla JavaScript.
*   The software must **never** highlight one morphological path or lexical sense as the "correct" one. All branches hold equal visual weight.

---

## 5. Implementation Phases for AI Agent

*   **Phase 1: Local Server & Caching Boilerplate**
    *   Create `main.py` with FastAPI.
    *   Implement SQLite setup and basic `/api/query` route (returning dummy data).
    *   Create `static/index.html` and wire up the FastAPI static file serving.
*   **Phase 2: Frontend Text Processing**
    *   Implement JS to take text input, tokenize it, wrap words in spans, and render them to the DOM.
    *   Add click event listeners to words that trigger a `fetch()` to the local API.
*   **Phase 3: External API Integration**
    *   Implement HTTPX client in Python to fetch from Perseus/Logeion APIs based on the incoming word.
    *   Implement XML/JSON parsing to extract Morphology and Lexicon data.
*   **Phase 4: The Chronological Filter**
    *   Write the logic to parse historical dates/authors from the lexicon data.
    *   Implement the comparison logic against `cutoff_year` to drop future definitions.
*   **Phase 5: UI Construction**
    *   Write the JS logic to dynamically build the DOM elements for the Collapsible Directory Tree based on the JSON response.
    *   Apply minimalist, academic CSS styling.
