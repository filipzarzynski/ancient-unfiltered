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

function tokenize(text) {
  return text.match(/\p{L}+|[^\p{L}]+/gu) || [];
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

async function queryWord(target) {
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
    year: cutoffYear.value || "-399",
    language: languageMode.value || "auto",
    context: sentenceAround(target),
    token_index: target.dataset.tokenIndex || "0",
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

processText();
