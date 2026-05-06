/*
Local Diachronic Philology Engine
Copyright (C) 2026 Filip Zarzynski

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.
*/

const form = document.querySelector("#process-form");
const sourceText = document.querySelector("#source-text");
const cutoffYear = document.querySelector("#cutoff-year");
const languageMode = document.querySelector("#language-mode");
const processedText = document.querySelector("#processed-text");
const treeRoot = document.querySelector("#tree-root");
const queryState = document.querySelector("#query-state");
const deskTab = document.querySelector("#desk-tab");
const corpusTab = document.querySelector("#corpus-tab");
const readingDesk = document.querySelector("#reading-desk");
const corpusExplorer = document.querySelector("#corpus-explorer");
const corpusSelect = document.querySelector("#corpus-select");
const loadCorpusEntry = document.querySelector("#load-corpus-entry");
const corpusFocus = document.querySelector("#corpus-focus");
const corpusList = document.querySelector("#corpus-list");
const corpusState = document.querySelector("#corpus-state");
const corpusJson = document.querySelector("#corpus-json");
const localEntryForm = document.querySelector("#local-entry-form");
const exportLocalCorpus = document.querySelector("#export-local-corpus");
const importLocalCorpus = document.querySelector("#import-local-corpus");

const LOCAL_ENTRIES_KEY = "ancient-unfiltered-v03-local-entries";
const PATH_SELECTIONS_KEY = "ancient-unfiltered-v03-path-selections";

let seedCorpusEntries = [];
let localCorpusEntries = readJsonStorage(LOCAL_ENTRIES_KEY, []);
let corpusEntries = [];
let pathSelections = readJsonStorage(PATH_SELECTIONS_KEY, {});
let activeCorpusEntry = null;

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[char]);
}

function readJsonStorage(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function writeJsonStorage(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

function tokenize(text) {
  return text.match(/\p{L}+|[^\p{L}]+/gu) || [];
}

function setMode(mode, updateHash = true) {
  const corpusMode = mode === "corpus";
  deskTab.classList.toggle("is-active", !corpusMode);
  corpusTab.classList.toggle("is-active", corpusMode);
  deskTab.setAttribute("aria-selected", String(!corpusMode));
  corpusTab.setAttribute("aria-selected", String(corpusMode));
  readingDesk.hidden = corpusMode;
  corpusExplorer.hidden = !corpusMode;
  if (updateHash) history.replaceState(null, "", corpusMode ? "#corpus" : "#desk");
  if (corpusMode && !corpusEntries.length) loadCorpus();
}

function processText() {
  processedText.replaceChildren();
  for (const token of tokenize(sourceText.value)) {
    if (/^\p{L}+$/u.test(token)) {
      const word = document.createElement("span");
      word.className = "interactive-word";
      word.tabIndex = 0;
      word.dataset.tokenIndex = String(processedText.querySelectorAll(".interactive-word").length);
      word.textContent = token;
      processedText.append(word);
    } else {
      processedText.append(document.createTextNode(token));
    }
  }
  treeRoot.innerHTML = '<p class="empty-state">Select a word.</p>';
  queryState.textContent = "Ready";
}

function normalizeToken(token) {
  return token.normalize("NFC").replace(/^[^\p{L}]+|[^\p{L}]+$/gu, "").toLocaleLowerCase();
}

async function queryWord(target, overrides = {}) {
  const word = normalizeToken(target.textContent);
  if (!word) return;

  document.querySelectorAll(".interactive-word.is-selected").forEach((node) => {
    node.classList.remove("is-selected");
  });
  target.classList.add("is-selected");

  queryState.textContent = "Loading";
  treeRoot.innerHTML = '<p class="empty-state">Fetching external data...</p>';

  const params = new URLSearchParams({
    word,
    year: String(overrides.year ?? cutoffYear.value ?? "-399"),
    language: overrides.language ?? languageMode.value ?? "auto",
    context: overrides.context ?? sentenceAround(target),
    token_index: String(overrides.tokenIndex ?? target.dataset.tokenIndex ?? "0"),
  });

  try {
    const response = await fetch(`/api/query?${params.toString()}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    treeRoot.replaceChildren(buildDirectoryTree(data));
    queryState.textContent = "Loaded";
  } catch (error) {
    treeRoot.innerHTML = "";
    const message = document.createElement("p");
    message.className = "error-state";
    message.textContent = `Lookup failed: ${error.message}`;
    treeRoot.append(message);
    queryState.textContent = "Error";
  }
}

function buildDirectoryTree(data) {
  const root = document.createElement("div");
  const rootNode = makeDetails(`${data.display_word || data.word || "Selected word"} (${data.language || "unknown"})`, true);

  rootNode.append(
    makeLocalContextBranch(data.local_context || {}),
    makeBranch("Morphology", data.morphology || [], renderMorphologyPath),
    makeBranch(`Lexicon by cutoff (pre-${data.query_year})`, data.lexicon || [], renderLexiconSense),
    makeSourceSentenceBranch(data.lexicon || []),
    makeEtymologyBranch(data.etymology || {}),
    makeBranch("Translation context, not interpretation", data.translations || [], renderTranslation),
    makeBranch("Source warnings", (data.warnings || []).map((warning) => ({ warning })), renderWarning),
  );

  root.append(rootNode);
  return root;
}

function makeBranch(title, items, renderer) {
  const branch = makeDetails(title, true);
  if (!items.length) {
    branch.append(makeLeaf("No source data returned."));
    return branch;
  }
  items.forEach((item) => branch.append(renderer(item)));
  return branch;
}

function makeEtymologyBranch(etymology) {
  const branch = makeDetails("Etymology", false);
  const items = etymology.items || [];
  if (!items.length && !etymology.literal_meaning) {
    branch.append(makeLeaf("No source data returned."));
    return branch;
  }
  if (etymology.root) branch.append(makeLeaf(`Root: ${etymology.root}`));
  if (etymology.literal_meaning) branch.append(makeLeaf(`Text: ${etymology.literal_meaning}`));
  for (const item of items) {
    branch.append(makeLeaf(`${item.source || "source"}: ${item.text || ""} (${item.date_status || "date unverified"})`));
  }
  return branch;
}

function renderMorphologyPath(path) {
  const node = makeDetails(`${path.path}: ${path.lemma || "unlisted"} (${path.pos || "unlisted"})`, false);
  node.append(makeLeaf(path.details || "No additional morphology fields returned."));
  node.append(makeLeaf(`Source: ${path.source || "unlisted"}; confidence: ${path.confidence || "unlisted"}`));
  return node;
}

function renderLexiconSense(sense) {
  const node = makeDetails(`${sense.sense}: ${sense.definition || "No definition text returned."}`, false);
  node.append(makeLeaf(`Source: ${sense.source || "unlisted"}; date status: ${sense.date_status || "unverified"}`));
  const citationBranch = makeDetails("Citations", false);
  const list = document.createElement("ul");
  list.className = "tree-list";
  for (const citation of sense.citations || []) {
    const item = document.createElement("li");
    if (typeof citation === "string") {
      item.textContent = citation;
    } else {
      const year = citation.estimated_year === null || citation.estimated_year === undefined
        ? "date unverified"
        : `${Math.abs(citation.estimated_year)} ${citation.estimated_year < 0 ? "BCE" : "CE"} estimated`;
      item.textContent = `${citation.raw || "citation"} (${year})`;
    }
    list.append(item);
  }
  citationBranch.append(list);
  node.append(citationBranch);
  return node;
}

function makeLocalContextBranch(context) {
  const branch = makeDetails("Word", true);
  branch.append(makeLeaf(`Local sentence: ${context.sentence || "No local context sent."}`));
  branch.append(makeLeaf(`Token index: ${context.token_index ?? "unlisted"}`));
  return branch;
}

function makeSourceSentenceBranch(lexicon) {
  const branch = makeDetails("Source sentence estimates", false);
  let count = 0;
  for (const sense of lexicon) {
    for (const citation of sense.citations || []) {
      if (typeof citation === "string") continue;
      const estimate = citation.source_sentence || {};
      const label = citation.raw || "citation";
      const node = makeDetails(label, false);
      node.append(makeLeaf(`Provider: ${estimate.provider || "source sentence unavailable"}`));
      node.append(makeLeaf(`Match: ${estimate.match_strategy || "source sentence unavailable"}; confidence: ${estimate.confidence || "unavailable"}`));
      node.append(makeLeaf(estimate.text || "source sentence unavailable"));
      branch.append(node);
      count += 1;
    }
  }
  if (!count) branch.append(makeLeaf("No source sentence estimates returned."));
  return branch;
}

function renderTranslation(translation) {
  const node = makeDetails(translation.passage || "Translation context", false);
  node.append(makeLeaf(translation.text || "No translation text returned."));
  node.append(makeLeaf(`Source: ${translation.source || "unlisted"}; ${translation.date_status || "translation date unverified"}`));
  return node;
}

function renderWarning(item) {
  return makeLeaf(item.warning || "No warning text returned.");
}

function makeDetails(summaryText, open) {
  const details = document.createElement("details");
  details.open = open;
  const summary = document.createElement("summary");
  summary.textContent = summaryText;
  details.append(summary);
  return details;
}

function makeLeaf(text) {
  const leaf = document.createElement("p");
  leaf.className = "tree-leaf";
  leaf.textContent = text;
  return leaf;
}

function sentenceAround(target) {
  const fullText = sourceText.value;
  const token = target.textContent;
  const index = fullText.indexOf(token);
  if (index < 0) return "";

  const before = fullText.slice(0, index);
  const after = fullText.slice(index + token.length);
  const start = Math.max(before.lastIndexOf("."), before.lastIndexOf(";"), before.lastIndexOf("?"), before.lastIndexOf("!")) + 1;
  const endCandidates = [after.indexOf("."), after.indexOf(";"), after.indexOf("?"), after.indexOf("!")].filter((value) => value >= 0);
  const end = endCandidates.length ? index + token.length + Math.min(...endCandidates) + 1 : fullText.length;
  return fullText.slice(start, end).trim();
}

async function loadCorpus() {
  try {
    const response = await fetch("/api/corpus/seed");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const corpus = await response.json();
    seedCorpusEntries = corpus.entries || [];
    refreshCorpus();
    corpusState.textContent = `Loaded ${seedCorpusEntries.length} seed entries and ${localCorpusEntries.length} local entries.`;
  } catch (error) {
    corpusFocus.innerHTML = `<p class="error-state">Corpus failed to load: ${escapeHtml(error.message)}</p>`;
    corpusState.textContent = "Corpus load failed.";
  }
}

function refreshCorpus() {
  corpusEntries = [...seedCorpusEntries, ...localCorpusEntries];
  renderCorpusSelect();
  renderCorpusList();
  if (!activeCorpusEntry && corpusEntries.length) activeCorpusEntry = corpusEntries[0];
  if (activeCorpusEntry) renderCorpusFocus(activeCorpusEntry);
}

function renderCorpusSelect() {
  corpusSelect.innerHTML = corpusEntries.map((entry) => `
    <option value="${escapeHtml(entry.id)}">${escapeHtml(entry.theme)} - ${escapeHtml(entry.author)}, ${escapeHtml(entry.work)} ${escapeHtml(entry.citation)}</option>
  `).join("");
  if (activeCorpusEntry) corpusSelect.value = activeCorpusEntry.id;
}

function renderCorpusList() {
  corpusList.innerHTML = corpusEntries.map((entry) => `
    <button class="corpus-card" type="button" data-entry="${escapeHtml(entry.id)}">
      <span>${escapeHtml(entry.theme)}</span>
      <strong>${escapeHtml(entry.current_english)}</strong>
      <small>${escapeHtml(entry.author)}, ${escapeHtml(entry.work)} ${escapeHtml(entry.citation)}</small>
    </button>
  `).join("");
}

function selectCorpusEntry(entryId) {
  const entry = corpusEntries.find((candidate) => candidate.id === entryId);
  if (!entry) return;
  activeCorpusEntry = entry;
  corpusSelect.value = entry.id;
  renderCorpusFocus(entry);
}

function entryLanguage(entry) {
  return entry.critical_original?.language === "lat" ? "latin" : "greek";
}

function renderCorpusOriginal(entry) {
  return tokenize(entry.critical_original?.text || "").map((token, index) => {
    if (/^\p{L}+$/u.test(token)) {
      return `<button class="inline-token interactive-word" type="button" data-token-index="${index}">${escapeHtml(token)}</button>`;
    }
    return escapeHtml(token);
  }).join("");
}

function renderPathOptions(entry) {
  const selected = pathSelections[entry.id] || entry.selected_paths || {};
  return (entry.path_options || []).map((path, pathIndex) => {
    const token = path.token || `path-${pathIndex}`;
    const checkedValue = selected[token] || path.options?.[0] || "";
    const options = (path.options || []).map((option) => `
      <label class="path-choice">
        <input
          type="radio"
          name="${escapeHtml(entry.id)}-${pathIndex}"
          value="${escapeHtml(option)}"
          data-token="${escapeHtml(token)}"
          ${option === checkedValue ? "checked" : ""}
        >
        <span>${escapeHtml(option)}</span>
      </label>
    `).join("");

    return `
      <fieldset class="path-field">
        <legend><span lang="grc">${escapeHtml(token)}</span> <small>${escapeHtml(path.lemma || "lemma unlisted")}</small></legend>
        ${options}
      </fieldset>
    `;
  }).join("");
}

function renderCorpusFocus(entry) {
  const source = entry.critical_original || {};
  corpusFocus.innerHTML = `
    <div class="pair-meta">
      <span>${escapeHtml(entry.theme)}</span>
      <span>${escapeHtml(entry.author)}</span>
      <span>${escapeHtml(entry.work)} ${escapeHtml(entry.citation)}</span>
      <span>${Math.abs(entry.approximate_year || 0)} ${(entry.approximate_year || 0) < 0 ? "BCE" : "CE"} estimated</span>
    </div>
    <section>
      <h2>Current English reception</h2>
      <p class="current-english">${escapeHtml(entry.current_english)}</p>
    </section>
    <section>
      <h2>Cited original-language wording</h2>
      <blockquote class="corpus-original" lang="${escapeHtml(source.language || "grc")}">${renderCorpusOriginal(entry)}</blockquote>
      <p class="source-note">${escapeHtml(source.source_label || "source label missing")}. <a href="${escapeHtml(source.source_url || "#")}">Source</a></p>
    </section>
    <section>
      <h2>Token-level branch choices</h2>
      <div class="path-grid">${renderPathOptions(entry)}</div>
    </section>
    <section class="translation-preview">
      <h2>Selected-path translation preview</h2>
      <p class="path-summary"></p>
      <p class="selected-output"></p>
    </section>
    <section>
      <h2>Equal-weight alternative renderings</h2>
      <ol class="renderings">
        ${(entry.alternative_translations || []).map((translation) => `<li>${escapeHtml(translation)}</li>`).join("")}
      </ol>
    </section>
  `;
  bindCorpusFocus(entry);
}

function bindCorpusFocus(entry) {
  const selectedOutput = corpusFocus.querySelector(".selected-output");
  const updateSummary = () => {
    const selected = {};
    corpusFocus.querySelectorAll(".path-field input:checked").forEach((input) => {
      selected[input.dataset.token] = input.value;
    });
    pathSelections[entry.id] = selected;
    writeJsonStorage(PATH_SELECTIONS_KEY, pathSelections);
    const summary = Object.entries(selected).map(([token, option]) => `${token}: ${option}`).join(" | ");
    corpusFocus.querySelector(".path-summary").textContent = summary || "No path selected.";
    selectedOutput.textContent = buildSelectedOutput(entry, selected);
  };

  corpusFocus.querySelectorAll(".path-field input").forEach((input) => {
    input.addEventListener("change", updateSummary);
  });
  updateSummary();
}

function buildSelectedOutput(entry, selected) {
  const template = entry.example_selected_output || entry.alternative_translations?.[0] || "";
  if (!template) return "No selected-path preview available.";
  return (entry.path_options || []).reduce((output, path) => {
    const selectedOption = selected[path.token];
    return selectedOption ? replaceKnownOption(output, path.options || [], selectedOption) : output;
  }, template);
}

function replaceKnownOption(text, options, selectedOption) {
  const alternatives = [...options]
    .filter((option) => option && option !== selectedOption)
    .sort((left, right) => right.length - left.length);
  for (const option of alternatives) {
    const next = replacePhrase(text, option, selectedOption);
    if (next !== text) return next;
  }
  return text;
}

function replacePhrase(text, phrase, replacement) {
  const escaped = phrase.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const pattern = new RegExp(`(^|[^A-Za-z])(${escaped})(?=$|[^A-Za-z])`, "gi");
  return text.replace(pattern, (_, prefix) => `${prefix}${replacement}`);
}

function parsePathOptions(raw) {
  return raw.split("\n").map((line) => line.trim()).filter(Boolean).map((line) => {
    const [token, lemma, optionsText] = line.split("|").map((part) => part.trim());
    return {
      token,
      lemma,
      options: (optionsText || "").split(";").map((option) => option.trim()).filter(Boolean),
    };
  });
}

function localEntryFromForm(formElement) {
  const data = new FormData(formElement);
  const alternatives = String(data.get("alternative_translations") || "").split("\n").map((line) => line.trim()).filter(Boolean);
  const pathOptions = parsePathOptions(String(data.get("path_options") || ""));
  return {
    id: String(data.get("id") || "").trim(),
    theme: String(data.get("theme") || "").trim(),
    author: String(data.get("author") || "").trim(),
    work: String(data.get("work") || "").trim(),
    citation: String(data.get("citation") || "").trim(),
    approximate_year: Number(data.get("approximate_year") || 0),
    current_english: String(data.get("current_english") || "").trim(),
    critical_original: {
      language: "grc",
      text: String(data.get("original_text") || "").trim(),
      source_label: String(data.get("source_label") || "").trim(),
      source_url: String(data.get("source_url") || "").trim(),
      confidence: "user-proposed",
    },
    path_options: pathOptions,
    alternative_translations: alternatives,
    example_selected_output: alternatives[0] || "Alternative rendering not supplied.",
    selected_paths: Object.fromEntries(pathOptions.map((path) => [path.token, path.options[0] || ""])),
  };
}

async function validateEntry(entry) {
  const response = await fetch("/api/corpus/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(entry),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(Array.isArray(data.detail) ? data.detail.join("; ") : `HTTP ${response.status}`);
  }
  return data.entry;
}

function mergeLocalEntries(entries) {
  const byId = new Map(localCorpusEntries.map((entry) => [entry.id, entry]));
  entries.forEach((entry) => byId.set(entry.id, entry));
  localCorpusEntries = [...byId.values()];
  writeJsonStorage(LOCAL_ENTRIES_KEY, localCorpusEntries);
  refreshCorpus();
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  processText();
});

processedText.addEventListener("click", (event) => {
  if (event.target.classList.contains("interactive-word")) {
    queryWord(event.target);
  }
});

processedText.addEventListener("keydown", (event) => {
  if ((event.key === "Enter" || event.key === " ") && event.target.classList.contains("interactive-word")) {
    event.preventDefault();
    queryWord(event.target);
  }
});

deskTab.addEventListener("click", () => setMode("desk"));
corpusTab.addEventListener("click", () => setMode("corpus"));
window.addEventListener("hashchange", () => {
  setMode(location.hash === "#corpus" ? "corpus" : "desk", false);
});

corpusSelect.addEventListener("change", () => selectCorpusEntry(corpusSelect.value));
loadCorpusEntry.addEventListener("click", () => selectCorpusEntry(corpusSelect.value));

corpusList.addEventListener("click", (event) => {
  const card = event.target.closest(".corpus-card");
  if (!card) return;
  selectCorpusEntry(card.dataset.entry);
  corpusFocus.scrollIntoView({ behavior: "smooth", block: "start" });
});

corpusFocus.addEventListener("click", (event) => {
  if (!event.target.classList.contains("inline-token") || !activeCorpusEntry) return;
  queryWord(event.target, {
    year: activeCorpusEntry.approximate_year || cutoffYear.value || "-399",
    language: entryLanguage(activeCorpusEntry),
    context: activeCorpusEntry.critical_original?.text || "",
    tokenIndex: event.target.dataset.tokenIndex || "0",
  });
});

localEntryForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const entry = await validateEntry(localEntryFromForm(localEntryForm));
    mergeLocalEntries([entry]);
    activeCorpusEntry = entry;
    corpusState.textContent = `Added local entry ${entry.id}. Export it before clearing browser storage.`;
    localEntryForm.reset();
  } catch (error) {
    corpusState.textContent = `Local entry rejected: ${error.message}`;
  }
});

exportLocalCorpus.addEventListener("click", async () => {
  try {
    const entries = localCorpusEntries.map((entry) => ({
      ...entry,
      selected_paths: pathSelections[entry.id] || entry.selected_paths || {},
    }));
    const response = await fetch("/api/corpus/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source: "browser-local", entries }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(Array.isArray(data.detail) ? data.detail.join("; ") : `HTTP ${response.status}`);
    }
    corpusJson.value = JSON.stringify(data, null, 2);
    corpusState.textContent = `Exported ${entries.length} local entries as a v0.3 evidence proposal.`;
  } catch (error) {
    corpusState.textContent = `Export failed: ${error.message}`;
  }
});

importLocalCorpus.addEventListener("click", async () => {
  try {
    const patch = JSON.parse(corpusJson.value);
    const response = await fetch("/api/corpus/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patch),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(Array.isArray(data.detail) ? data.detail.join("; ") : `HTTP ${response.status}`);
    }
    mergeLocalEntries(data.entries || []);
    corpusState.textContent = `Imported ${data.entries.length} validated evidence proposals.`;
  } catch (error) {
    corpusState.textContent = `Import failed: ${error.message}`;
  }
});

processText();
setMode(location.hash === "#corpus" ? "corpus" : "desk", false);
