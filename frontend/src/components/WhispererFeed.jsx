import React, { useEffect, useRef } from 'react';
import { Zap, Mic } from 'lucide-react';

/**
 * WhispererFeed Component
 * Real-time feed of ATOM's insights and system messages
 * Slides in with animation, shows "ATOM is listening" when quiet
 */
export function WhispererFeed({ messages = [] }) {
  const feedEndRef = useRef(null);

  // Auto-scroll to latest message
  useEffect(() => {
    feedEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="h-full bg-card rounded-lg border border-gray-700 overflow-hidden flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-700 bg-opacity-50">
        <h2 className="text-lg font-bold flex items-center gap-2">
          <Zap size={20} color="#00ff88" />
          <span>ATOM Feed</span>
        </h2>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-500">
            <Mic size={32} className="mb-2 opacity-50" />
            <p className="text-sm">ATOM is listening...</p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
              className="animate-slide-in border-l-2 border-green-500 pl-3 py-2 text-sm"
              style={{
                animationDelay: `${idx * 0.05}s`,
              }}
            >
              {msg.type === 'atom_response' ? (
                <div>
                  <div className="text-gray-400 text-xs mb-1">{msg.timestamp}</div>
                  <div className="flex items-start gap-2">
                    <span className="text-lg">⚛️</span>
                    <p className="text-green-300 font-medium">{msg.text}</p>
                  </div>
                </div>
              ) : msg.type === 'interrupt' ? (
                <div className="bg-red-900 bg-opacity-30 border-l-2 border-red-500 p-2 rounded">
                  <div className="flex items-center gap-2 mb-1">
                    <Zap size={16} color="#ff3333" />
                    <span className="text-red-400 font-bold text-xs">INTERRUPTING</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-lg">⚛️</span>
                    <p className="text-red-300">{msg.text}</p>
                  </div>
                </div>
              ) : (
                <div>
                  <div className="text-gray-500 text-xs mb-1">{msg.timestamp}</div>
                  <p className="text-gray-300">{msg.text}</p>
                </div>
              )}
            </div>
          ))
        )}
        <div ref={feedEndRef} />
      </div>
    </div>
  );
}

export default WhispererFeed;
