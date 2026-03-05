import React, { useState, useEffect } from 'react';
import { AlertTriangle, Clock } from 'lucide-react';

/**
 * SLACountdown Component
 * Displays dramatic SLA breach countdown with color transitions
 * Green → Amber (5 min) → Red (2 min) → Flashing Red (30 sec)
 */
export function SLACountdown({ slaSecondsRemaining, isResolved }) {
  const [isFlashing, setIsFlashing] = useState(false);

  // Flash effect when under 30 seconds
  useEffect(() => {
    if (slaSecondsRemaining !== null && slaSecondsRemaining < 30 && !isResolved) {
      const interval = setInterval(() => {
        setIsFlashing(prev => !prev);
      }, 500);
      return () => clearInterval(interval);
    }
    setIsFlashing(false);
  }, [slaSecondsRemaining, isResolved]);

  // Determine color based on SLA time remaining
  const getColor = () => {
    if (isResolved) return '#00ff88';
    if (slaSecondsRemaining === null) return '#e0e0e0';
    if (slaSecondsRemaining < 30) return isFlashing ? '#ff3333' : '#1a1a1f';
    if (slaSecondsRemaining < 120) return '#ff3333';
    if (slaSecondsRemaining < 300) return '#ffaa00';
    return '#00ff88';
  };

  // Format time display
  const formatTime = () => {
    if (isResolved) return 'RESOLVED';
    if (slaSecondsRemaining === null) return '--:--';
    
    const minutes = Math.floor(slaSecondsRemaining / 60);
    const seconds = slaSecondsRemaining % 60;
    return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
  };

  return (
    <div className="bg-card p-6 rounded-lg border border-gray-700 h-full flex flex-col justify-center items-center">
      {isResolved ? (
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-4" style={{ color: '#00ff88' }}>
            ✓ INCIDENT RESOLVED
          </h2>
          <p className="text-gray-400">All systems nominal</p>
        </div>
      ) : slaSecondsRemaining !== null && slaSecondsRemaining < 120 ? (
        <>
          <div className="flex items-center gap-3 mb-4">
            <AlertTriangle color="#ff3333" size={32} />
            <span className="text-xl font-bold text-red-500">SLA BREACH IMMINENT</span>
          </div>
          <div className="text-7xl font-mono font-bold mb-4" style={{ color: getColor() }}>
            {formatTime()}
          </div>
          <p className="text-gray-400 text-center">Payments service at critical latency</p>
        </>
      ) : (
        <>
          <div className="flex items-center gap-2 mb-4">
            <Clock size={24} color={getColor()} />
            <span className="text-gray-400">Time to SLA</span>
          </div>
          <div className="text-6xl font-mono font-bold" style={{ color: getColor() }}>
            {formatTime()}
          </div>
        </>
      )}
    </div>
  );
}

export default SLACountdown;
