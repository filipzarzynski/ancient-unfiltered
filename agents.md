# agents.md: Autonomous Execution Directives
**Project:** Local Diachronic Philology Engine  
**Target Model:** GPT-5.5 (Extra High Effort / Deep Reasoning Enabled)  
**Reference Document:** `spec.md`  

## 1. Meta-Directive for the Primary Orchestrator (Codex Agent)
You are the Lead Autonomous Developer. Your objective is to read `spec.md` and this `agents.md` file to generate the complete, functioning source code for the "Local Diachronic Philology Engine". 

You will execute this build sequentially, adopting specific sub-agent personas for each phase. Do not skip phases. After completing each phase, self-verify the code against the "Strict Guardrails" before proceeding to the next.

### Strict Guardrails (Global Rules)
1.  **No Node.js/NPM on the Frontend:** The frontend MUST be zero-build Vanilla JS, HTML, and CSS. Do not generate `package.json`, React components, or Webpack configs for the frontend.
2.  **Local Execution Only:** The backend MUST be a single Python FastAPI application (`main.py`) running via Uvicorn. No cloud databases; use local SQLite (`sqlite3` standard library).
3.  **Zero Hallucination in Data:** The chronological filter is the core product. The agent must write robust parsing logic to extract dates from external API payloads (Perseus/Logeion) and strictly drop data past the user's cutoff year. Do not allow the LLM to "guess" definitions; surface only API-retrieved data.
4.  **GPL-3 Compliance:** Include standard GPL-3 headers in all major files.

---

## 2. Sub-Agent Prompts & Execution Phases

### Phase 1: Scaffolding & Local Backend Agent
**Persona:** Python Systems Architect
**Objective:** Set up the project structure, SQLite database, and FastAPI boilerplate.
**Instructions:**
1.  Generate `requirements.txt` containing strictly what is needed (e.g., `fastapi`, `uvicorn`, `httpx`, `beautifulsoup4` or `lxml`).
2.  Write `database.py`. Implement a simple SQLite initialization that creates a table `cache` with columns: `word` (TEXT), `cutoff_year` (INTEGER), and `response_data` (JSON). Include functions to `get_cached_query` and `set_cached_query`.
3.  Write `main.py`. Initialize the FastAPI app. Mount a `/static` directory for the frontend. Create a dummy `/api/query` GET endpoint that accepts `word` and `year` and returns a mock JSON matching the schema in `spec.md`.
4.  **Self-Correction Check:** Ensure CORS is not an issue since static files are served directly from the FastAPI Uvicorn instance.

### Phase 2: Frontend DOM & Interaction Agent
**Persona:** Vanilla JavaScript UI/UX Expert
**Objective:** Build the interface, text tokenizer, and DOM manipulation logic.
**Instructions:**
1.  Create `static/index.html` with a minimalist UI: A `textarea` for input, a `number` input for the Cutoff Year, a "Process" button, a main display area for the text, and a side-panel for the Directory Tree.
2.  Create `static/style.css`. Implement clean, academic styling. Use Flexbox/Grid for layout. Style the `.interactive-word` class (e.g., subtle dashed underline, cursor pointer) and the nested accordion structure.
3.  Write `static/script.js`.
    *   Write a tokenizer that takes the textarea input, splits by word boundaries while preserving punctuation, and wraps purely alphabetic strings in `<span class="interactive-word">`.
    *   Add event delegation to the main display area to catch clicks on `.interactive-word`.
    *   On click, fetch from `/api/query?word={clicked_word}&year={cutoff_year}`.
    *   Write the render function `buildDirectoryTree(jsonData)` that recursively generates collapsible HTML `<details>` and `<summary>` tags for the Morphology, Etymology, and Lexicon branches.

### Phase 3: External API & Philological Parsing Agent
**Persona:** Computational Linguist & Data Engineer
**Objective:** Connect FastAPI to Perseus/Logeion APIs and parse the complex XML/JSON responses.
**Instructions:**
1.  Update the `/api/query` endpoint in `main.py` to use asynchronous HTTP requests (`httpx.AsyncClient`).
2.  **Morphology Logic:** Query the Perseus morphological analyzer (`http://www.perseus.tufts.edu/hopper/xmlmorph?lang=la&text={word}`). Parse the returned XML to extract all `<lemma>` and `<pos>` elements. Map these into "Morphological Paths".
3.  **Lexicon Logic:** For each lemma, query the appropriate lexicon (e.g., Lewis & Short for Latin). *Note to Agent: You may need to utilize the Logeion API or Perseus dictionary endpoints. Write robust error handling if an endpoint 404s.*
4.  Extract the `<sense>` and related `<cit>` (citation) tags.

### Phase 4: The Chronological Filter Agent (High Difficulty)
**Persona:** Algorithmic Date Parser
**Objective:** Implement the logic to filter out future definitions.
**Instructions:**
1.  Create a utility function `filter_by_date(lexicon_data, cutoff_year)`.
2.  **Date Extraction:** Academic APIs often return messy string dates in citations (e.g., "Cic. Ep. 43", "Plaut. Bacch. 3, 3", "c. 200 B.C.", "late 1st cent. A.D.").
3.  Write a robust regex and mapping dictionary within Python that attempts to map known authors (e.g., Plautus -> ~200 BCE, Cicero -> ~50 BCE) to integer years.
4.  If a `sense` branch only contains citations with dates/authors chronologically *greater* than the `cutoff_year`, drop that entire sense branch from the JSON payload.
5.  If a date cannot be definitively parsed, keep it (err on the side of providing data, but flag it as unverified in the UI).
6.  Finalize the API response to exactly match the JSON schema in `spec.md`, cache it via `database.py`, and return it to the frontend.

---

## 3. Final Verification Step
Before concluding execution, the Agent must review the complete generated codebase and assert:
- [ ] Are there any API keys required? (There should be none; use open endpoints).
- [ ] Does the frontend rely on any external JS libraries? (It must not).
- [ ] Is the data structure strictly objective? (No LLM summarization of the meaning, only API data passed through).
- [ ] Is the app ready to run locally via `pip install -r requirements.txt && uvicorn main:app --reload`?