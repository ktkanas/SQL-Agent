const messagesEl = document.querySelector("#messages");
const formEl = document.querySelector("#chatForm");
const inputEl = document.querySelector("#questionInput");
const traceListEl = document.querySelector("#traceList");
const traceEmptyEl = document.querySelector("#traceEmpty");
const tableListEl = document.querySelector("#tableList");
const connectionStateEl = document.querySelector("#connectionState");
const refreshTablesEl = document.querySelector("#refreshTables");
const clearTraceEl = document.querySelector("#clearTrace");

function scrollMessages() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function addMessage(role, text, loading = false) {
  const article = document.createElement("article");
  article.className = `message ${role}${loading ? " loading" : ""}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "You" : "AI";

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  bubble.appendChild(paragraph);

  article.append(avatar, bubble);
  messagesEl.appendChild(article);
  scrollMessages();

  return { article, paragraph };
}

function addTrace(title, content) {
  traceEmptyEl.style.display = "none";

  const card = document.createElement("section");
  card.className = "trace-card";

  const heading = document.createElement("strong");
  heading.textContent = title;

  const pre = document.createElement("pre");
  pre.textContent = content || "(empty)";

  card.append(heading, pre);
  traceListEl.prepend(card);
}

async function loadTables() {
  tableListEl.innerHTML = "";
  connectionStateEl.textContent = "Checking database";

  try {
    const response = await fetch("/api/tables");
    if (!response.ok) {
      throw new Error(await response.text());
    }

    const data = await response.json();
    connectionStateEl.textContent = `${data.tables.length} tables connected`;

    if (!data.tables.length) {
      tableListEl.innerHTML = '<div class="trace-empty">No tables found.</div>';
      return;
    }

    for (const table of data.tables) {
      const button = document.createElement("button");
      button.className = "table-item";
      button.type = "button";
      button.textContent = table;
      button.addEventListener("click", () => {
        inputEl.value = `Describe the ${table} table and show useful sample rows`;
        inputEl.focus();
        resizeInput();
      });
      tableListEl.appendChild(button);
    }
  } catch (error) {
    connectionStateEl.textContent = "Database offline";
    tableListEl.innerHTML = '<div class="trace-empty">Could not load tables.</div>';
  }
}

function resizeInput() {
  inputEl.style.height = "auto";
  inputEl.style.height = `${Math.min(inputEl.scrollHeight, 150)}px`;
}

async function ask(question) {
  addMessage("user", question);
  const pending = addMessage("assistant", "Working", true);

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
    pending.paragraph.textContent = data.answer || "No answer returned.";

    for (const sql of data.sql_queries || []) {
      addTrace("SQL", sql);
    }

    for (const result of data.tool_results || []) {
      addTrace(result.name, result.content);
    }
  } catch (error) {
    pending.article.classList.remove("loading");
    pending.paragraph.textContent = error.message;
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
