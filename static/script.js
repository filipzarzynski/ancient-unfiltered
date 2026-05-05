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

  const params = new URLSearchParams({ word, year: cutoffYear.value || "-50" });
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
  const rootNode = makeDetails(data.word || "Selected word", true);

  rootNode.append(
    makeBranch("1. Morphological Paths", data.morphology || [], renderMorphologyPath),
    makeEtymologyBranch(data.etymology || {}),
    makeBranch(`3. Chronological Lexicon (pre-${data.query_year})`, data.lexicon || [], renderLexiconSense),
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
  const branch = makeDetails("2. Etymological Topology", true);
  branch.append(makeLeaf(`Root: ${etymology.root || "No source data returned."}`));
  branch.append(makeLeaf(`Literal: ${etymology.literal_meaning || "No source data returned."}`));
  return branch;
}

function renderMorphologyPath(path) {
  const node = makeDetails(`${path.path}: ${path.lemma || "unlisted"} (${path.pos || "unlisted"})`, false);
  node.append(makeLeaf(path.details || "No additional morphology fields returned."));
  return node;
}

function renderLexiconSense(sense) {
  const node = makeDetails(`${sense.sense}: ${sense.definition || "No definition text returned."}`, false);
  const citationBranch = makeDetails("Citations", false);
  const list = document.createElement("ul");
  list.className = "tree-list";
  for (const citation of sense.citations || []) {
    const item = document.createElement("li");
    item.textContent = citation;
    list.append(item);
  }
  citationBranch.append(list);
  node.append(citationBranch);
  return node;
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
