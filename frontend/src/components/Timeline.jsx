import React, { useEffect, useRef } from 'react';
import { AlertCircle, AlertTriangle, Info } from 'lucide-react';

/**
 * Timeline Component
 * Chronological list of incident events color-coded by severity
 * INFO (grey), WARNING (amber), ERROR (orange), CRITICAL (red)
 */
export function Timeline({ events = [] }) {
  const timelineEndRef = useRef(null);

  // Auto-scroll to latest event
  useEffect(() => {
    timelineEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  // Get severity icon and color
  const getSeverityStyle = (severity) => {
    switch (severity) {
      case 'CRITICAL':
        return {
          color: '#ff3333',
          bgColor: 'rgba(255, 51, 51, 0.1)',
          icon: AlertCircle,
        };
      case 'ERROR':
        return {
          color: '#ff8800',
          bgColor: 'rgba(255, 136, 0, 0.1)',
          icon: AlertTriangle,
        };
      case 'WARNING':
        return {
          color: '#ffaa00',
          bgColor: 'rgba(255, 170, 0, 0.1)',
          icon: AlertTriangle,
        };
      default:
        return {
          color: '#888888',
          bgColor: 'rgba(136, 136, 136, 0.1)',
          icon: Info,
        };
    }
  };

  return (
    <div className="h-full bg-card rounded-lg border border-gray-700 overflow-hidden flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-700">
        <h2 className="text-lg font-bold">Incident Timeline</h2>
      </div>

      {/* Timeline */}
      <div className="flex-1 overflow-y-auto p-4">
        {events.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-sm">Waiting for events...</p>
          </div>
        ) : (
          <div className="space-y-2">
            {events.map((event, idx) => {
              const severity = event.severity || 'INFO';
              const style = getSeverityStyle(severity);
              const Icon = style.icon;

              return (
                <div key={idx} className="relative">
                  <div
                    className="p-3 rounded border-l-2 text-xs"
                    style={{
                      backgroundColor: style.bgColor,
                      borderColor: style.color,
                    }}
                  >
                    <div className="flex items-start gap-2">
                      <Icon size={14} color={style.color} className="flex-shrink-0 mt-0.5" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span
                            className="px-2 py-0.5 rounded text-xs font-bold"
                            style={{ color: style.color }}
                          >
                            {severity}
                          </span>
                          <span className="text-gray-400">{event.timestamp}</span>
                          {event.source && (
                            <span className="text-gray-500 text-xs">({event.source})</span>
                          )}
                        </div>
                        <p className="text-gray-200 break-words">{event.message}</p>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
            <div ref={timelineEndRef} />
          </div>
        )}
      </div>
    </div>
  );
}

export default Timeline;
