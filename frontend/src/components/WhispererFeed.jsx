import React, { useEffect, useRef } from 'react';
import { Activity, Mic } from 'lucide-react';

/**
 * Whisperer Feed — real-time ATOM insights
 */
export default function WhispererFeed({ messages = [] }) {
  const endRef = useRef(null);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  return (
    <div className="glass h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
        <Activity size={14} className="text-accent-green" />
        <h2 className="text-[13px] font-semibold text-label-primary tracking-tight">ATOM Feed</h2>
        <span className="ml-auto text-[11px] text-label-tertiary font-mono">{messages.length}</span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center gap-2 text-label-tertiary">
            <Mic size={22} strokeWidth={1.4} className="opacity-40" />
            <p className="text-[13px]">ATOM is listening…</p>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div
              key={i}
              className="animate-fade-up rounded-xl px-3.5 py-2.5 border-l-2"
              style={{
                animationDelay: `${Math.min(i * 0.04, 0.3)}s`,
                background: msg.type === 'interrupt'
                  ? 'rgba(255,69,58,0.06)'
                  : 'rgba(48,209,88,0.04)',
                borderColor: msg.type === 'interrupt' ? '#ff453a' : '#30d158',
              }}
            >
              <div className="flex items-center gap-1.5 mb-1">
                <span className="text-[11px] font-mono text-label-tertiary">{msg.ts}</span>
                {msg.type === 'interrupt' && (
                  <span className="text-[10px] font-bold text-accent-red tracking-wider uppercase">
                    Interrupting
                  </span>
                )}
              </div>
              <p className={`text-[13px] leading-relaxed ${
                msg.type === 'interrupt' ? 'text-accent-red' : 'text-label-primary'
              }`}>
                {msg.text}
              </p>
            </div>
          ))
        )}
        <div ref={endRef} />
      </div>
    </div>
  );
}
