import { useState, useEffect, useRef } from "react";

const STYLES = `
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: #0A0A0F;
    color: #E8E8F0;
    font-family: system-ui, -apple-system, sans-serif;
    min-height: 100vh;
  }

  .atom-root {
    max-width: 1280px;
    margin: 0 auto;
    padding: 24px 16px;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  /* TOP BAR */
  .topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border: 0.5px solid #1E1E2E;
    border-radius: 8px;
    padding: 14px 20px;
  }
  .topbar-wordmark {
    font-family: 'Space Mono', monospace;
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 4px;
    color: #E8E8F0;
  }
  .topbar-subtitle {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    letter-spacing: 2px;
    color: #888780;
    text-transform: uppercase;
  }
  .topbar-session {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    color: #444455;
    letter-spacing: 1px;
  }
  .topbar-session span {
    color: #E8E8F0;
  }

  /* INPUT PANEL */
  .input-panel {
    border: 0.5px solid #1E1E2E;
    border-radius: 8px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .input-label {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    letter-spacing: 2px;
    color: #444455;
    text-transform: uppercase;
  }
  .code-textarea {
    width: 100%;
    background: #07070C;
    border: 0.5px solid #1E1E2E;
    border-radius: 6px;
    color: #E8E8F0;
    font-family: 'Space Mono', monospace;
    font-size: 13px;
    line-height: 1.6;
    padding: 12px;
    resize: vertical;
    outline: none;
    transition: border-color 0.15s;
  }
  .code-textarea:focus {
    border-color: #2E2E4E;
  }
  .code-textarea::placeholder {
    color: #333344;
  }
  .run-btn {
    align-self: flex-start;
    background: #E8E8F0;
    color: #0A0A0F;
    border: none;
    border-radius: 6px;
    padding: 10px 24px;
    font-family: 'Space Mono', monospace;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 2px;
    cursor: pointer;
    transition: opacity 0.15s;
  }
  .run-btn:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }
  .run-btn:not(:disabled):hover {
    opacity: 0.85;
  }

  /* STATUS BAR */
  .status-bar {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    color: #888780;
    letter-spacing: 1px;
    padding: 8px 0;
  }
  .status-bar .dot {
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    margin-right: 8px;
    background: #888780;
  }
  .status-bar.running .dot { background: #F0C040; animation: blink 1s infinite; }
  .status-bar.done .dot { background: #1D9E75; }
  .status-bar.error .dot { background: #D85A30; }

  @keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.2; }
  }

  /* ARENA */
  .arena {
    display: grid;
    grid-template-columns: 1fr 220px 1fr;
    gap: 12px;
    align-items: start;
  }

  /* AGENT PANEL */
  .agent-panel {
    border: 0.5px solid #1E1E2E;
    border-radius: 8px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    min-height: 320px;
  }
  .agent-label {
    font-family: 'Space Mono', monospace;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 3px;
  }
  .agent-label.atlas { color: #185FA5; }
  .agent-label.riot  { color: #D85A30; }

  .conf-bar-track {
    width: 100%;
    height: 4px;
    background: #1E1E2E;
    border-radius: 2px;
    overflow: hidden;
  }
  .conf-bar-fill {
    height: 100%;
    border-radius: 2px;
    transition: width 0.4s ease;
  }
  .conf-bar-fill.atlas { background: #185FA5; }
  .conf-bar-fill.riot  { background: #D85A30; }
  .conf-pct {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    color: #888780;
  }

  .round-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 400px;
    overflow-y: auto;
  }
  .round-list::-webkit-scrollbar { width: 2px; }
  .round-list::-webkit-scrollbar-thumb { background: #1E1E2E; }

  .round-item {
    border: 0.5px solid #1E1E2E;
    border-radius: 6px;
    padding: 8px 10px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .round-item-header {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .round-num {
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    color: #444455;
    letter-spacing: 1px;
  }
  .hit-badge {
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    font-weight: 700;
    padding: 1px 5px;
    border-radius: 3px;
    letter-spacing: 1px;
  }
  .hit-badge.HIT     { background: #0D2E22; color: #1D9E75; border: 0.5px solid #1D9E75; }
  .hit-badge.BLOCK   { background: #2E140D; color: #D85A30; border: 0.5px solid #D85A30; }
  .hit-badge.DEFLECT { background: #1A1A1A; color: #888780; border: 0.5px solid #444440; }
  .round-claim {
    font-size: 12px;
    color: #BBBBC8;
    line-height: 1.45;
  }
  .evidence-tag {
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    color: #444455;
    letter-spacing: 1px;
  }

  /* ORBITAL */
  .orbital-panel {
    border: 0.5px solid #1E1E2E;
    border-radius: 8px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
  }
  .orbital-label {
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    letter-spacing: 2px;
    color: #444455;
    text-transform: uppercase;
  }
  .orbital-svg-wrap {
    position: relative;
    width: 180px;
    height: 180px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .orbital-svg { overflow: visible; }

  .orbit-dot {
    position: absolute;
    top: 50%;
    left: 50%;
    margin-top: -5px;
    margin-left: -5px;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    transform-origin: 5px 5px;
  }
  .orbit-dot.atlas-dot {
    background: #185FA5;
    animation: orbitCW 8s linear infinite;
  }
  .orbit-dot.riot-dot {
    background: #D85A30;
    animation: orbitCCW 6s linear infinite;
  }

  @keyframes orbitCW {
    from { transform: rotate(0deg) translateX(70px) rotate(0deg); }
    to   { transform: rotate(360deg) translateX(70px) rotate(-360deg); }
  }
  @keyframes orbitCCW {
    from { transform: rotate(0deg) translateX(50px) rotate(0deg); }
    to   { transform: rotate(-360deg) translateX(50px) rotate(360deg); }
  }

  .orbital-round {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    color: #444455;
    letter-spacing: 1px;
  }
  .orbital-round span {
    color: #E8E8F0;
  }

  /* FIX PANEL */
  .fix-panel {
    border: 0.5px solid #1E1E2E;
    border-radius: 8px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  .winner-banner {
    font-family: 'Space Mono', monospace;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 4px;
    padding: 10px 16px;
    border-radius: 6px;
    border: 0.5px solid;
  }
  .winner-banner.ATLAS { color: #185FA5; border-color: #185FA5; background: #05101A; }
  .winner-banner.RIOT  { color: #D85A30; border-color: #D85A30; background: #1A0804; }

  .fix-explanation {
    font-size: 13px;
    color: #BBBBC8;
    line-height: 1.6;
  }

  .fix-conf {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    color: #888780;
  }

  .diff-label {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    letter-spacing: 2px;
    color: #444455;
    text-transform: uppercase;
  }
  .diff-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }
  .diff-col-label {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    color: #444455;
    letter-spacing: 1px;
    margin-bottom: 6px;
  }
  .diff-row {
    display: flex;
    gap: 6px;
    align-items: flex-start;
    padding: 3px 0;
    border-bottom: 0.5px solid #0E0E18;
  }
  .diff-line-num {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    color: #333344;
    min-width: 24px;
    text-align: right;
    flex-shrink: 0;
  }
  .diff-line-content {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    line-height: 1.5;
    word-break: break-all;
  }
  .diff-line-content.original { color: #D85A30; }
  .diff-line-content.fixed    { color: #1D9E75; }

  .fixed-code-block {
    background: #07070C;
    border: 0.5px solid #1E1E2E;
    border-radius: 6px;
    padding: 14px;
    font-family: 'Space Mono', monospace;
    font-size: 12px;
    color: #E8E8F0;
    white-space: pre;
    overflow-x: auto;
    line-height: 1.6;
  }

  /* ERROR */
  .error-msg {
    font-family: 'Space Mono', monospace;
    font-size: 12px;
    color: #D85A30;
    border: 0.5px solid #D85A30;
    border-radius: 6px;
    padding: 10px 14px;
  }
`;

function generateSessionId() {
  return Math.floor(Math.random() * 0xFFFF).toString(16).padStart(4, "0").toUpperCase();
}

function HitBadge({ type }) {
  return <span className={`hit-badge ${type}`}>{type}</span>;
}

function AgentPanel({ agent, agentKey, rounds }) {
  const isAtlas = agentKey === "ATLAS";
  const colorClass = isAtlas ? "atlas" : "riot";
  const pct = Math.round((agent.confidence ?? 0.5) * 100);

  return (
    <div className="agent-panel">
      <div className={`agent-label ${colorClass}`}>{agentKey}</div>
      <div>
        <div className="conf-bar-track">
          <div
            className={`conf-bar-fill ${colorClass}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <div className="conf-pct" style={{ marginTop: 4 }}>{pct}% confidence</div>
      </div>
      <div className="round-list">
        {rounds.map((r, i) => {
          const side = isAtlas ? r.atlas : r.riot;
          if (!side) return null;
          return (
            <div className="round-item" key={i}>
              <div className="round-item-header">
                <span className="round-num">R{r.round_number ?? i + 1}</span>
                <HitBadge type={side.hit_type ?? "HIT"} />
                <span className="evidence-tag">{side.evidence_type}</span>
              </div>
              <div className="round-claim">{side.claim}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function OrbitalPanel({ currentRound, totalRounds }) {
  return (
    <div className="orbital-panel">
      <div className="orbital-label">ARENA</div>
      <div className="orbital-svg-wrap">
        {/* Outer dashed orbit */}
        <svg
          className="orbital-svg"
          width="180"
          height="180"
          style={{ position: "absolute", top: 0, left: 0 }}
        >
          <circle cx="90" cy="90" r="75" fill="none" stroke="#1E1E2E" strokeWidth="1" strokeDasharray="4 4" />
          <circle cx="90" cy="90" r="55" fill="none" stroke="#1A1A28" strokeWidth="1" />
          <circle cx="90" cy="90" r="30" fill="#0A0A0F" stroke="#1E1E2E" strokeWidth="0.5" />
          <text x="90" y="86" textAnchor="middle" fontFamily="'Space Mono', monospace" fontSize="7" fill="#444455" letterSpacing="1">BUG</text>
          <text x="90" y="97" textAnchor="middle" fontFamily="'Space Mono', monospace" fontSize="7" fill="#444455" letterSpacing="1">CORE</text>
        </svg>

        {/* Orbiting dots via CSS */}
        <div className="orbit-dot atlas-dot" />
        <div className="orbit-dot riot-dot" />
      </div>
      <div className="orbital-round">
        ROUND <span>{currentRound}</span>
        {totalRounds ? ` / ${totalRounds}` : ""}
      </div>
    </div>
  );
}

function DiffView({ diff }) {
  if (!diff || diff.length === 0) return null;
  return (
    <div>
      <div className="diff-label" style={{ marginBottom: 10 }}>Diff</div>
      <div className="diff-grid">
        <div>
          <div className="diff-col-label">ORIGINAL</div>
          {diff.map((d, i) => (
            <div className="diff-row" key={i}>
              <span className="diff-line-num">{d.line}</span>
              <span className="diff-line-content original">{d.original}</span>
            </div>
          ))}
        </div>
        <div>
          <div className="diff-col-label">FIXED</div>
          {diff.map((d, i) => (
            <div className="diff-row" key={i}>
              <span className="diff-line-num">{d.line}</span>
              <span className="diff-line-content fixed">{d.fixed}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function FixPanel({ winner, fix }) {
  if (!fix) return null;
  const conf = Math.round((fix.confidence ?? 0) * 100);
  return (
    <div className="fix-panel">
      <div className={`winner-banner ${winner}`}>WINNER: {winner}</div>
      <p className="fix-explanation">{fix.explanation}</p>
      <div className="fix-conf">Fix confidence: {conf}%</div>
      <DiffView diff={fix.diff} />
      <div>
        <div className="diff-label" style={{ marginBottom: 8 }}>Fixed Code</div>
        <pre className="fixed-code-block">{fix.fixed_code}</pre>
      </div>
    </div>
  );
}

export default function ATOMApp() {
  const [sessionId] = useState(() => generateSessionId());
  const [code, setCode] = useState("");
  const [status, setStatus] = useState("idle");
  const [rounds, setRounds] = useState([]);
  const [scores, setScores] = useState({ ATLAS: 0.5, RIOT: 0.5 });
  const [winner, setWinner] = useState("");
  const [fix, setFix] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");

  const currentRound = rounds.length;

  async function runDebate() {
    if (!code.trim()) return;
    setStatus("running");
    setRounds([]);
    setScores({ ATLAS: 0.5, RIOT: 0.5 });
    setWinner("");
    setFix(null);
    setErrorMsg("");

    try {
      const res = await fetch("http://localhost:8000/api/debate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, max_rounds: 5 }),
      });

      if (!res.ok) {
        throw new Error(`Server error: ${res.status}`);
      }

      const data = await res.json();
      setRounds(data.rounds ?? []);
      setScores(data.final_confidence ?? { ATLAS: 0.5, RIOT: 0.5 });
      setWinner(data.winner ?? "");
      setFix(data.fix ?? null);
      setStatus("done");
    } catch (err) {
      setErrorMsg(err.message ?? "Unknown error");
      setStatus("error");
    }
  }

  const atlasConf = { confidence: scores.ATLAS };
  const riotConf  = { confidence: scores.RIOT };

  const statusLabels = {
    idle:    "AWAITING INPUT",
    running: "DEBATE IN PROGRESS",
    done:    "DEBATE COMPLETE",
    error:   "ERROR",
  };

  return (
    <>
      <style>{STYLES}</style>
      <div className="atom-root">

        {/* TOP BAR */}
        <div className="topbar">
          <div className="topbar-wordmark">ATOM</div>
          <div className="topbar-subtitle">Adversarial Theory Opposition Mechanism</div>
          <div className="topbar-session">SESSION <span>{sessionId}</span></div>
        </div>

        {/* INPUT PANEL */}
        <div className="input-panel">
          <div className="input-label">Code Input</div>
          <textarea
            className="code-textarea"
            rows={10}
            placeholder="Paste buggy code here..."
            value={code}
            onChange={e => setCode(e.target.value)}
            spellCheck={false}
          />
          <button
            className="run-btn"
            onClick={runDebate}
            disabled={status === "running"}
          >
            RUN ATOM
          </button>
        </div>

        {/* STATUS */}
        <div className={`status-bar ${status}`}>
          <span className="dot" />
          {statusLabels[status]}
        </div>

        {/* ERROR */}
        {status === "error" && (
          <div className="error-msg">ERROR: {errorMsg}</div>
        )}

        {/* ARENA */}
        {status !== "idle" && (
          <div className="arena">
            <AgentPanel agent={atlasConf} agentKey="ATLAS" rounds={rounds} />
            <OrbitalPanel currentRound={currentRound} totalRounds={5} />
            <AgentPanel agent={riotConf}  agentKey="RIOT"  rounds={rounds} />
          </div>
        )}

        {/* FIX PANEL */}
        {status === "done" && winner && (
          <FixPanel winner={winner} fix={fix} />
        )}

      </div>
    </>
  );
}
