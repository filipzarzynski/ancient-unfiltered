const filterButtons = document.querySelectorAll(".filter-button");
const examples = document.querySelectorAll(".example");
const corpusSelect = document.querySelector("#corpusSelect");
const pairFocus = document.querySelector("#pairFocus");
const corpusList = document.querySelector("#corpusList");
let corpusEntries = [];

function setActiveFilter(nextFilter) {
  filterButtons.forEach((button) => {
    const isActive = button.dataset.filter === nextFilter;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
  });

  examples.forEach((example) => {
    const shouldShow = nextFilter === "all" || example.dataset.theme === nextFilter;
    example.hidden = !shouldShow;
  });
}

filterButtons.forEach((button) => {
  button.setAttribute("aria-pressed", button.classList.contains("active") ? "true" : "false");
  button.addEventListener("click", () => setActiveFilter(button.dataset.filter));
});

function renderPathOptions(entry) {
  return entry.path_options.map((path, pathIndex) => {
    const options = path.options.map((option, optionIndex) => `
      <label class="path-choice">
        <input
          type="radio"
          name="${entry.id}-${pathIndex}"
          value="${option}"
          ${optionIndex === 0 ? "checked" : ""}
        >
        <span>${option}</span>
      </label>
    `).join("");

    return `
      <fieldset class="path-field">
        <legend><span lang="grc">${path.token}</span> <small>${path.lemma}</small></legend>
        ${options}
      </fieldset>
    `;
  }).join("");
}

function selectedPathSummary(container) {
  return [...container.querySelectorAll(".path-field")].map((field) => {
    const token = field.querySelector("legend span").textContent;
    const checked = field.querySelector("input:checked");
    return `${token}: ${checked ? checked.value : ""}`;
  }).join(" | ");
}

function renderFocusedPair(entry) {
  pairFocus.innerHTML = `
    <div class="pair-meta">
      <span>${entry.theme}</span>
      <span>${entry.author}</span>
      <span>${entry.work} ${entry.citation}</span>
    </div>
    <div class="pair-columns">
      <section>
        <h3>Current English reception</h3>
        <p class="current-english">${entry.current_english}</p>
      </section>
      <section>
        <h3>Cited original-language wording</h3>
        <blockquote lang="${entry.critical_original.language}">${entry.critical_original.text}</blockquote>
        <p class="source-note">
          ${entry.critical_original.source_label}.
          <a href="${entry.critical_original.source_url}">Source</a>
        </p>
      </section>
    </div>
    <section>
      <h3>Available meaning paths</h3>
      <div class="path-grid">${renderPathOptions(entry)}</div>
    </section>
    <section class="translation-preview">
      <h3>Example selected output</h3>
      <p class="path-summary"></p>
      <p class="selected-output">${entry.example_selected_output}</p>
    </section>
    <section>
      <h3>Other grammar-respecting renderings</h3>
      <ol class="renderings">
        ${entry.alternative_translations.map((translation) => `<li>${translation}</li>`).join("")}
      </ol>
    </section>
  `;

  const updateSummary = () => {
    pairFocus.querySelector(".path-summary").textContent = selectedPathSummary(pairFocus);
  };

  pairFocus.querySelectorAll("input[type='radio']").forEach((input) => {
    input.addEventListener("change", updateSummary);
  });
  updateSummary();
}

function renderCorpusList(entries) {
  corpusList.innerHTML = entries.map((entry) => `
    <button class="corpus-card" type="button" data-entry="${entry.id}">
      <span>${entry.theme}</span>
      <strong>${entry.current_english}</strong>
      <small>${entry.author}, ${entry.work} ${entry.citation}</small>
    </button>
  `).join("");

  corpusList.querySelectorAll(".corpus-card").forEach((card) => {
    card.addEventListener("click", () => {
      corpusSelect.value = card.dataset.entry;
      renderFocusedPair(corpusEntries.find((entry) => entry.id === card.dataset.entry));
      pairFocus.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
}

async function loadCorpus() {
  if (!corpusSelect || !pairFocus || !corpusList) return;

  try {
    const response = await fetch("corpus/v0.3-seed.json");
    if (!response.ok) throw new Error(`Corpus request failed: ${response.status}`);
    const corpus = await response.json();
    corpusEntries = corpus.entries;

    corpusSelect.innerHTML = corpusEntries.map((entry) => `
      <option value="${entry.id}">${entry.theme} - ${entry.author}, ${entry.work} ${entry.citation}</option>
    `).join("");

    corpusSelect.addEventListener("change", () => {
      renderFocusedPair(corpusEntries.find((entry) => entry.id === corpusSelect.value));
    });

    renderFocusedPair(corpusEntries[0]);
    renderCorpusList(corpusEntries);
  } catch (error) {
    pairFocus.innerHTML = `<p>Corpus could not be loaded: ${error.message}</p>`;
  }
}

loadCorpus();
