import React, { useEffect, useRef } from 'react';
import { AlertOctagon, AlertTriangle, Info } from 'lucide-react';

const SEVERITY = {
  CRITICAL: { color: '#ff453a', bg: 'rgba(255,69,58,0.06)', Icon: AlertOctagon },
  ERROR:    { color: '#ff9f0a', bg: 'rgba(255,159,10,0.06)', Icon: AlertTriangle },
  WARNING:  { color: '#ffd60a', bg: 'rgba(255,214,10,0.05)', Icon: AlertTriangle },
  INFO:     { color: 'rgba(255,255,255,0.32)', bg: 'rgba(255,255,255,0.02)', Icon: Info },
};

/**
 * Timeline — chronological severity-coded event log
 */
export default function Timeline({ events = [] }) {
  const endRef = useRef(null);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [events]);

  return (
    <div className="glass h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
        <h2 className="text-[13px] font-semibold text-label-primary tracking-tight">Timeline</h2>
        <span className="ml-auto text-[11px] text-label-tertiary font-mono">{events.length}</span>
      </div>

      {/* Events */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1.5">
        {events.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <p className="text-[13px] text-label-tertiary">Waiting for events…</p>
          </div>
        ) : (
          events.map((evt, i) => {
            const sev = SEVERITY[evt.severity] || SEVERITY.INFO;
            const { Icon } = sev;
            return (
              <div
                key={i}
                className="animate-fade-up rounded-xl border-l-2 px-3 py-2"
                style={{
                  animationDelay: `${Math.min(i * 0.03, 0.25)}s`,
                  background: sev.bg,
                  borderColor: sev.color,
                }}
              >
                <div className="flex items-center gap-2 mb-0.5">
                  <Icon size={12} style={{ color: sev.color }} className="flex-none" />
                  <span className="text-[11px] font-semibold uppercase tracking-wide" style={{ color: sev.color }}>
                    {evt.severity || 'INFO'}
                  </span>
                  <span className="text-[11px] font-mono text-label-tertiary">{evt.ts}</span>
                </div>
                <p className="text-[12px] leading-snug text-label-secondary break-words pl-5">
                  {evt.message}
                </p>
              </div>
            );
          })
        )}
        <div ref={endRef} />
      </div>
    </div>
  );
}
