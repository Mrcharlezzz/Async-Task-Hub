const UI = {
  runButton: document.getElementById("run"),
  runStatus: document.getElementById("run-status"),
  digitsInput: document.getElementById("digits"),
  pollInput: document.getElementById("poll-interval"),
  streaming: {
    progress: document.querySelector('.progress-bar[data-panel="streaming"]'),
    result: document.querySelector('.result[data-panel="streaming"]'),
    metrics: document.querySelector('.metrics[data-panel="streaming"]'),
  },
  polling: {
    progress: document.querySelector('.progress-bar[data-panel="polling"]'),
    result: document.querySelector('.result[data-panel="polling"]'),
    metrics: document.querySelector('.metrics[data-panel="polling"]'),
  },
};

const API_BASE = "/api";
const WS_BASE = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}`;

const formatMs = (ms) => `${Math.round(ms)} ms`;
const formatSec = (ms) => `${(ms / 1000).toFixed(2)} s`;
const formatBytes = (bytes) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
};

class ApiClient {
  async startPi(digits) {
    const res = await fetch(`${API_BASE}/calculate_pi`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ n: digits }),
    });
    if (!res.ok) {
      throw new Error(`Failed to start task (${res.status})`);
    }
    const data = await res.json();
    return data.id;
  }

  async startNaivePi(digits, taskId) {
    const res = await fetch(`${API_BASE}/naive/calculate_pi`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ digits, task_id: taskId }),
    });
    if (!res.ok) {
      throw new Error(`Failed to start naive task (${res.status})`);
    }
    const data = await res.json();
    return data.task_id;
  }

  async getProgress(taskId) {
    return this._getJson(`${API_BASE}/check_progress?task_id=${encodeURIComponent(taskId)}`);
  }

  async getResult(taskId) {
    return this._getJson(`${API_BASE}/task_result?task_id=${encodeURIComponent(taskId)}`);
  }

  async getNaiveProgress(taskId) {
    return this._getJson(
      `${API_BASE}/naive/check_progress?task_id=${encodeURIComponent(taskId)}`
    );
  }

  async getNaiveResult(taskId) {
    return this._getJson(`${API_BASE}/naive/task_result?task_id=${encodeURIComponent(taskId)}`);
  }

  async _getJson(url) {
    const res = await fetch(url);
    const text = await res.text();
    const bytes = text.length;
    let data = null;
    if (text) {
      try {
        data = JSON.parse(text);
      } catch {
        data = null;
      }
    }
    return { ok: res.ok, status: res.status, data, bytes };
  }
}

class WsClient {
  constructor(base) {
    this.base = base;
  }

  connect(taskId, onMessage, onOpen, onClose) {
    const ws = new WebSocket(`${this.base}/ws/tasks/${taskId}`);
    const keepalive = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send("ping");
      }
    }, 1000);
    ws.addEventListener("open", () => onOpen?.());
    ws.addEventListener("message", (event) => onMessage(event.data));
    ws.addEventListener("close", () => {
      clearInterval(keepalive);
      onClose?.();
    });
    return {
      close: () => ws.close(),
    };
  }
}

class StreamingEngine {
  constructor(taskId, wsClient, state) {
    this.taskId = taskId;
    this.wsClient = wsClient;
    this.state = state;
    this.socket = null;
    this.startTime = performance.now();
  }

  start() {
    this.socket = this.wsClient.connect(
      this.taskId,
      (data) => this._handleMessage(data),
      () => {},
      () => {}
    );
  }

  stop() {
    this.socket?.close();
  }

  _handleMessage(raw) {
    this.state.metrics.messages += 1;
    this.state.metrics.bytes += raw.length;
    if (!this.state.metrics.firstUpdateMs) {
      this.state.metrics.firstUpdateMs = performance.now() - this.startTime;
    }
    let message;
    try {
      message = JSON.parse(raw);
    } catch {
      return;
    }
    if (message.type === "task.status") {
      const status = message.payload?.status;
      const progress = status?.progress?.percentage ?? 0;
      this.state.progress = progress;
      this.state.status = status?.state ?? "RUNNING";
    }
    if (message.type === "task.result_chunk") {
      const payload = message.payload;
      const data = Array.isArray(payload?.data) ? payload.data : [];
      if (data.length) {
        this.state.result += data.join("");
      }
      if (payload?.is_last) {
        this.state.completed = true;
        this.state.metrics.totalMs = performance.now() - this.startTime;
      }
    }
    if (message.type === "task.result") {
      this.state.completed = true;
      this.state.metrics.totalMs = performance.now() - this.startTime;
    }
  }
}

class PollingEngine {
  constructor(taskId, apiClient, state, intervalMs) {
    this.taskId = taskId;
    this.apiClient = apiClient;
    this.state = state;
    this.intervalMs = intervalMs;
    this.timer = null;
    this.inFlight = false;
    this.startTime = performance.now();
  }

  start() {
    this.timer = setInterval(() => this._tick(), this.intervalMs);
    this._tick();
  }

  stop() {
    clearInterval(this.timer);
  }

  async _tick() {
    if (this.inFlight || this.state.completed) return;
    this.inFlight = true;
    try {
      const progressRes = await this.apiClient.getNaiveProgress(this.taskId);
      this._record(progressRes.bytes);
      if (progressRes.ok && progressRes.data) {
        const progress = progressRes.data.progress?.percentage ?? 0;
        this.state.progress = progress;
        this.state.status = progressRes.data.state ?? "RUNNING";
        this._maybeFirstUpdate();
      }

      const resultRes = await this.apiClient.getNaiveResult(this.taskId);
      this._record(resultRes.bytes);
      if (resultRes.ok && resultRes.data) {
        const payload = resultRes.data.partial_result ?? "";
        this.state.result = typeof payload === "string" ? payload : JSON.stringify(payload);
        this._maybeFirstUpdate();
        if (resultRes.data.done === true) {
          this.state.completed = true;
          this.state.metrics.totalMs = performance.now() - this.startTime;
          this.stop();
        }
      }
    } finally {
      this.inFlight = false;
    }
  }

  _record(bytes) {
    this.state.metrics.requests += 1;
    this.state.metrics.bytes += bytes;
  }

  _maybeFirstUpdate() {
    if (!this.state.metrics.firstUpdateMs) {
      this.state.metrics.firstUpdateMs = performance.now() - this.startTime;
    }
  }
}

class RunController {
  constructor(apiClient, wsClient) {
    this.apiClient = apiClient;
    this.wsClient = wsClient;
    this.streamingEngine = null;
    this.pollingEngine = null;
  }

  async run(digits, pollInterval, state) {
    this._resetState(state);
    state.runStatus = "starting";
    render(state);
    try {
      const taskId = await this.apiClient.startPi(digits);
      await this.apiClient.startNaivePi(digits, taskId);
      state.taskId = taskId;
      state.runStatus = "running";
      this.streamingEngine = new StreamingEngine(taskId, this.wsClient, state.streaming);
      this.pollingEngine = new PollingEngine(taskId, this.apiClient, state.polling, pollInterval);
      this.streamingEngine.start();
      this.pollingEngine.start();
    } catch (err) {
      state.runStatus = "error";
      state.error = err.message || String(err);
    }
  }

  stop() {
    this.streamingEngine?.stop();
    this.pollingEngine?.stop();
  }

  _resetState(state) {
    state.taskId = null;
    state.runStatus = "idle";
    state.error = null;
    state.streaming.reset();
    state.polling.reset();
  }
}

const createModeState = () => ({
  status: "IDLE",
  progress: 0,
  result: "",
  completed: false,
  metrics: {
    firstUpdateMs: null,
    totalMs: null,
    messages: 0,
    requests: 0,
    bytes: 0,
  },
  reset() {
    this.status = "IDLE";
    this.progress = 0;
    this.result = "";
    this.completed = false;
    this.metrics.firstUpdateMs = null;
    this.metrics.totalMs = null;
    this.metrics.messages = 0;
    this.metrics.requests = 0;
    this.metrics.bytes = 0;
  },
});

const state = {
  taskId: null,
  runStatus: "idle",
  error: null,
  streaming: createModeState(),
  polling: createModeState(),
};

const apiClient = new ApiClient();
const wsClient = new WsClient(WS_BASE);
const controller = new RunController(apiClient, wsClient);

function render(state) {
  UI.runButton.disabled = state.runStatus === "running" || state.runStatus === "starting";
  UI.runStatus.textContent = state.error
    ? `Error: ${state.error}`
    : state.runStatus.toUpperCase();
  renderPanel(UI.streaming, state.streaming, true);
  renderPanel(UI.polling, state.polling, false);
}

function renderPanel(ui, mode, isStreaming) {
  ui.progress.style.width = `${Math.min(mode.progress * 100, 100)}%`;
  ui.result.textContent = mode.result || "—";

  const metrics = [
    ["Time to first update", mode.metrics.firstUpdateMs ? formatMs(mode.metrics.firstUpdateMs) : "—"],
    ["Total time", mode.metrics.totalMs ? formatSec(mode.metrics.totalMs) : "—"],
    [
      isStreaming ? "WS messages" : "HTTP requests",
      isStreaming ? mode.metrics.messages : mode.metrics.requests,
    ],
    ["Bytes received", formatBytes(mode.metrics.bytes)],
  ];

  ui.metrics.innerHTML = metrics
    .map(([label, value]) => `<div><dt>${label}</dt><dd>${value}</dd></div>`)
    .join("");
}

UI.runButton.addEventListener("click", async (event) => {
  event.preventDefault();
  controller.stop();
  const digits = Number(UI.digitsInput.value) || 500;
  const pollInterval = Number(UI.pollInput.value) || 150;
  await controller.run(digits, pollInterval, state);
});

setInterval(() => {
  render(state);
  if (state.streaming.completed && state.polling.completed) {
    state.runStatus = "done";
  }
}, 100);

render(state);
