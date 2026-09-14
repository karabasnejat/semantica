const config = window.SEMANTICA_CONFIG || {};
const params = new URLSearchParams(window.location.search);
const form = document.querySelector("#form");
const apiBaseInput = document.querySelector("#api-base");
const repositoryUrlInput = document.querySelector("#repository-url");
const statusElement = document.querySelector("#status");
const statsElement = document.querySelector("#stats");
const nodesElement = document.querySelector("#nodes");
const edgesElement = document.querySelector("#edges");
const actionsElement = document.querySelector("#actions");
const wikiElement = document.querySelector("#wiki");
const wikiFrameElement = document.querySelector("#wiki-frame");
const submitButton = document.querySelector("#submit");

const storedApiBase = window.localStorage.getItem("semantica.apiBaseUrl");
apiBaseInput.value = params.get("api") || storedApiBase || config.apiBaseUrl || "";

function normalizeApiBase(value) {
  const trimmed = value.trim();
  if (!trimmed) {
    return window.location.origin;
  }
  return trimmed.replace(/\/+$/, "");
}

function setStatus(message, isError = false) {
  statusElement.textContent = message;
  statusElement.classList.toggle("error", isError);
}

function normalizeErrorMessage(error) {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  if (typeof error === "string" && error) {
    return error;
  }
  return "Build failed.";
}

function resetResult() {
  statsElement.hidden = true;
  actionsElement.innerHTML = "";
  wikiElement.hidden = true;
  wikiFrameElement.srcdoc = "";
}

function renderWiki(html) {
  wikiFrameElement.srcdoc = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <base target="_blank">
    <style>
      :root { color-scheme: dark; }
      body {
        margin: 0;
        color: #eef2ff;
        background: transparent;
        font: 15px/1.6 Inter, system-ui, sans-serif;
      }
      h1 { font-size: 30px; }
      h2 {
        margin-top: 32px;
        border-bottom: 1px solid #263047;
      }
      a { color: #63e6ff; }
      code { color: #c4b5fd; }
      pre {
        overflow: auto;
        padding: 16px;
        border-radius: 12px;
        background: #0b1020;
      }
      table {
        width: 100%;
        border-collapse: collapse;
      }
      th, td {
        padding: 8px;
        border: 1px solid #263047;
        text-align: left;
      }
    </style>
  </head>
  <body>${html}</body>
</html>`;
}

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  const text = await response.text();
  return text ? { detail: text } : {};
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  submitButton.disabled = true;
  resetResult();

  const apiBaseUrl = normalizeApiBase(apiBaseInput.value);
  window.localStorage.setItem("semantica.apiBaseUrl", apiBaseUrl);
  setStatus("Cloning repository and building graph…");

  try {
    const response = await fetch(`${apiBaseUrl}/api/build`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repository_url: repositoryUrlInput.value }),
    });
    const data = await parseResponse(response);
    if (!response.ok) {
      throw new Error(data.detail || "Build failed.");
    }

    nodesElement.textContent = data.node_count.toLocaleString();
    edgesElement.textContent = data.edge_count.toLocaleString();
    statsElement.hidden = false;

    const graphUrl = new URL(data.graph_url, `${apiBaseUrl}/`).toString();
    const downloadLink = document.createElement("a");
    downloadLink.className = "button";
    downloadLink.href = graphUrl;
    downloadLink.target = "_blank";
    downloadLink.rel = "noreferrer";
    downloadLink.textContent = "Download graph.json";
    actionsElement.replaceChildren(downloadLink);

    renderWiki(data.wiki_html);
    wikiElement.hidden = false;
    setStatus("Wiki ready.");
  } catch (error) {
    setStatus(normalizeErrorMessage(error), true);
  } finally {
    submitButton.disabled = false;
  }
});
