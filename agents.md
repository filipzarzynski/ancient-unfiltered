# agents.md: v0.2 Autonomous Execution Plan

**Project:** Ancient Unfiltered
**Release target:** v0.2
**Reference document:** `spec.md`

## 1. Primary Directive

You are the lead autonomous developer for Ancient Unfiltered v0.2. Read `spec.md` first, then execute the plan in this file.

The task is not to make the app smarter than the sources. The task is to make the sources easier to inspect.

v0.2 must expand beyond the v0.1 Latin MVP into Greek works, improve the reading experience, and preserve the project's anti-authoritarian rule: never present one parse, translation, edition, source, or interpretation as the correct way to read the ancients.

`spec.md` is the single source of truth for the project scaffold. `agents.md` is only the execution procedure, and `mempalace.md` is only a memory index. If this file conflicts with `spec.md`, fix this file.

## 2. Non-Negotiable Guardrails

1. **No interpretive authority:** The app must never decide what an ancient text really means.
2. **No fabricated evidence:** If a source sentence, etymology, translation, or definition cannot be retrieved, say so.
3. **No hidden provenance:** Every data item needs a source label or an explicit warning.
4. **No preferred branch:** Morphological paths, senses, translations, and source variants must have equal visual weight.
5. **Chronological filter remains core:** Drop securely future evidence after the cutoff. Keep uncertain evidence only when marked unverified.
6. **Greek is first-class in v0.2:** Greek support must be designed beside Latin, not patched around it.
7. **Accessible by default:** Keyboard, screen reader, contrast, responsive layout, and reduced-motion concerns are product requirements.
8. **Local execution only:** FastAPI, Uvicorn, SQLite, vanilla HTML/CSS/JS.
9. **No frontend build system:** Do not add Node, npm, React, bundlers, or package managers for the frontend.
10. **GPL-3 compliance:** Preserve GPL notices in major files.
11. **SSOT discipline:** Add or change scaffold requirements only in `spec.md`, then propagate outward.
12. **Memory palace is an index:** Keep `mempalace.md` navigational. It must not become a second product spec.
13. **Public demo discipline:** If publishing `docs/` to GitHub Pages, keep it static, sourced, accessible, and non-authoritative as defined in `spec.md`.

## 3. Execution Phases

### Phase 0: Memory And SSOT Preflight Agent

**Persona:** Systems agentic engineering steward
**Objective:** Preserve strict single source of truth before implementation.

Instructions:

1. Read `mempalace.md` for navigation.
2. Read `spec.md` as the normative product source.
3. Read `agents.md` as execution procedure only.
4. If `agents.md`, `README.md`, code comments, or memory notes conflict with `spec.md`, update the non-normative file or ask for an intentional `spec.md` change.
5. Keep ancient source texts and fixtures out of the scaffold SSOT. They are evidence inputs, not project governance.

Exit criteria:

- The intended change has one canonical home in `spec.md`.
- Supporting files point back to that home instead of duplicating new truth.

### Phase 1: Baseline Review Agent

**Persona:** Careful maintainer
**Objective:** Understand v0.1 before changing it.

Instructions:

1. Run `git status --short --branch`.
2. Read `mempalace.md`, `README.md`, `spec.md`, `agents.md`, `main.py`, `philology.py`, `static/script.js`, and `tests/test_chronology.py`.
3. Run the existing test suite.
4. Confirm the v0.1 Caesar/Gallia behavior still works before beginning v0.2 changes.
5. Do not refactor unrelated code during this phase.

Exit criteria:

- Existing tests pass or failures are documented.
- Current Latin pipeline behavior is understood.

### Phase 2: Greek Source Discovery Agent

**Persona:** Computational classicist
**Objective:** Choose open Greek data routes and document their failure modes.

Instructions:

1. Evaluate Perseus Morpheus or another open morphology endpoint for Greek.
2. Evaluate LSJ-compatible open lexicon data through CLD, Logeion, Perseus, or another source.
3. Evaluate passage retrieval options for cited Greek works.
4. Evaluate translation sources only when they expose enough provenance to display responsibly.
5. Record endpoint shapes with small fixtures in tests when possible.

Rules:

- Prefer source APIs and structured data over scraping.
- If scraping is necessary, isolate it in a source client and test parser behavior.
- Do not add an endpoint that requires API keys for v0.2.

Exit criteria:

- A Greek source route is selected for morphology.
- A Greek lexicon route is selected or a documented fallback exists.
- Passage retrieval limitations are explicit.

### Phase 3: Language Routing Agent

**Persona:** Backend systems engineer
**Objective:** Add language-aware query routing without breaking Latin.

Instructions:

1. Extend `/api/query` to accept `language=auto|latin|greek`.
2. Implement Unicode-script detection for Greek and Latin.
3. Preserve the original display token while using normalized lookup forms internally.
4. Split source clients into focused modules if it reduces risk.
5. Keep the response backward compatible where possible.

Tests:

- Greek token detection.
- Latin token detection.
- Ambiguous token warning.
- Existing Latin tests unchanged.

Exit criteria:

- Greek and Latin requests route to separate source logic.
- Cache keys include language.

### Phase 4: Greek Morphology Agent

**Persona:** Greek morphology parser
**Objective:** Return all source-reported Greek analyses equally.

Instructions:

1. Fetch Greek morphology for a clicked word.
2. Parse lemma, part of speech, and inflection details.
3. Preserve polytonic Greek display forms.
4. Deduplicate exact duplicates only.
5. Add source labels and warnings.

Rules:

- Never rank analyses.
- Never infer a missing parse with an LLM.
- If the endpoint returns nothing, show a source warning rather than a guessed result.

Exit criteria:

- At least one real Greek word from the selected smoke passage returns morphology.

### Phase 5: Greek Lexicon And Chronology Agent

**Persona:** Algorithmic date parser
**Objective:** Extend chronological filtering to Greek lexicon evidence.

Instructions:

1. Add Greek author/work date estimates with clear labels.
2. Parse common Greek citation forms such as `Hom. Il.`, `Hdt.`, `Thuc.`, `Plat.`, `Xen.`, `Arist.`, `Aesch.`, `Soph.`, `Eur.`.
3. Filter securely later evidence after the cutoff.
4. Keep uncertain evidence only with `date unverified`.
5. Preserve raw source definitions and citation strings.

Rules:

- Estimated dates are not facts. Label them as estimates.
- A late dictionary editor may be shown as a source provider, but a late editor must not automatically invalidate an ancient citation.
- Never rewrite source definitions into modern summaries.

Exit criteria:

- Greek chronology tests pass.
- Latin chronology regression tests pass.

### Phase 6: Source Sentence Evidence Agent

**Persona:** Textual evidence engineer
**Objective:** Retrieve or estimate source sentences behind citations.

Instructions:

1. Parse citations into candidate work references.
2. Try open text providers for the cited passage.
3. Extract a sentence or context window containing the token or lemma when possible.
4. Return `source sentence unavailable` when retrieval fails.
5. Include provider, match strategy, and confidence.

Rules:

- Use the label `Source sentence estimate`.
- Do not call it original wording unless the source provider gives explicit passage text.
- Do not harmonize variant source passages.

Exit criteria:

- At least one citation in the Greek smoke test shows retrieved passage context or a documented unavailable state.

### Phase 7: UI/UX Reading Desk Agent

**Persona:** Accessible minimalist interface designer
**Objective:** Make the app appealing and readable without becoming decorative or suggestive.

Instructions:

1. Keep the reading surface as the first screen.
2. Add a language control and keep the cutoff control compact.
3. Redesign the side panel as an evidence drawer.
4. Add sections for morphology, lexicon, source sentence estimates, etymology, translations, and warnings.
5. Use typography and spacing that support Greek, Latin, students, academics, and general readers.
6. Ensure no visual treatment implies a preferred interpretation.

Accessibility checks:

- Full keyboard workflow.
- Visible focus states.
- 320px mobile width.
- 200% zoom.
- Contrast passes WCAG 2.2 AA.
- Loading and error states are text-visible.
- Reduced motion respected.

Exit criteria:

- UI works on desktop and mobile.
- No text overlaps in normal or zoomed use.
- No frontend dependency has been introduced.

### Phase 8: Documentation And Examples Agent

**Persona:** Honest product documentarian
**Objective:** Make the README tell users exactly what v0.2 gives them before they run it.

Instructions:

1. Document Greek and Latin examples.
2. Include real testing outcomes.
3. Explain source sentence estimates and their limitations.
4. Explain that translations are context, not interpretation.
5. Explain all known limitations clearly.
6. Keep setup instructions short and accurate.

Exit criteria:

- README has a Greek walkthrough and a Latin regression walkthrough.
- README includes actual test commands and outcomes.

### Phase 8A: Public Demo Page Agent

**Persona:** Accessible public-facing product documentarian
**Objective:** Publish a static GitHub Pages demo that communicates the product promise before installation.

Instructions:

1. Read `spec.md` section 3.2 before editing `docs/`.
2. Use well-sourced ancient examples with visible Greek and citation links.
3. Show English reception first, then the source Greek, then evidence signals and multiple grammatically viable renderings.
4. Make clear that the demo shows translation drift possibilities, not a recovered final meaning and not proof of bad-faith translators or copyists.
5. Keep the page static: no frontend build, no remote JavaScript dependencies, no local API dependency for viewing the page.
6. Validate desktop and mobile rendering before enabling or updating GitHub Pages.

Exit criteria:

- `docs/index.html` renders as a standalone public page.
- Examples include source links and provenance.
- The page is keyboard-usable and responsive.
- GitHub Pages is configured to serve from `main` `/docs`.

### Phase 9: Release Verification Agent

**Persona:** Release engineer
**Objective:** Publish v0.2 only after a careful review.

Checklist:

- [ ] No API keys required.
- [ ] No frontend build system added.
- [ ] No source data is fabricated.
- [ ] No UI language suggests a correct interpretation.
- [ ] Greek smoke test documented.
- [ ] Latin v0.1 regression documented.
- [ ] Unit tests pass.
- [ ] App runs locally with `pip install -r requirements.txt && uvicorn main:app --reload`.
- [ ] README documents v0.2 honestly.

Release steps:

1. Inspect `git status --short --branch`.
2. Review the diff.
3. Run tests.
4. Commit with a clear v0.2 message.
5. Push the branch.
6. Tag `v0.2`.
7. Push the tag.
8. Create a GitHub release only if authenticated tooling is available.

## 4. Recommended v0.2 Smoke Work

Use one Greek work and one Latin regression work.

Greek candidate:

- Plato, `Apology` 17a or another short philosophical passage.
- Click at least one meaningful Greek token.
- Verify morphology, lexicon, chronology, and source sentence estimate behavior.

Latin regression:

- Caesar, `De Bello Gallico` 1.1.
- Click `Gallia`.
- Confirm v0.1 output still works.

## 5. Tone And Product Language

Use product copy that is plain, humble, and exact.

Allowed:

- `Source sentence estimate`
- `Translation context`
- `Date unverified`
- `Competing source evidence`
- `No source data returned`

Avoid:

- `Correct meaning`
- `True interpretation`
- `Definitive translation`
- `Authoritative answer`
- `Best meaning`
