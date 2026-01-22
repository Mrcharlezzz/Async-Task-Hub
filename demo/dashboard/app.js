import { API_BASE, WS_BASE, postJson, WsClient, ApiClient } from "../shared/transport.js";
import {
  formatMs,
  formatSec,
  formatBytes,
  StreamingEngine,
  TERMINAL_STATES,
} from "../shared/engine.js";

const UI = {
  piDigits: document.getElementById("pi-digits"),
  piStart: document.getElementById("pi-start"),
  docUrl: document.getElementById("doc-url"),
  docPath: document.getElementById("doc-path"),
  docKeywords: document.getElementById("doc-keywords"),
  docStart: document.getElementById("doc-start"),
  taskList: document.getElementById("task-list"),
  summaryTotal: document.getElementById("summary-total"),
  summaryRunning: document.getElementById("summary-running"),
  summaryCompleted: document.getElementById("summary-completed"),
  summaryThroughput: document.getElementById("summary-throughput"),
};

const wsClient = new WsClient(WS_BASE);

const api = new ApiClient({
  startTask: (type, payload) => {
    if (type === "compute_pi") {
      return postJson(`${API_BASE}/calculate_pi`, { n: payload.digits });
    }
    if (type === "document_analysis") {
      return postJson(`${API_BASE}/tasks/document-analysis`, {
        document_path: payload.documentPath,
        document_url: payload.documentUrl,
        keywords: payload.keywords,
      });
    }
    return Promise.resolve({ ok: false, status: 400, data: null, bytes: 0, elapsedMs: 0 });
  },
});

const tasks = [];

function createTaskState() {
  return {
    status: "QUEUED",
    progress: 0,
    result: "",
    statusMetrics: null,
    completed: false,
    metrics: {
      firstUpdateMs: null,
      totalMs: null,
      messages: 0,
      requests: 0,
      bytes: 0,
      latencyTotalMs: 0,
      latencyCount: 0,
      serverCpuMs: 0,
    },
  };
}

function renderSummary() {
  const total = tasks.length;
  const completed = tasks.filter((task) => task.state.completed).length;
  const running = total - completed;
  const now = performance.now();
  let messages = 0;
  let elapsedMs = 0;
  tasks.forEach((task) => {
    messages += task.state.metrics.messages;
    const taskElapsed = task.state.metrics.totalMs ?? (now - task.startTime);
    elapsedMs = Math.max(elapsedMs, taskElapsed);
  });
  const throughput = elapsedMs > 0 ? messages / (elapsedMs / 1000) : 0;
  UI.summaryTotal.textContent = String(total);
  UI.summaryRunning.textContent = String(running);
  UI.summaryCompleted.textContent = String(completed);
  UI.summaryThroughput.textContent = throughput ? `${throughput.toFixed(2)} updates/s` : "—";
}

function formatAvgLatency(metrics) {
  if (!metrics.latencyCount) return "—";
  return formatMs(metrics.latencyTotalMs / metrics.latencyCount);
}

function formatThroughput(task) {
  const elapsedMs = task.state.metrics.totalMs ?? (performance.now() - task.startTime);
  if (elapsedMs <= 0) return "—";
  const messages = task.state.metrics.messages;
  const rate = messages / (elapsedMs / 1000);
  return `${rate.toFixed(2)} updates/s`;
}

function updateTaskCard(task) {
  const { state, nodes } = task;
  const status = state.completed ? "COMPLETED" : state.status;
  nodes.status.textContent = status;
  nodes.statusText.textContent = status;
  const pct = Number.isFinite(state.progress) ? state.progress : 0;
  nodes.progress.textContent = `${Math.round(pct * 100)}%`;
  if (nodes.progressBar) {
    nodes.progressBar.style.width = `${Math.min(pct * 100, 100)}%`;
  }
  nodes.latency.textContent = formatAvgLatency(state.metrics);
  nodes.cpu.textContent = `${Math.round(state.metrics.serverCpuMs)} ms`;
  nodes.messages.textContent = String(state.metrics.messages);
  nodes.bytes.textContent = formatBytes(state.metrics.bytes);
  nodes.throughput.textContent = formatThroughput(task);
  nodes.duration.textContent = state.metrics.totalMs ? formatSec(state.metrics.totalMs) : "—";
  if (state.result) {
    nodes.result.textContent = state.result;
    nodes.result.scrollTop = nodes.result.scrollHeight;
  } else {
    nodes.result.textContent = "—";
  }
}

function createTaskCard(task) {
  const card = document.createElement("article");
  card.className = "task-card";
  card.innerHTML = `
    <header>
      <div class="task-title">${task.label}</div>
      <div class="task-status">${task.state.status}</div>
    </header>
    <div class="task-progress-track">
      <div class="task-progress-bar" style="width: 0%"></div>
    </div>
    <dl class="task-meta">
      <div><dt>Status</dt><dd class="task-status-text">${task.state.status}</dd></div>
      <div><dt>Progress</dt><dd class="task-progress">0%</dd></div>
      <div><dt>Latency (avg)</dt><dd class="task-latency">—</dd></div>
      <div><dt>Server CPU</dt><dd class="task-cpu">0 ms</dd></div>
      <div><dt>Messages</dt><dd class="task-messages">0</dd></div>
      <div><dt>Bytes</dt><dd class="task-bytes">0 B</dd></div>
      <div><dt>Throughput</dt><dd class="task-throughput">—</dd></div>
      <div><dt>Duration</dt><dd class="task-duration">—</dd></div>
    </dl>
    <div class="task-result">—</div>
  `;
  const nodes = {
    status: card.querySelector(".task-status"),
    statusText: card.querySelector(".task-status-text"),
    progress: card.querySelector(".task-progress"),
    progressBar: card.querySelector(".task-progress-bar"),
    latency: card.querySelector(".task-latency"),
    cpu: card.querySelector(".task-cpu"),
    messages: card.querySelector(".task-messages"),
    bytes: card.querySelector(".task-bytes"),
    throughput: card.querySelector(".task-throughput"),
    duration: card.querySelector(".task-duration"),
    result: card.querySelector(".task-result"),
  };
  task.nodes = nodes;
  UI.taskList.prepend(card);
  updateTaskCard(task);
}

function resolveDocumentPath(documentPath, documentUrl) {
  if (documentPath) return documentPath;
  if (!documentUrl) return "";
  try {
    const url = new URL(documentUrl);
    const name = url.pathname.split("/").pop() || "document.txt";
    return `/data/books/${name}`;
  } catch {
    return "";
  }
}

function parseKeywords(input) {
  return input
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

async function createTask(type, payload, label) {
  const taskRes = await api.startTask(type, payload);
  if (!taskRes.ok) {
    throw new Error(`Failed to start ${label} (${taskRes.status})`);
  }
  const taskId = taskRes.data?.id;
  const state = createTaskState();
  const task = {
    id: taskId,
    type,
    label: `${label} (${taskId})`,
    state,
    startTime: performance.now(),
    nodes: null,
  };
  tasks.push(task);
  createTaskCard(task);

  task.engine = new StreamingEngine({
    taskId,
    wsClient,
    state,
    onResultChunk: (payload, taskState) => {
      if (type === "compute_pi") {
        const payloadData = payload?.data;
        if (Array.isArray(payloadData)) {
          if (payloadData.length) {
            taskState.result += payloadData.join("");
          }
        } else if (typeof payloadData === "string" && payloadData) {
          taskState.result += payloadData;
        }
      }
      if (type === "document_analysis") {
        const data = Array.isArray(payload?.data) ? payload.data : [];
        if (data.length) {
          const lines = [];
          for (const item of data) {
            const line = item?.snippet ? `[line ${item.location?.line ?? "?"}] ${item.keyword ?? "keyword"}: ${item.snippet}` : "";
            if (line) lines.push(line);
          }
          if (lines.length) {
            taskState.result = taskState.result
              ? `${taskState.result}\n${lines.join("\n")}`
              : lines.join("\n");
          }
        }
      }
    },
    onUpdate: () => {
      if (taskStateShouldStop(task.state) && !task.state.completed) {
        task.state.completed = true;
        if (!task.state.metrics.totalMs) {
          task.state.metrics.totalMs = performance.now() - task.startTime;
        }
      }
      updateTaskCard(task);
      renderSummary();
    },
  });
  task.engine.start();
  renderSummary();
}

function taskStateShouldStop(state) {
  return TERMINAL_STATES.has(state.status);
}

UI.piStart?.addEventListener("click", async () => {
  const digits = Number(UI.piDigits?.value) || 200;
  try {
    await createTask("compute_pi", { digits }, "Compute Pi");
  } catch (error) {
    console.error(error);
  }
});

UI.docStart?.addEventListener("click", async () => {
  const documentUrl = UI.docUrl?.value.trim() || "";
  const documentPath = resolveDocumentPath(UI.docPath?.value.trim(), documentUrl);
  const keywords = parseKeywords(UI.docKeywords?.value || "");
  if (!documentPath && !documentUrl) {
    alert("Document path or URL is required");
    return;
  }
  if (!keywords.length) {
    alert("Keywords are required");
    return;
  }
  try {
    await createTask(
      "document_analysis",
      { documentPath, documentUrl, keywords },
      "Document Analysis"
    );
  } catch (error) {
    console.error(error);
  }
});

setInterval(() => {
  tasks.forEach(updateTaskCard);
  renderSummary();
}, 500);

renderSummary();
