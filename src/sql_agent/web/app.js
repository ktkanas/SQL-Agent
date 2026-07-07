const messagesEl = document.querySelector("#messages");
const formEl = document.querySelector("#chatForm");
const inputEl = document.querySelector("#questionInput");
const traceListEl = document.querySelector("#traceList");
const traceEmptyEl = document.querySelector("#traceEmpty");
const tableListEl = document.querySelector("#tableList");
const connectionStateEl = document.querySelector("#connectionState");
const tableCountEl = document.querySelector("#tableCount");
const refreshTablesEl = document.querySelector("#refreshTables");
const clearTraceEl = document.querySelector("#clearTrace");

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatInline(value) {
  return escapeHtml(value)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
}

function isTableSeparator(line) {
  return /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line);
}

function renderMarkdown(text) {
  const lines = text.split(/\r?\n/);
  const chunks = [];
  let listItems = [];

  function flushList() {
    if (!listItems.length) {
      return;
    }
    chunks.push(`<ul>${listItems.map((item) => `<li>${formatInline(item)}</li>`).join("")}</ul>`);
    listItems = [];
  }

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index].trim();

    if (!line) {
      flushList();
      continue;
    }

    if (line.includes("|") && lines[index + 1] && isTableSeparator(lines[index + 1])) {
      flushList();
      const headers = line.split("|").map((cell) => cell.trim()).filter(Boolean);
      index += 2;
      const rows = [];

      while (index < lines.length && lines[index].includes("|")) {
        rows.push(lines[index].split("|").map((cell) => cell.trim()).filter(Boolean));
        index += 1;
      }
      index -= 1;

      chunks.push(`
        <table class="message-table">
          <thead><tr>${headers.map((cell) => `<th>${formatInline(cell)}</th>`).join("")}</tr></thead>
          <tbody>${rows.map((row) => `<tr>${row.map((cell) => `<td>${formatInline(cell)}</td>`).join("")}</tr>`).join("")}</tbody>
        </table>
      `);
      continue;
    }

    if (/^#{2,4}\s+/.test(line)) {
      flushList();
      chunks.push(`<h3>${formatInline(line.replace(/^#{2,4}\s+/, ""))}</h3>`);
      continue;
    }

    if (/^[-*]\s+/.test(line)) {
      listItems.push(line.replace(/^[-*]\s+/, ""));
      continue;
    }

    if (/^\d+\.\s+/.test(line)) {
      listItems.push(line.replace(/^\d+\.\s+/, ""));
      continue;
    }

    flushList();
    chunks.push(`<p>${formatInline(line)}</p>`);
  }

  flushList();
  return chunks.join("");
}

function scrollMessages() {
  messagesEl.scrollTo({ top: messagesEl.scrollHeight, behavior: "smooth" });
}

function addMessage(role, text, loading = false) {
  const article = document.createElement("article");
  article.className = `message ${role}${loading ? " loading" : ""}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "You" : "AI";

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  const content = document.createElement("div");
  content.className = "message-content";
  content.innerHTML = loading
    ? '<span class="thinking">Thinking <span></span><span></span><span></span></span>'
    : renderMarkdown(text);
  bubble.appendChild(content);

  article.append(avatar, bubble);
  messagesEl.appendChild(article);
  scrollMessages();

  return { article, content };
}

function addTrace(title, content) {
  traceEmptyEl.style.display = "none";

  const card = document.createElement("details");
  card.className = "trace-card";
  card.open = traceListEl.children.length === 0;

  const summary = document.createElement("summary");
  summary.innerHTML = `${escapeHtml(title)} <span>${content ? `${content.length} chars` : "empty"}</span>`;

  const pre = document.createElement("pre");
  pre.textContent = content || "(empty)";

  card.append(summary, pre);
  traceListEl.prepend(card);
}

async function loadTables() {
  tableListEl.innerHTML = "";
  connectionStateEl.textContent = "Checking database";
  tableCountEl.textContent = "Refreshing schema";

  try {
    const response = await fetch("/api/tables");
    if (!response.ok) {
      throw new Error(await response.text());
    }

    const data = await response.json();
    connectionStateEl.textContent = "Database online";
    tableCountEl.textContent = `${data.tables.length} table${data.tables.length === 1 ? "" : "s"} available`;

    if (!data.tables.length) {
      tableListEl.innerHTML = '<div class="trace-empty">No tables found.</div>';
      return;
    }

    for (const table of data.tables) {
      const button = document.createElement("button");
      button.className = "table-item";
      button.type = "button";

      const name = document.createElement("span");
      name.className = "table-name";
      name.textContent = table;

      const meta = document.createElement("span");
      meta.className = "table-meta";
      meta.textContent = "Click to draft a profiling question";

      const label = document.createElement("span");
      label.append(name, meta);
      button.appendChild(label);

      button.addEventListener("click", () => {
        inputEl.value = `Profile the ${table} table: columns, row count, useful segments, and data quality notes`;
        inputEl.focus();
        resizeInput();
      });
      tableListEl.appendChild(button);
    }
  } catch (error) {
    connectionStateEl.textContent = "Database offline";
    tableCountEl.textContent = "Connection failed";
    tableListEl.innerHTML = '<div class="trace-empty">Could not load tables.</div>';
  }
}

function resizeInput() {
  inputEl.style.height = "auto";
  inputEl.style.height = `${Math.min(inputEl.scrollHeight, 150)}px`;
}

async function ask(question) {
  addMessage("user", question);
  const pending = addMessage("assistant", "", true);

  formEl.querySelector("button").disabled = true;

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "The agent could not answer.");
    }

    const data = await response.json();
    pending.article.classList.remove("loading");
    pending.content.innerHTML = renderMarkdown(data.answer || "No answer returned.");

    for (const sql of data.sql_queries || []) {
      addTrace("SQL query", sql);
    }

    for (const result of data.tool_results || []) {
      addTrace(result.name, result.content);
    }
  } catch (error) {
    pending.article.classList.remove("loading");
    pending.content.innerHTML = renderMarkdown(error.message);
  } finally {
    formEl.querySelector("button").disabled = false;
    scrollMessages();
  }
}

formEl.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = inputEl.value.trim();
  if (!question) {
    return;
  }

  inputEl.value = "";
  resizeInput();
  ask(question);
});

inputEl.addEventListener("input", resizeInput);
inputEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    formEl.requestSubmit();
  }
});

document.querySelectorAll(".suggestions button").forEach((button) => {
  button.addEventListener("click", () => {
    inputEl.value = button.textContent;
    resizeInput();
    formEl.requestSubmit();
  });
});

refreshTablesEl.addEventListener("click", loadTables);
clearTraceEl.addEventListener("click", () => {
  traceListEl.innerHTML = "";
  traceEmptyEl.style.display = "";
});

loadTables();
