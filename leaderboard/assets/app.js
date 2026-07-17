const state = {
  papers: [],
  filtered: [],
  visible: [],
  tags: [],
  aliasMap: {},
  tagByNorm: {},
  include: [],
  exclude: [],
  invalid: [],
  sort: "total_score",
  dateFrom: "",
  dateTo: "",
  stats: null,
  suggestions: [],
  suggestionEntries: [],
  activeSuggestion: -1,
  virtual: {
    rowHeight: 96,
    overscan: 8,
    scrollTop: 0,
  },
  renderQueued: false,
};

const ui = {
  meta: document.querySelector("#site-meta"),
  form: document.querySelector("#query-form"),
  queryInput: document.querySelector("#query-input"),
  sortSelect: document.querySelector("#sort-select"),
  dateFrom: document.querySelector("#date-from"),
  dateTo: document.querySelector("#date-to"),
  dateTriggers: document.querySelectorAll(".date-trigger"),
  datePicker: document.querySelector("#date-picker"),
  dateTitle: document.querySelector("#date-title"),
  datePrev: document.querySelector("#date-prev"),
  dateNext: document.querySelector("#date-next"),
  dateWeekdays: document.querySelector("#date-weekdays"),
  dateGrid: document.querySelector("#date-grid"),
  dateClear: document.querySelector("#date-clear"),
  includeChips: document.querySelector("#include-chips"),
  excludeChips: document.querySelector("#exclude-chips"),
  queryErrors: document.querySelector("#query-errors"),
  tagCloud: document.querySelector("#tag-cloud"),
  tagCount: document.querySelector("#tag-count"),
  resultsSummary: document.querySelector("#results-summary"),
  resultsViewport: document.querySelector(".table-wrap"),
  resultsBody: document.querySelector("#results-body"),
  clearButton: document.querySelector("#clear-button"),
  shareButton: document.querySelector("#share-button"),
  suggestionList: document.querySelector("#suggestion-list"),
};

function normalizeKey(value) {
  return (value || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

function composeQuery(include, exclude) {
  const includeTerms = include.map(quoteIfNeeded);
  const excludeTerms = exclude.map((term) => `- ${quoteIfNeeded(term)}`);
  return [...includeTerms, ...excludeTerms].join(" + ").replace(/\+\s-\s/g, "- ");
}

function quoteIfNeeded(value) {
  return /\s/.test(value) ? `"${value}"` : value;
}

function tokenizeQuery(input) {
  const tokens = [];
  const regex = /"([^"]+)"|([+-])|([^\s]+)/g;
  let match;
  while ((match = regex.exec(input)) !== null) {
    if (match[1]) {
      tokens.push(match[1]);
    } else if (match[2]) {
      tokens.push(match[2]);
    } else if (match[3]) {
      tokens.push(match[3]);
    }
  }
  return tokens;
}

function resolveTag(term) {
  const normalized = normalizeKey(term);
  return state.aliasMap[normalized] || state.tagByNorm[normalized] || null;
}

function parseQuery(input) {
  const tokens = tokenizeQuery(input);
  const include = [];
  const exclude = [];
  const invalid = [];
  let mode = "include";
  let phrase = [];

  function flushPhrase() {
    if (!phrase.length) return;
    const term = phrase.join(" ");
    const canonical = resolveTag(term);
    if (!canonical) {
      invalid.push(term);
      phrase = [];
      mode = "include";
      return;
    }
    const bucket = mode === "exclude" ? exclude : include;
    if (!bucket.includes(canonical)) {
      bucket.push(canonical);
    }
    phrase = [];
    mode = "include";
  }

  for (const token of tokens) {
    if (token === "+") {
      flushPhrase();
      mode = "include";
      continue;
    }
    if (token === "-") {
      flushPhrase();
      mode = "exclude";
      continue;
    }
    phrase.push(token);
  }

  flushPhrase();

  return { include, exclude, invalid };
}

function splitQueryForSuggestion(input) {
  const match = /^(.*?)(?:([+-])\s*)?([^+-]*)$/.exec(input);
  if (!match) {
    return { prefix: "", mode: "include", fragment: input.trimStart() };
  }
  return {
    prefix: match[1] || "",
    mode: match[2] === "-" ? "exclude" : "include",
    fragment: (match[3] || "").trimStart(),
  };
}

function buildSuggestionEntries() {
  const entries = [];
  const seen = new Set();
  const validCanonicals = new Set(state.tags.map((tag) => tag.label));

  for (const tag of state.tags) {
    const normalized = normalizeKey(tag.label);
    if (normalized && !seen.has(`${normalized}=>${tag.label}`)) {
      entries.push({ raw: tag.label, canonical: tag.label, display: tag.label });
      seen.add(`${normalized}=>${tag.label}`);
    }
  }

  for (const [alias, canonical] of Object.entries(state.aliasMap)) {
    if (!alias || !canonical) continue;
    if (!validCanonicals.has(canonical)) continue;
    const key = `${alias}=>${canonical}`;
    if (seen.has(key)) continue;
    entries.push({
      raw: alias,
      canonical,
      display: canonical,
    });
    seen.add(key);
  }

  state.suggestionEntries = entries;
}

function rankSuggestions(fragment) {
  const norm = normalizeKey(fragment);
  if (!norm) return [];
  const starts = [];
  const tokenStarts = [];
  const used = new Set();
  for (const entry of state.suggestionEntries) {
    const rawNorm = normalizeKey(entry.raw);
    if (rawNorm === norm) continue;
    if (rawNorm.startsWith(norm)) {
      if (!used.has(entry.canonical)) {
        starts.push(entry);
        used.add(entry.canonical);
      }
      continue;
    }

    const tokens = rawNorm.split(/\s+/).filter(Boolean);
    if (tokens.some((token) => token.startsWith(norm))) {
      if (!used.has(entry.canonical)) {
        tokenStarts.push(entry);
        used.add(entry.canonical);
      }
    }
  }
  return [...starts, ...tokenStarts].slice(0, 8);
}

function renderSuggestions() {
  ui.suggestionList.innerHTML = "";
  if (!state.suggestions.length) {
    ui.suggestionList.parentElement.classList.remove("open");
    ui.suggestionList.hidden = true;
    return;
  }
  ui.suggestionList.parentElement.classList.add("open");
  state.suggestions.forEach((entry, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `suggestion-item${index === state.activeSuggestion ? " active" : ""}`;
    button.textContent = entry.display;
    button.addEventListener("mousedown", (event) => {
      event.preventDefault();
      applySuggestion(entry.canonical);
    });
    ui.suggestionList.appendChild(button);
  });
  ui.suggestionList.hidden = false;
}

function hideSuggestions() {
  state.suggestions = [];
  state.activeSuggestion = -1;
  renderSuggestions();
}

function updateSuggestions() {
  const { fragment } = splitQueryForSuggestion(ui.queryInput.value);
  state.suggestions = rankSuggestions(fragment);
  state.activeSuggestion = state.suggestions.length ? 0 : -1;
  renderSuggestions();
}

function applySuggestion(tag) {
  const { prefix, mode } = splitQueryForSuggestion(ui.queryInput.value);
  ui.queryInput.value = `${prefix}${mode === "exclude" ? "- " : ""}${quoteIfNeeded(tag)}`.trim();
  hideSuggestions();
}

function formatNumber(value) {
  return new Intl.NumberFormat("en-US").format(value || 0);
}

function formatScore(value) {
  return Number(value || 0).toFixed(3);
}

function isValidDateInput(value) {
  return !value || /^\d{4}-\d{2}-\d{2}$/.test(value);
}

const datePickerState = {
  target: null,
  anchor: null,
  year: 0,
  month: 0,
};

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function formatDateParts(year, month, day) {
  return `${String(year).padStart(4, "0")}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

function parseDateValue(value) {
  if (!isValidDateInput(value) || !value) return null;
  const [year, month, day] = value.split("-").map(Number);
  return { year, month: month - 1, day };
}

function openDatePicker(targetInput, anchorButton) {
  const parsed = parseDateValue(targetInput.value);
  const today = new Date();
  datePickerState.target = targetInput;
  datePickerState.anchor = anchorButton;
  datePickerState.year = parsed?.year ?? today.getFullYear();
  datePickerState.month = parsed?.month ?? today.getMonth();
  renderDatePicker();
  positionDatePicker();
  ui.datePicker.hidden = false;
}

function closeDatePicker() {
  ui.datePicker.hidden = true;
  datePickerState.target = null;
  datePickerState.anchor = null;
}

function positionDatePicker() {
  if (!datePickerState.anchor) return;
  const rect = datePickerState.anchor.getBoundingClientRect();
  const top = rect.bottom + 8;
  const left = Math.max(16, rect.left - 220);
  ui.datePicker.style.top = `${top}px`;
  ui.datePicker.style.left = `${left}px`;
}

function renderDatePicker() {
  ui.dateTitle.textContent = `${MONTHS[datePickerState.month]} ${datePickerState.year}`;
  ui.dateWeekdays.innerHTML = WEEKDAYS.map((day) => `<div>${day}</div>`).join("");

  const firstDay = new Date(datePickerState.year, datePickerState.month, 1);
  const startOffset = firstDay.getDay();
  const daysInMonth = new Date(datePickerState.year, datePickerState.month + 1, 0).getDate();
  const selected = parseDateValue(datePickerState.target?.value || "");

  ui.dateGrid.innerHTML = "";

  for (let index = 0; index < 42; index += 1) {
    const cell = document.createElement("button");
    cell.type = "button";
    cell.className = "date-cell";
    const dayNumber = index - startOffset + 1;
    if (dayNumber < 1 || dayNumber > daysInMonth) {
      cell.disabled = true;
      cell.classList.add("muted");
      cell.textContent = "";
    } else {
      const value = formatDateParts(datePickerState.year, datePickerState.month, dayNumber);
      cell.textContent = String(dayNumber);
      cell.dataset.value = value;
      if (
        selected &&
        selected.year === datePickerState.year &&
        selected.month === datePickerState.month &&
        selected.day === dayNumber
      ) {
        cell.classList.add("selected");
      }
      cell.addEventListener("click", () => {
        if (!datePickerState.target) return;
        datePickerState.target.value = value;
        closeDatePicker();
      });
    }
    ui.dateGrid.appendChild(cell);
  }
}

function applyUrlState() {
  const params = new URLSearchParams(window.location.search);
  const query = params.get("q") || "";
  const sort = params.get("sort") || "total_score";
  const dateFrom = params.get("from") || "";
  const dateTo = params.get("to") || "";
  ui.queryInput.value = query;
  ui.sortSelect.value = sort;
  ui.dateFrom.value = dateFrom;
  ui.dateTo.value = dateTo;
  state.sort = sort;
  state.dateFrom = dateFrom;
  state.dateTo = dateTo;
  const parsed = parseQuery(query);
  state.include = parsed.include;
  state.exclude = parsed.exclude;
  state.invalid = parsed.invalid;
}

function syncUrl() {
  const params = new URLSearchParams();
  const query = composeQuery(state.include, state.exclude);
  if (query) {
    params.set("q", query);
  }
  if (state.sort !== "total_score") {
    params.set("sort", state.sort);
  }
  if (state.dateFrom) {
    params.set("from", state.dateFrom);
  }
  if (state.dateTo) {
    params.set("to", state.dateTo);
  }
  const next = `${window.location.pathname}${params.toString() ? `?${params}` : ""}`;
  window.history.replaceState({}, "", next);
}

function filterAndSort() {
  const filtered = state.papers.filter((paper) => {
    const keywords = new Set(paper.keywords);
    const published = paper.published_date || "";
    if (state.dateFrom && (!published || published < state.dateFrom)) return false;
    if (state.dateTo && (!published || published > state.dateTo)) return false;
    return state.include.every((tag) => keywords.has(tag)) && !state.exclude.some((tag) => keywords.has(tag));
  });

  const sorted = filtered.sort((a, b) => {
    if (state.sort === "published_date") {
      return (b.published_date || "").localeCompare(a.published_date || "") || a.total_rank - b.total_rank;
    }
    if (state.sort === "cited_by_count") {
      return (b.cited_by_count || 0) - (a.cited_by_count || 0) || a.total_rank - b.total_rank;
    }
    return (b[state.sort] || 0) - (a[state.sort] || 0) || a.total_rank - b.total_rank;
  });

  state.filtered = sorted;
  state.virtual.scrollTop = 0;
  if (ui.resultsViewport) {
    ui.resultsViewport.scrollTop = 0;
  }
}

function renderMeta() {
  if (!state.stats) return;
  const updated = new Date(state.stats.updated_at);
  ui.meta.textContent = `${formatNumber(state.stats.paper_count)} papers · updated ${updated.toISOString().slice(0, 10)}`;
  ui.tagCount.textContent = `${formatNumber(state.stats.tag_count)} tags`;
}

function renderQueryState() {
  ui.includeChips.innerHTML = "";
  ui.excludeChips.innerHTML = "";

  state.include.forEach((tag) => ui.includeChips.appendChild(makeFilterChip(tag, "include")));
  state.exclude.forEach((tag) => ui.excludeChips.appendChild(makeFilterChip(tag, "exclude")));

  const dateError = !isValidDateInput(state.dateFrom) || !isValidDateInput(state.dateTo);
  if (state.invalid.length || dateError) {
    ui.queryErrors.hidden = false;
    const messages = [];
    if (state.invalid.length) {
      messages.push(`Unrecognized tags: ${state.invalid.join(", ")}`);
    }
    if (dateError) {
      messages.push("Date format must be YYYY-MM-DD");
    }
    ui.queryErrors.textContent = messages.join(" · ");
  } else {
    ui.queryErrors.hidden = true;
    ui.queryErrors.textContent = "";
  }
}

function makeFilterChip(tag, kind) {
  const chip = document.createElement("div");
  chip.className = `chip ${kind}`;
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = tag;
  button.addEventListener("click", () => removeTag(tag, kind));
  chip.appendChild(button);
  return chip;
}

function removeTag(tag, kind) {
  state[kind] = state[kind].filter((entry) => entry !== tag);
  refresh();
}

function addIncludeTag(tag) {
  if (!state.include.includes(tag)) {
    state.include.push(tag);
  }
  state.exclude = state.exclude.filter((entry) => entry !== tag);
  refresh();
}

function renderTagCloud() {
  ui.tagCloud.innerHTML = "";
  state.tags.slice(0, 40).forEach((tag) => {
    const chip = document.createElement("div");
    chip.className = "tag-chip";
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = `${tag.label} (${formatNumber(tag.count)})`;
    button.addEventListener("click", () => addIncludeTag(tag.label));
    chip.appendChild(button);
    ui.tagCloud.appendChild(chip);
  });
}

function estimateVirtualWindow() {
  const total = state.filtered.length;
  const viewport = ui.resultsViewport?.clientHeight || 640;
  const rowHeight = state.virtual.rowHeight;
  const visibleCount = Math.max(1, Math.ceil(viewport / rowHeight));
  const start = Math.max(0, Math.floor(state.virtual.scrollTop / rowHeight) - state.virtual.overscan);
  const end = Math.min(total, start + visibleCount + state.virtual.overscan * 2);
  return { start, end, total };
}

function renderResults() {
  state.renderQueued = false;
  const { start, end, total } = estimateVirtualWindow();
  const topPadding = start * state.virtual.rowHeight;
  const bottomPadding = Math.max(0, (total - end) * state.virtual.rowHeight);

  ui.resultsBody.innerHTML = "";

  if (topPadding > 0) {
    ui.resultsBody.appendChild(makeSpacerRow(topPadding));
  }

  state.visible = state.filtered.slice(start, end);
  state.visible.forEach((paper, offset) => {
    const index = start + offset;
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${formatRank(paper, index)}</td>
      <td>
        <a class="paper-title" href="${paper.abs_url}" target="_blank" rel="noreferrer">${escapeHtml(paper.title)}</a>
      </td>
      <td>${paper.published_date || ""}</td>
      <td>${formatNumber(paper.cited_by_count)}</td>
      <td>${formatScore(paper.total_score)}</td>
      <td>${formatScore(paper.hot_score)}</td>
      <td>${renderMiniChips(paper.keywords)}</td>
    `;
    row.querySelectorAll(".mini-chip button").forEach((button) => {
      button.addEventListener("click", () => addIncludeTag(button.dataset.tag));
    });
    ui.resultsBody.appendChild(row);
  });

  if (bottomPadding > 0) {
    ui.resultsBody.appendChild(makeSpacerRow(bottomPadding));
  }

  ui.resultsSummary.textContent = `${formatNumber(state.filtered.length)} matching papers`;
}

function scheduleRenderResults() {
  if (state.renderQueued) return;
  state.renderQueued = true;
  window.requestAnimationFrame(() => {
    renderResults();
  });
}

function makeSpacerRow(height) {
  const row = document.createElement("tr");
  row.setAttribute("aria-hidden", "true");
  row.className = "spacer-row";
  const cell = document.createElement("td");
  cell.colSpan = 7;
  cell.style.height = `${height}px`;
  cell.style.padding = "0";
  cell.style.border = "0";
  row.appendChild(cell);
  return row;
}

function formatRank(paper, index) {
  if (state.sort === "total_score") return paper.total_rank;
  if (state.sort === "hot_score") return paper.hot_rank;
  return index + 1;
}

function tagColorStyle(tag) {
  let hash = 0;
  for (let index = 0; index < tag.length; index += 1) {
    hash = (hash * 31 + tag.charCodeAt(index)) >>> 0;
  }
  const hue = hash % 360;
  return `--tag-bg:hsl(${hue} 72% 96%);--tag-border:hsl(${hue} 48% 78%);--tag-ink:hsl(${hue} 36% 24%);`;
}

function renderMiniChips(items) {
  return `
    <div class="mini-chips">
      ${items
        .map(
          (tag) =>
            `<span class="mini-chip" style="${tagColorStyle(tag)}"><button type="button" data-tag="${escapeHtml(tag)}">${escapeHtml(tag)}</button></span>`,
        )
        .join("")}
    </div>
  `;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function refresh() {
  ui.queryInput.value = composeQuery(state.include, state.exclude);
  state.dateFrom = ui.dateFrom.value.trim();
  state.dateTo = ui.dateTo.value.trim();
  hideSuggestions();
  if (!isValidDateInput(state.dateFrom) || !isValidDateInput(state.dateTo)) {
    renderQueryState();
    syncUrl();
    return;
  }
  filterAndSort();
  renderQueryState();
  renderResults();
  syncUrl();
}

async function copyShareLink() {
  syncUrl();
  await navigator.clipboard.writeText(window.location.href);
  ui.resultsSummary.textContent = `${formatNumber(state.filtered.length)} matching papers · link copied`;
}

async function init() {
  const [papers, tags, aliasMap, stats] = await Promise.all([
    fetch("./data/papers.min.json").then((response) => response.json()),
    fetch("./data/tags.json").then((response) => response.json()),
    fetch("./data/aliases.json").then((response) => response.json()),
    fetch("./data/stats.json").then((response) => response.json()),
  ]);

  state.papers = papers;
  state.tags = tags;
  state.aliasMap = aliasMap;
  state.stats = stats;
  state.tagByNorm = Object.fromEntries(tags.map((tag) => [normalizeKey(tag.label), tag.label]));
  buildSuggestionEntries();

  applyUrlState();
  renderMeta();
  renderTagCloud();
  filterAndSort();
  renderQueryState();
  renderResults();

  ui.form.addEventListener("submit", (event) => {
    event.preventDefault();
    const parsed = parseQuery(ui.queryInput.value);
    state.include = parsed.include;
    state.exclude = parsed.exclude;
    state.invalid = parsed.invalid;
    refresh();
  });

  ui.queryInput.addEventListener("input", () => {
    updateSuggestions();
  });

  ui.queryInput.addEventListener("keydown", (event) => {
    if (!state.suggestions.length) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      state.activeSuggestion = Math.min(state.activeSuggestion + 1, state.suggestions.length - 1);
      renderSuggestions();
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      state.activeSuggestion = Math.max(state.activeSuggestion - 1, 0);
      renderSuggestions();
      return;
    }
    if (event.key === "Enter" && state.activeSuggestion >= 0) {
      event.preventDefault();
      applySuggestion(state.suggestions[state.activeSuggestion].canonical);
      return;
    }
    if (event.key === "Escape") {
      hideSuggestions();
    }
  });

  ui.queryInput.addEventListener("focus", () => {
    updateSuggestions();
  });

  ui.queryInput.addEventListener("blur", () => {
    window.setTimeout(hideSuggestions, 120);
  });

  ui.dateTriggers.forEach((button) => {
    button.addEventListener("click", () => {
      const target = document.querySelector(`#${button.dataset.dateTarget}`);
      if (!target) return;
      if (!ui.datePicker.hidden && datePickerState.target === target) {
        closeDatePicker();
        return;
      }
      openDatePicker(target, button);
    });
  });

  [ui.dateFrom, ui.dateTo].forEach((input) => {
    input.addEventListener("focus", () => {
      const trigger = document.querySelector(`.date-trigger[data-date-target="${input.id}"]`);
      if (trigger) {
        openDatePicker(input, trigger);
      }
    });
  });

  ui.datePrev.addEventListener("click", () => {
    datePickerState.month -= 1;
    if (datePickerState.month < 0) {
      datePickerState.month = 11;
      datePickerState.year -= 1;
    }
    renderDatePicker();
  });

  ui.dateNext.addEventListener("click", () => {
    datePickerState.month += 1;
    if (datePickerState.month > 11) {
      datePickerState.month = 0;
      datePickerState.year += 1;
    }
    renderDatePicker();
  });

  ui.dateClear.addEventListener("click", () => {
    if (datePickerState.target) {
      datePickerState.target.value = "";
    }
    closeDatePicker();
  });

  ui.sortSelect.addEventListener("change", () => {
    state.sort = ui.sortSelect.value;
    filterAndSort();
    renderResults();
    syncUrl();
  });

  ui.clearButton.addEventListener("click", () => {
    state.include = [];
    state.exclude = [];
    state.invalid = [];
    state.sort = "total_score";
    state.dateFrom = "";
    state.dateTo = "";
    ui.sortSelect.value = "total_score";
    ui.dateFrom.value = "";
    ui.dateTo.value = "";
    refresh();
  });

  ui.shareButton.addEventListener("click", () => {
    copyShareLink().catch(() => {
      ui.resultsSummary.textContent = `${formatNumber(state.filtered.length)} matching papers`;
    });
  });

  ui.resultsViewport?.addEventListener("scroll", () => {
    state.virtual.scrollTop = ui.resultsViewport.scrollTop;
    scheduleRenderResults();
  });

  window.addEventListener("resize", () => {
    scheduleRenderResults();
    if (!ui.datePicker.hidden) {
      positionDatePicker();
    }
  });

  document.addEventListener("mousedown", (event) => {
    if (ui.datePicker.hidden) return;
    const target = event.target;
    if (ui.datePicker.contains(target)) return;
    if (target.closest(".date-input")) return;
    closeDatePicker();
  });
}

init().catch((error) => {
  ui.resultsSummary.textContent = "Failed to load site data";
  ui.queryErrors.hidden = false;
  ui.queryErrors.textContent = error instanceof Error ? error.message : String(error);
});
