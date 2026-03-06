import React, { useState, useEffect, useRef } from 'react';
import { ShieldAlert, CheckCircle2, Clock } from 'lucide-react';

/**
 * SLA Countdown — Apple-dark aesthetic
 * Counts down locally once a target is received from WS.
 * Green → Amber (5 min) → Red (2 min) → Pulsing Red (30 s)
 */
export default function SLACountdown({ seconds: initialSeconds, resolved }) {
  const [remaining, setRemaining] = useState(null);
  const intervalRef = useRef(null);

  // Sync from parent whenever a new SLA value arrives
  useEffect(() => {
    if (initialSeconds == null) return;
    setRemaining(initialSeconds);
  }, [initialSeconds]);

  // Local 1-second tick
  useEffect(() => {
    clearInterval(intervalRef.current);
    if (remaining == null || remaining <= 0 || resolved) return;
    intervalRef.current = setInterval(() => {
      setRemaining(p => (p != null && p > 0 ? p - 1 : 0));
    }, 1000);
    return () => clearInterval(intervalRef.current);
  }, [remaining != null, resolved]); // eslint-disable-line react-hooks/exhaustive-deps

  const fmt = () => {
    if (resolved)        return 'RESOLVED';
    if (remaining == null) return '--:--';
    const m = Math.floor(remaining / 60);
    const s = remaining % 60;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  };

  const color = () => {
    if (resolved)              return '#30d158';
    if (remaining == null)     return 'rgba(255,255,255,0.25)';
    if (remaining < 30)        return '#ff453a';
    if (remaining < 120)       return '#ff453a';
    if (remaining < 300)       return '#ffd60a';
    return '#30d158';
  };

  const critical = remaining != null && remaining < 120 && !resolved;
  const flash    = remaining != null && remaining < 30  && !resolved;

  return (
    <div className="glass h-full flex flex-col items-center justify-center p-6 relative overflow-hidden">
      {/* Danger glow */}
      {critical && (
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background: `radial-gradient(ellipse at 50% 60%, ${color()}15 0%, transparent 70%)`,
          }}
        />
      )}

      {resolved ? (
        <div className="animate-fade-up text-center z-10 space-y-2">
          <CheckCircle2 size={36} className="mx-auto text-accent-green" />
          <h2 className="text-xl font-semibold text-accent-green tracking-tight">Incident Resolved</h2>
          <p className="text-[13px] text-label-tertiary">All systems nominal</p>
        </div>
      ) : (
        <div className="z-10 flex flex-col items-center gap-4">
          {critical ? (
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-accent-red/10">
              <ShieldAlert size={14} className="text-accent-red" />
              <span className="text-[12px] font-semibold tracking-wide text-accent-red uppercase">
                SLA Breach Imminent
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Clock size={16} style={{ color: color() }} />
              <span className="text-[12px] text-label-tertiary uppercase tracking-widest font-medium">
                Time to SLA
              </span>
            </div>
          )}

          <div
            className={`font-mono font-bold tracking-tighter leading-none ${
              flash ? 'animate-countdown-pulse' : ''
            }`}
            style={{
              color: color(),
              fontSize: critical ? '5rem' : '4rem',
              transition: 'color 0.6s ease, font-size 0.4s ease',
            }}
          >
            {fmt()}
          </div>

          {critical && (
            <p className="text-[13px] text-label-secondary text-center">
              Payments service at critical latency
            </p>
          )}
        </div>
      )}
    </div>
  );
}
