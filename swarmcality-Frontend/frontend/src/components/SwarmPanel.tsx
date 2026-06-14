"use client";

import { useState, useEffect, useRef, useCallback } from "react";

const SWARM_WS = process.env.NEXT_PUBLIC_SWARM_WS_URL ?? "ws://localhost:8765/ws";
const SWARM_HTTP = process.env.NEXT_PUBLIC_SWARM_API_URL ?? "http://localhost:8765";

// ── Topology definitions ──────────────────────────────────────────────────────

const TOPOLOGIES: Record<string, { name: string; description: string; agents: string[] }> = {
  coding_swarm: {
    name: "Coding Swarm",
    description: "Planner + Coder + Critic for focused, single-task coding jobs.",
    agents: ["orchestrator", "planner", "coder", "critic"],
  },
  software_delivery: {
    name: "Software Delivery",
    description: "Full 8-phase lifecycle: Discovery → Planning → Architecture → Build → QA → Deploy.",
    agents: [
      "chief_orchestrator",
      "product_manager",
      "architecture",
      "frontend_engineer",
      "backend_engineer",
      "database_engineer",
      "qa_engineer",
      "code_reviewer",
      "debug_agent",
      "devops_engineer",
      "deployment_engineer",
    ],
  },
  research_swarm: {
    name: "Research Swarm",
    description: "Market research, synthesis and critique for discovery tasks.",
    agents: ["orchestrator", "market_research", "critic", "memory_agent"],
  },
  simple_chat: {
    name: "Simple Chat",
    description: "A single orchestrator — fast, low-cost, for Q&A or small tasks.",
    agents: ["orchestrator"],
  },
};

const ALL_AGENTS = [
  "orchestrator",
  "chief_orchestrator",
  "planner",
  "coder",
  "frontend_engineer",
  "backend_engineer",
  "database_engineer",
  "integration_engineer",
  "qa_engineer",
  "code_reviewer",
  "debug_agent",
  "product_manager",
  "architecture",
  "market_research",
  "critic",
  "devops_engineer",
  "deployment_engineer",
  "sre_engineer",
  "security_engineer",
  "memory_agent",
  "repo_scout",
  "human_liaison",
  "iteration",
];

const AGENT_ICONS: Record<string, string> = {
  orchestrator: "🧠",
  chief_orchestrator: "👑",
  planner: "📋",
  coder: "💻",
  frontend_engineer: "🎨",
  backend_engineer: "⚙️",
  database_engineer: "🗄️",
  integration_engineer: "🔗",
  qa_engineer: "🧪",
  code_reviewer: "👁️",
  debug_agent: "🐛",
  product_manager: "📊",
  architecture: "🏗️",
  market_research: "🔍",
  critic: "📝",
  devops_engineer: "🚢",
  deployment_engineer: "🚀",
  sre_engineer: "📡",
  security_engineer: "🔐",
  memory_agent: "💾",
  repo_scout: "🗺️",
  human_liaison: "🤝",
  iteration: "🔄",
};

// ── Types ─────────────────────────────────────────────────────────────────────

type AgentStatus = "idle" | "thinking" | "working" | "waiting" | "done" | "error";
type SwarmStatus = "idle" | "connecting" | "running" | "completed" | "error";

interface LogEntry {
  time: string;
  text: string;
  mine?: boolean;
}

interface AgentState {
  role: string;
  status: AgentStatus;
  currentTask: string;
  logs: LogEntry[];
}

interface SwarmPanelProps {
  /** The generated prompt from the notebook — fed as the swarm goal context. */
  notebookGoal?: string;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const STATUS_PILL: Record<AgentStatus, string> = {
  idle: "bg-secondary/10 text-secondary",
  thinking: "bg-accent/20 text-accent",
  working: "bg-success/20 text-success",
  waiting: "bg-yellow-500/20 text-yellow-400",
  done: "bg-success/10 text-success/60",
  error: "bg-danger/20 text-danger",
};

const STATUS_DOT: Record<AgentStatus, string> = {
  idle: "bg-secondary/50",
  thinking: "bg-accent animate-pulse",
  working: "bg-success animate-pulse",
  waiting: "bg-yellow-400",
  done: "bg-success/60",
  error: "bg-danger",
};

function nowTime() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function SwarmPanel({ notebookGoal }: SwarmPanelProps) {
  // ── Config state ────────────────────────────────────────────────────────────
  const [topology, setTopology] = useState("coding_swarm");
  const [agents, setAgents] = useState<string[]>([...TOPOLOGIES.coding_swarm.agents]);
  const [outputPath, setOutputPath] = useState("");
  const [extraInstructions, setExtraInstructions] = useState("");
  const [showAddAgent, setShowAddAgent] = useState(false);

  // ── Swarm runtime state ─────────────────────────────────────────────────────
  const [swarmStatus, setSwarmStatus] = useState<SwarmStatus>("idle");
  const [agentStates, setAgentStates] = useState<Record<string, AgentState>>({});
  const [globalLog, setGlobalLog] = useState<LogEntry[]>([]);
  const [traceId, setTraceId] = useState<string | null>(null);

  // ── Intervention state ──────────────────────────────────────────────────────
  const [expanded, setExpanded] = useState<string | null>(null);
  const [interventionAgent, setInterventionAgent] = useState<string | null>(null);
  const [interventionMsg, setInterventionMsg] = useState("");
  const [broadcastMsg, setBroadcastMsg] = useState("");
  const [showBroadcast, setShowBroadcast] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const globalLogRef = useRef<HTMLDivElement>(null);

  // ── Auto-scroll global log ───────────────────────────────────────────────────
  useEffect(() => {
    const el = globalLogRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [globalLog]);

  // ── Topology change resets agents to defaults ────────────────────────────────
  function handleTopologyChange(t: string) {
    setTopology(t);
    setAgents([...TOPOLOGIES[t].agents]);
  }

  function toggleAgent(role: string) {
    setAgents((prev) =>
      prev.includes(role) ? prev.filter((a) => a !== role) : [...prev, role]
    );
  }

  function addGlobalLog(text: string, mine = false) {
    setGlobalLog((prev) => [
      ...prev.slice(-199),
      { time: nowTime(), text, mine },
    ]);
  }

  // ── WebSocket ────────────────────────────────────────────────────────────────

  const handleSwarmEvent = useCallback((event: Record<string, unknown>) => {
    const role = event.role as string | undefined;
    const type = event.type as string;
    const content = (event.content as string) ?? "";
    const time = nowTime();

    if (type === "run_start") {
      setSwarmStatus("running");
      addGlobalLog(`Swarm started — trace: ${event.trace_id ?? "?"}`);
      if (event.trace_id) setTraceId(event.trace_id as string);
    } else if (type === "run_end") {
      setSwarmStatus("completed");
      addGlobalLog("Swarm completed successfully");
    } else if (type === "run_error") {
      setSwarmStatus("error");
      addGlobalLog(`Swarm error: ${content}`);
    } else if (role) {
      setAgentStates((prev) => {
        const current: AgentState = prev[role] ?? {
          role,
          status: "idle",
          currentTask: "Initializing…",
          logs: [],
        };

        let status: AgentStatus = current.status;
        let currentTask = current.currentTask;

        switch (type) {
          case "agent_start":
            status = "thinking";
            currentTask = content || "Starting…";
            break;
          case "agent_thinking":
            status = "thinking";
            currentTask = content || "Thinking…";
            break;
          case "tool_call":
            status = "working";
            currentTask = `Using tool: ${content}`;
            break;
          case "agent_message":
            status = "working";
            currentTask = content;
            break;
          case "agent_waiting":
            status = "waiting";
            currentTask = "Waiting for peer agents…";
            break;
          case "agent_done":
            status = "done";
            currentTask = content || "Task completed";
            break;
          case "agent_error":
            status = "error";
            currentTask = content || "An error occurred";
            break;
        }

        return {
          ...prev,
          [role]: {
            ...current,
            status,
            currentTask,
            logs: [
              ...current.logs.slice(-99),
              { time, text: content || type },
            ],
          },
        };
      });
    }
  }, []);

  function connectWS() {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    try {
      const ws = new WebSocket(SWARM_WS);
      ws.onopen = () => addGlobalLog("WebSocket connected to swarm runtime");
      ws.onmessage = (e) => {
        try {
          handleSwarmEvent(JSON.parse(e.data));
        } catch {
          /* ignore malformed frames */
        }
      };
      ws.onerror = () => addGlobalLog("WebSocket error — live updates unavailable");
      ws.onclose = () => {
        addGlobalLog("WebSocket disconnected");
      };
      wsRef.current = ws;
    } catch {
      addGlobalLog("Could not open WebSocket — check swarm runtime is running");
    }
  }

  useEffect(() => () => { wsRef.current?.close(); }, []);

  // ── Launch ───────────────────────────────────────────────────────────────────

  async function launchSwarm() {
    if (!outputPath.trim()) return;

    setSwarmStatus("connecting");
    setAgentStates({});
    setGlobalLog([]);
    setTraceId(null);

    // Seed agent cards so they appear immediately
    const initial: Record<string, AgentState> = {};
    for (const role of agents) {
      initial[role] = {
        role,
        status: "idle",
        currentTask: "Waiting to start…",
        logs: [],
      };
    }
    setAgentStates(initial);

    connectWS();

    const goalParts: string[] = [];
    if (notebookGoal) goalParts.push(`## Context from notebook\n${notebookGoal}`);
    if (extraInstructions.trim()) goalParts.push(`## Additional instructions\n${extraInstructions.trim()}`);
    goalParts.push(`## Output directory\n${outputPath.trim()}`);
    const goal = goalParts.join("\n\n");

    try {
      addGlobalLog(`Submitting goal to swarm runtime (topology: ${topology})…`);
      const res = await fetch(`${SWARM_HTTP}/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ goal, topology }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        addGlobalLog(`Launch failed: ${err.detail ?? res.statusText}`);
        setSwarmStatus("error");
        return;
      }

      const data = await res.json();
      if (data.trace_id) setTraceId(data.trace_id);
      setSwarmStatus("completed");
      addGlobalLog(`Run finished. Trace: ${data.trace_id ?? "—"}`);
    } catch (err) {
      // POST failed (runtime offline) — keep WS open if connected, show running UI
      addGlobalLog(
        `Swarm HTTP unreachable: ${err instanceof Error ? err.message : String(err)}. Watching WebSocket for events.`
      );
      setSwarmStatus("running");
    }
  }

  // ── Intervention ─────────────────────────────────────────────────────────────

  function sendToWS(payload: object) {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload));
      return true;
    }
    return false;
  }

  function sendIntervention() {
    if (!interventionAgent || !interventionMsg.trim()) return;
    const msg = interventionMsg.trim();
    const sent = sendToWS({ type: "intervention", target_agent: interventionAgent, message: msg });
    addGlobalLog(`${sent ? "Sent" : "Logged"} intervention → ${interventionAgent}: ${msg}`);
    setAgentStates((prev) => {
      const a = prev[interventionAgent];
      if (!a) return prev;
      return {
        ...prev,
        [interventionAgent]: {
          ...a,
          logs: [...a.logs, { time: nowTime(), text: msg, mine: true }],
        },
      };
    });
    setInterventionMsg("");
    setInterventionAgent(null);
  }

  function sendBroadcast() {
    if (!broadcastMsg.trim()) return;
    const msg = broadcastMsg.trim();
    sendToWS({ type: "broadcast_intervention", message: msg });
    addGlobalLog(`Broadcast to all agents: ${msg}`);
    setBroadcastMsg("");
    setShowBroadcast(false);
  }

  function stopAgent(role: string) {
    sendToWS({ type: "stop_agent", target_agent: role });
    addGlobalLog(`Stop signal sent to ${role}`);
    setAgentStates((prev) => ({
      ...prev,
      [role]: { ...prev[role], status: "done", currentTask: "Stopped by user" },
    }));
  }

  function stopAll() {
    sendToWS({ type: "stop_swarm" });
    addGlobalLog("Stop-all signal sent to swarm");
    setSwarmStatus("completed");
    setAgentStates((prev) => {
      const next = { ...prev };
      for (const role of Object.keys(next)) {
        if (next[role].status === "running" || next[role].status === "thinking" || next[role].status === "working") {
          next[role] = { ...next[role], status: "done", currentTask: "Stopped by user" };
        }
      }
      return next;
    });
  }

  // ── Derived ───────────────────────────────────────────────────────────────────

  const isLive = swarmStatus === "running";
  const hasMonitor = swarmStatus !== "idle" && swarmStatus !== "connecting";
  const availableToAdd = ALL_AGENTS.filter((a) => !agents.includes(a));

  // ── Render ────────────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col gap-6">

      {/* ── CONFIG PANEL (idle only) ────────────────────────────────────────── */}
      {swarmStatus === "idle" && (
        <div className="bg-card border border-border rounded-2xl p-6 flex flex-col gap-5">
          <div>
            <h2 className="font-semibold text-base">Launch Swarm</h2>
            <p className="text-secondary text-xs mt-1">
              Configure the build target and the agent team, then launch.
            </p>
          </div>

          {/* Output path */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-secondary">
              Output path <span className="text-danger">*</span>
            </label>
            <input
              value={outputPath}
              onChange={(e) => setOutputPath(e.target.value)}
              placeholder={
                typeof window !== "undefined" && navigator.userAgent.includes("Win")
                  ? "C:\\Users\\you\\projects\\my-app"
                  : "/Users/you/projects/my-app"
              }
              className="bg-elevated border border-border rounded-lg px-3 py-2.5 text-sm font-mono outline-none focus:border-accent transition-colors placeholder:text-secondary/40"
            />
            <p className="text-xs text-secondary/60">
              The directory where the swarm will create and modify files.
            </p>
          </div>

          {/* Topology + agents */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            {/* Topology selector */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-secondary">Topology</label>
              <select
                value={topology}
                onChange={(e) => handleTopologyChange(e.target.value)}
                className="bg-elevated border border-border rounded-lg px-3 py-2.5 text-sm outline-none focus:border-accent transition-colors"
              >
                {Object.entries(TOPOLOGIES).map(([key, t]) => (
                  <option key={key} value={key}>
                    {t.name}
                  </option>
                ))}
              </select>
              <p className="text-xs text-secondary/60 leading-relaxed">
                {TOPOLOGIES[topology].description}
              </p>
            </div>

            {/* Agent selector */}
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-secondary">
                  Agents{" "}
                  <span className="font-normal text-secondary/60">— click to toggle</span>
                </label>
                {availableToAdd.length > 0 && (
                  <div className="relative">
                    <button
                      onClick={() => setShowAddAgent((v) => !v)}
                      className="text-xs px-2 py-1 border border-dashed border-border-light hover:border-accent text-secondary hover:text-accent rounded-lg transition-colors"
                    >
                      + Add
                    </button>
                    {showAddAgent && (
                      <div className="absolute right-0 top-7 z-30 w-52 bg-card border border-border rounded-xl shadow-xl overflow-hidden max-h-60 overflow-y-auto animate-fade-in">
                        {availableToAdd.map((role) => (
                          <button
                            key={role}
                            onClick={() => { toggleAgent(role); setShowAddAgent(false); }}
                            className="w-full flex items-center gap-2 px-3 py-2 text-xs hover:bg-elevated text-secondary hover:text-primary transition-colors text-left"
                          >
                            <span>{AGENT_ICONS[role] ?? "🤖"}</span>
                            {role.replace(/_/g, " ")}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="flex flex-wrap gap-1.5 min-h-[32px]">
                {agents.map((role) => (
                  <button
                    key={role}
                    onClick={() => toggleAgent(role)}
                    title="Click to remove"
                    className="flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium border bg-accent/15 border-accent/35 text-accent hover:bg-danger/10 hover:border-danger/40 hover:text-danger transition-colors"
                  >
                    {AGENT_ICONS[role] ?? "🤖"} {role.replace(/_/g, " ")}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Extra instructions */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-secondary">
              Additional instructions{" "}
              <span className="font-normal text-secondary/60">(optional)</span>
            </label>
            <textarea
              rows={3}
              value={extraInstructions}
              onChange={(e) => setExtraInstructions(e.target.value)}
              placeholder="Any extra constraints, architecture decisions, or directions for the swarm beyond your notebook sources…"
              className="bg-elevated border border-border rounded-lg px-3 py-2.5 text-sm outline-none focus:border-accent transition-colors resize-none placeholder:text-secondary/40"
            />
          </div>

          {/* Context status */}
          {notebookGoal ? (
            <div className="flex items-start gap-2 text-xs text-success bg-success/10 border border-success/20 rounded-lg px-3 py-2.5">
              <span className="mt-0.5 shrink-0">✓</span>
              <span>Notebook prompt will be included as context for the swarm.</span>
            </div>
          ) : (
            <div className="flex items-start gap-2 text-xs text-secondary bg-elevated border border-border rounded-lg px-3 py-2.5">
              <span className="mt-0.5 shrink-0">💡</span>
              <span>
                Switch to the <strong className="text-primary">Prompt</strong> tab to generate context from
                your sources first — it gives the swarm richer requirements.
              </span>
            </div>
          )}

          <button
            onClick={launchSwarm}
            disabled={!outputPath.trim() || agents.length === 0}
            className="self-start flex items-center gap-2 px-6 py-2.5 bg-accent hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed rounded-lg text-sm font-semibold transition-colors shadow-lg shadow-accent/20"
          >
            🚀 Launch Swarm
          </button>
        </div>
      )}

      {/* ── CONNECTING ──────────────────────────────────────────────────────── */}
      {swarmStatus === "connecting" && (
        <div className="bg-card border border-border rounded-2xl p-6 flex items-center gap-4">
          <div className="w-5 h-5 border-2 border-accent border-t-transparent rounded-full animate-spin shrink-0" />
          <div>
            <p className="text-sm font-medium">Connecting to swarm runtime…</p>
            <p className="text-xs text-secondary mt-0.5">
              Establishing WebSocket · submitting goal to {SWARM_HTTP}
            </p>
          </div>
        </div>
      )}

      {/* ── MONITOR ─────────────────────────────────────────────────────────── */}
      {hasMonitor && (
        <div className="flex flex-col gap-4">

          {/* Status bar */}
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-3">
              <div
                className={`w-2 h-2 rounded-full ${
                  isLive
                    ? "bg-success animate-pulse"
                    : swarmStatus === "completed"
                    ? "bg-success"
                    : "bg-danger"
                }`}
              />
              <span className="text-sm font-semibold">
                {isLive
                  ? "Swarm running"
                  : swarmStatus === "completed"
                  ? "Swarm completed"
                  : "Swarm error"}
              </span>
              {traceId && (
                <span className="text-xs text-secondary font-mono">
                  trace: {traceId.slice(0, 8)}…
                </span>
              )}
            </div>

            <div className="flex items-center gap-2">
              {/* Broadcast */}
              {isLive && (
                <button
                  onClick={() => setShowBroadcast((v) => !v)}
                  className="flex items-center gap-1.5 text-xs px-3 py-1.5 border border-border hover:border-accent text-secondary hover:text-accent rounded-lg transition-colors"
                >
                  📢 Broadcast
                </button>
              )}
              {/* Stop all */}
              {isLive && (
                <button
                  onClick={stopAll}
                  className="flex items-center gap-1.5 text-xs px-3 py-1.5 border border-border hover:border-danger text-secondary hover:text-danger rounded-lg transition-colors"
                >
                  ⛔ Stop all
                </button>
              )}
              {/* Reset */}
              <button
                onClick={() => {
                  wsRef.current?.close();
                  setSwarmStatus("idle");
                  setAgentStates({});
                  setGlobalLog([]);
                  setTraceId(null);
                  setExpanded(null);
                }}
                className="text-xs px-3 py-1.5 border border-border hover:border-border-light text-secondary hover:text-primary rounded-lg transition-colors"
              >
                Reset
              </button>
            </div>
          </div>

          {/* Broadcast input */}
          {showBroadcast && (
            <div className="flex gap-2 animate-slide-up">
              <input
                autoFocus
                value={broadcastMsg}
                onChange={(e) => setBroadcastMsg(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendBroadcast()}
                placeholder="Broadcast a message or redirection to all active agents…"
                className="flex-1 bg-elevated border border-accent rounded-lg px-3 py-2 text-sm outline-none"
              />
              <button
                onClick={sendBroadcast}
                className="px-4 py-2 bg-accent hover:bg-accent-hover rounded-lg text-sm font-medium"
              >
                Send
              </button>
              <button
                onClick={() => { setShowBroadcast(false); setBroadcastMsg(""); }}
                className="px-3 py-2 border border-border rounded-lg text-sm text-secondary hover:text-primary"
              >
                Cancel
              </button>
            </div>
          )}

          {/* Agent cards */}
          <div className="flex flex-col gap-2">
            {Object.values(agentStates).length === 0 && (
              <div className="bg-card border border-border rounded-xl p-6 text-center text-secondary text-sm">
                Waiting for agents to come online…
              </div>
            )}

            {Object.values(agentStates).map((agent) => {
              const isExpanded = expanded === agent.role;
              const isInterveningThis = interventionAgent === agent.role;

              return (
                <div
                  key={agent.role}
                  className={`bg-card border rounded-xl transition-colors ${
                    isExpanded ? "border-accent/40" : "border-border hover:border-border-light"
                  }`}
                >
                  {/* Card header — click to expand */}
                  <button
                    onClick={() => setExpanded((e) => (e === agent.role ? null : agent.role))}
                    className="w-full flex items-center gap-3 px-4 py-3 text-left"
                  >
                    <span className="text-xl shrink-0">{AGENT_ICONS[agent.role] ?? "🤖"}</span>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold">
                          {agent.role.replace(/_/g, " ")}
                        </span>
                        <span
                          className={`inline-flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_PILL[agent.status]}`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${STATUS_DOT[agent.status]}`}
                          />
                          {agent.status}
                        </span>
                      </div>
                      <p className="text-xs text-secondary truncate mt-0.5">
                        {agent.currentTask}
                      </p>
                    </div>

                    <span className="text-secondary/50 text-xs shrink-0">
                      {isExpanded ? "▲" : "▼"}
                    </span>
                  </button>

                  {/* Expanded body */}
                  {isExpanded && (
                    <div className="border-t border-border px-4 pb-4 flex flex-col gap-3 animate-slide-up">
                      {/* Activity log */}
                      <div className="mt-3 bg-elevated rounded-lg px-3 py-2.5 max-h-44 overflow-y-auto space-y-1">
                        {agent.logs.length === 0 ? (
                          <p className="text-xs text-secondary/40 font-mono">No activity yet</p>
                        ) : (
                          agent.logs.map((l, i) => (
                            <p key={i} className="text-xs font-mono leading-relaxed">
                              <span className="text-secondary/40 select-none">{l.time} </span>
                              <span className={l.mine ? "text-accent" : "text-secondary/80"}>
                                {l.mine ? "[you] " : ""}{l.text}
                              </span>
                            </p>
                          ))
                        )}
                      </div>

                      {/* Intervention controls */}
                      {isLive && (
                        <div className="flex flex-col gap-2">
                          {isInterveningThis ? (
                            <div className="flex gap-2 animate-slide-up">
                              <input
                                autoFocus
                                value={interventionMsg}
                                onChange={(e) => setInterventionMsg(e.target.value)}
                                onKeyDown={(e) => e.key === "Enter" && sendIntervention()}
                                placeholder={`Tell ${agent.role.replace(/_/g, " ")} what to do instead…`}
                                className="flex-1 bg-elevated border border-accent rounded-lg px-3 py-2 text-xs outline-none"
                              />
                              <button
                                onClick={sendIntervention}
                                className="px-3 py-2 bg-accent hover:bg-accent-hover rounded-lg text-xs font-medium"
                              >
                                Send
                              </button>
                              <button
                                onClick={() => { setInterventionAgent(null); setInterventionMsg(""); }}
                                className="px-3 py-2 border border-border rounded-lg text-xs text-secondary hover:text-primary"
                              >
                                Cancel
                              </button>
                            </div>
                          ) : (
                            <div className="flex gap-2">
                              <button
                                onClick={() => setInterventionAgent(agent.role)}
                                className="flex items-center gap-1.5 px-3 py-1.5 border border-border hover:border-accent text-secondary hover:text-accent rounded-lg text-xs transition-colors"
                              >
                                💬 Intervene
                              </button>
                              <button
                                onClick={() => stopAgent(agent.role)}
                                className="flex items-center gap-1.5 px-3 py-1.5 border border-border hover:border-danger text-secondary hover:text-danger rounded-lg text-xs transition-colors"
                              >
                                ⛔ Stop agent
                              </button>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Global swarm log */}
          {globalLog.length > 0 && (
            <div className="bg-card border border-border rounded-xl p-4">
              <p className="text-xs font-semibold text-secondary uppercase tracking-widest mb-2">
                Swarm log
              </p>
              <div
                ref={globalLogRef}
                className="max-h-36 overflow-y-auto space-y-0.5"
              >
                {globalLog.map((l, i) => (
                  <p key={i} className="text-xs font-mono text-secondary/70 leading-relaxed">
                    <span className="text-secondary/40 select-none">{l.time} </span>
                    <span className={l.mine ? "text-accent" : ""}>{l.text}</span>
                  </p>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
