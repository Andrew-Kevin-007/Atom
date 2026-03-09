import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Play, Square, Activity } from 'lucide-react';
import SLACountdown from './components/SLACountdown';
import WhispererFeed from './components/WhispererFeed';
import Timeline from './components/Timeline';
import Postmortem from './components/Postmortem';

const API = 'https://atom-backend-803244244025.asia-south1.run.app';
const WS  = 'wss://atom-backend-803244244025.asia-south1.run.app/ws';

function App() {
  const [incident, setIncident]       = useState(null);
  const [messages, setMessages]       = useState([]);
  const [events, setEvents]           = useState([]);
  const [isLoading, setIsLoading]     = useState(false);
  const [status, setStatus]           = useState('idle'); // idle | active | resolved
  const [slaSeconds, setSlaSeconds]   = useState(null);
  const [postmortem, setPostmortem]   = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);

  /* ── WebSocket ─────────────────────────────────────────────── */
  const handleWsMessage = useCallback((data) => {
    console.log('[WS] Received message:', data.type, data);
    const ts = new Date().toLocaleTimeString('en-US', { hour12: false });
    
    switch (data.type) {
      case 'incident_started':
        console.log('[WS] Incident started:', data.incident_id);
        setIncident({ id: data.incident_id, name: data.name, status: 'active' });
        setStatus('active');
        setMessages([]);
        setEvents([]);
        setSlaSeconds(null);
        setPostmortem(null);
        break;
        
      case 'atom_response':
        console.log('[WS] ATOM response received:', data.text);
        setMessages(p => [...p, { type: 'atom', text: data.text, ts }]);
        break;
        
      case 'log_event':
        console.log('[WS] Log event:', data.severity, data.message);
        setEvents(p => [...p, {
          message: data.message,
          severity: data.severity,
          ts,
          source: 'LOGS',
        }]);
        break;
        
      case 'sla_update':
        console.log('[WS] SLA update:', data.sla_seconds_remaining);
        setSlaSeconds(data.sla_seconds_remaining);
        break;
        
      case 'postmortem_update':
        console.log('[WS] Postmortem update received');
        setPostmortem(data.content);
        break;
        
      case 'incident_resolved':
        console.log('[WS] Incident resolved');
        setStatus('resolved');
        setIncident(p => p ? { ...p, status: 'resolved' } : null);
        break;
        
      case 'incident_error':
        console.error('[WS] Incident error:', data.error);
        setStatus('idle');
        setIncident(null);
        break;

      case 'ping':
        break;
        
      default:
        console.log('[WS] Unknown message type:', data.type);
        break;
    }
  }, []);

  useEffect(() => {
    let alive = true;
    const connect = () => {
      if (!alive) return;
      console.log('[WS] Attempting connection to', WS);
      const ws = new WebSocket(WS);
      
      ws.onopen = () => {
        console.log('[WS] Connection established');
        setWsConnected(true);
      };
      
      ws.onmessage = (e) => {
        console.log('[WS] Raw message received:', e.data);
        try {
          const data = JSON.parse(e.data);
          handleWsMessage(data);
        } catch (err) {
          console.error('[WS] Failed to parse message:', err);
        }
      };
      
      ws.onerror = (err) => {
        console.error('[WS] WebSocket error:', err);
        setWsConnected(false);
      };
      
      ws.onclose = () => {
        console.log('[WS] Connection closed, reconnecting in 3s...');
        setWsConnected(false);
        if (alive) setTimeout(connect, 3000);
      };
      
      wsRef.current = ws;
    };
    
    connect();
    return () => {
      console.log('[WS] Cleanup: closing connection');
      alive = false;
      wsRef.current?.close();
    };
  }, [handleWsMessage]);

  /* ── Actions ───────────────────────────────────────────────── */
  const startIncident = async () => {
    setIsLoading(true);
    try {
      await fetch(`${API}/incident/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Production Incident', incident_type: 'simulated' }),
      });
    } catch { alert('Backend unreachable — is uvicorn running?'); }
    finally { setIsLoading(false); }
  };

  const stopIncident = async () => {
    if (!incident) return;
    try { await fetch(`${API}/incident/${incident.id}/stop`, { method: 'POST' }); }
    catch { /* ignore */ }
    setIncident(null); setStatus('idle'); setMessages([]); setEvents([]); setSlaSeconds(null);
  };

  /* ── Render ────────────────────────────────────────────────── */
  return (
    <div className="h-screen flex flex-col bg-surface-0 overflow-hidden select-none">

      {/* ▸ Top Bar */}
      <header className="flex-none flex items-center justify-between px-6 h-14 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-8 h-8">
            <Activity size={20} className="text-accent-green" />
            {status === 'active' && (
              <span className="absolute inset-0 rounded-full bg-accent-green/20 animate-breathe" />
            )}
          </div>
          <div className="leading-tight">
            <h1 className="text-[15px] font-semibold tracking-tight text-label-primary">ATOM</h1>
            <p className="text-[11px] text-label-tertiary tracking-wide">Autonomous Threat & Operations Monitor</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Status pill */}
          {incident && (
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-surface-2">
              <span className={`w-1.5 h-1.5 rounded-full ${
                status === 'resolved' ? 'bg-accent-green' : 'bg-accent-red animate-pulse'
              }`} />
              <span className="text-xs font-mono text-label-secondary">{incident.id}</span>
            </div>
          )}

          {/* WS indicator */}
          <span className={`w-1.5 h-1.5 rounded-full ${wsConnected ? 'bg-accent-green' : 'bg-label-tertiary'}`}
            title={wsConnected ? 'Connected' : 'Disconnected'} />

          {/* CTA */}
          {status === 'idle' ? (
            <button
              onClick={startIncident}
              disabled={isLoading}
              className="flex items-center gap-2 h-8 px-4 rounded-full text-[13px] font-medium
                         bg-accent-green text-black hover:brightness-110 active:scale-[0.97]
                         disabled:opacity-40 disabled:pointer-events-none"
            >
              <Play size={14} />
              {isLoading ? 'Starting…' : 'Start Incident'}
            </button>
          ) : (
            <button
              onClick={stopIncident}
              className="flex items-center gap-2 h-8 px-4 rounded-full text-[13px] font-medium
                         bg-accent-red/90 text-white hover:bg-accent-red active:scale-[0.97]"
            >
              <Square size={12} />
              Stop
            </button>
          )}
        </div>
      </header>

      {/* ▸ Body */}
      {status === 'idle' ? (
        /* ── Hero / Idle State ──────────────────────────────────── */
        <main className="flex-1 flex flex-col items-center justify-center gap-8 px-6">
          <div className="relative">
            <Activity size={52} strokeWidth={1.4} className="text-accent-green/80" />
            <span className="absolute inset-0 rounded-full bg-accent-green/10 animate-breathe" />
          </div>

          <div className="text-center max-w-md space-y-3">
            <h2 className="text-[28px] font-bold tracking-tight text-label-primary">
              Ready to Monitor
            </h2>
            <p className="text-[15px] leading-relaxed text-label-secondary">
              ATOM is a real-time incident intelligence agent. Start a simulated incident
              with voice, screen, and log monitoring powered by Gemini.
            </p>
          </div>

          <div className="glass p-6 max-w-lg w-full space-y-4">
            <h3 className="text-[13px] font-semibold text-label-secondary uppercase tracking-widest">
              How it works
            </h3>
            <ul className="space-y-2.5 text-[14px] text-label-secondary leading-snug">
              {[
                'Monitors microphone, screen & production logs simultaneously',
                'Detects correlation between errors and system changes',
                'Proactively alerts when SLA breach is imminent',
                'Suggests root cause and resolution in real time',
                'Auto-generates a complete postmortem',
              ].map((t, i) => (
                <li key={i} className="flex gap-2.5 items-start">
                  <span className="mt-1.5 w-1 h-1 rounded-full bg-accent-green flex-none" />
                  {t}
                </li>
              ))}
            </ul>
          </div>

          <button
            onClick={startIncident}
            disabled={isLoading}
            className="h-11 px-8 rounded-full text-[15px] font-semibold
                       bg-accent-green text-black hover:brightness-110 active:scale-[0.97]
                       disabled:opacity-40 disabled:pointer-events-none"
          >
            {isLoading ? 'Starting…' : 'Start Demo Incident'}
          </button>
        </main>
      ) : (
        /* ── War Room ──────────────────────────────────────────── */
        <main className="flex-1 flex min-h-0 overflow-hidden">
          {/* Left — Feed & Timeline */}
          <div className="w-[42%] flex flex-col gap-3 p-3 min-h-0 border-r border-border">
            <div className="flex-1 min-h-0"><WhispererFeed messages={messages} /></div>
            <div className="flex-1 min-h-0"><Timeline events={events} /></div>
          </div>
          {/* Right — SLA & Postmortem */}
          <div className="flex-1 flex flex-col gap-3 p-3 min-h-0">
            <div className="h-[38%] min-h-0"><SLACountdown seconds={slaSeconds} resolved={status === 'resolved'} /></div>
            <div className="flex-1 min-h-0"><Postmortem incident={incident} postmortem={postmortem} /></div>
          </div>
        </main>
      )}
    </div>
  );
}

export default App;
