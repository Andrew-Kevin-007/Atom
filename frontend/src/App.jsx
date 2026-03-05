import React, { useState, useEffect, useRef } from 'react';
import { AlertCircle, Play, Square, Zap } from 'lucide-react';
import SLACountdown from './components/SLACountdown';
import WhispererFeed from './components/WhispererFeed';
import Timeline from './components/Timeline';
import Postmortem from './components/Postmortem';

/**
 * ATOM - Autonomous Threat & Operations Monitor
 * Main application component - war room UI
 */
function App() {
  const [incident, setIncident] = useState(null);
  const [messages, setMessages] = useState([]);
  const [events, setEvents] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState('idle'); // idle, active, resolved
  const [slaSecondsRemaining, setSlaSecondsRemaining] = useState(null);
  const wsRef = useRef(null);

  // WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        wsRef.current = new WebSocket('ws://localhost:8000/ws');

        wsRef.current.onopen = () => {
          console.log('✓ WebSocket connected');
        };

        wsRef.current.onmessage = (event) => {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        };

        wsRef.current.onclose = () => {
          console.log('✗ WebSocket disconnected');
          // Attempt reconnection
          setTimeout(connectWebSocket, 3000);
        };

        wsRef.current.onerror = (error) => {
          console.error('WebSocket error:', error);
        };
      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
      }
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Handle WebSocket messages
  const handleWebSocketMessage = (data) => {
    const timestamp = new Date().toLocaleTimeString();

    switch (data.type) {
      case 'incident_started':
        setIncident({ id: data.incident_id, status: 'active' });
        setStatus('active');
        setMessages([]);
        setEvents([]);
        console.log(`🚀 Incident started: ${data.incident_id}`);
        break;

      case 'atom_response':
        const atomMsg = {
          type: 'atom_response',
          text: data.text,
          timestamp: timestamp,
        };
        setMessages(prev => [...prev, atomMsg]);
        console.log(`🔊 ATOM: ${data.text}`);
        break;

      case 'log_event':
        const logEvent = {
          message: data.message,
          severity: data.severity,
          timestamp: timestamp,
          source: 'LOGS',
        };
        setEvents(prev => [...prev, logEvent]);

        // Parse SLA messages
        if (data.message.includes('SLA breach imminent')) {
          const match = data.message.match(/(\d+) seconds/);
          if (match) {
            setSlaSecondsRemaining(parseInt(match[1]));
          }
        }
        break;

      case 'incident_resolved':
        setStatus('resolved');
        setIncident(prev => prev ? { ...prev, status: 'resolved' } : null);
        console.log('✓ Incident resolved');
        break;

      default:
        break;
    }
  };

  // Start new incident
  const handleStartIncident = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/incident/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Production Incident', incident_type: 'simulated' }),
      });

      const data = await response.json();
      console.log('Incident started:', data);
    } catch (error) {
      console.error('Failed to start incident:', error);
      alert('Failed to start incident. Is the backend running?');
    } finally {
      setIsLoading(false);
    }
  };

  // Stop incident
  const handleStopIncident = async () => {
    if (!incident) return;

    try {
      await fetch(`http://localhost:8000/incident/${incident.id}/stop`, {
        method: 'POST',
      });

      setIncident(null);
      setStatus('idle');
      setMessages([]);
      setEvents([]);
      setSlaSecondsRemaining(null);
    } catch (error) {
      console.error('Failed to stop incident:', error);
    }
  };

  return (
    <div
      className="h-screen overflow-hidden"
      style={{
        backgroundColor: '#0a0a0f',
        color: '#e0e0e0',
        fontFamily: 'system-ui, -apple-system, sans-serif',
      }}
    >
      {/* Top Bar */}
      <div
        className="border-b border-gray-700 px-6 py-4 flex items-center justify-between"
        style={{ backgroundColor: '#12121a' }}
      >
        <div className="flex items-center gap-3">
          <div className="text-3xl">⚛️</div>
          <div>
            <h1 className="text-2xl font-bold">ATOM</h1>
            <p style={{ color: '#888' }} className="text-xs">
              Autonomous Threat &amp; Operations Monitor
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Status Badge */}
          {incident && (
            <div className="flex items-center gap-2">
              <div
                className="w-2 h-2 rounded-full animate-pulse"
                style={{
                  backgroundColor:
                    status === 'resolved' ? '#00ff88' : status === 'active' ? '#ff3333' : '#888',
                }}
              />
              <span className="text-sm font-mono" style={{ color: '#888' }}>
                {incident.id}
              </span>
            </div>
          )}

          {/* Action Buttons */}
          {status === 'idle' ? (
            <button
              onClick={handleStartIncident}
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2 rounded font-semibold transition-colors"
              style={{
                backgroundColor: '#00ff88',
                color: '#000',
                opacity: isLoading ? 0.5 : 1,
              }}
            >
              <Play size={18} />
              {isLoading ? 'Starting...' : 'Start Incident'}
            </button>
          ) : (
            <button
              onClick={handleStopIncident}
              className="flex items-center gap-2 px-4 py-2 rounded font-semibold transition-colors"
              style={{
                backgroundColor: '#ff3333',
                color: '#fff',
              }}
            >
              <Square size={18} />
              Stop
            </button>
          )}
        </div>
      </div>

      {/* Main Content */}
      {status === 'idle' ? (
        <div
          className="h-full flex flex-col items-center justify-center"
          style={{ backgroundColor: '#0a0a0f' }}
        >
          <Zap size={48} style={{ color: '#00ff88', marginBottom: '1rem' }} />
          <h2 className="text-3xl font-bold mb-4">Ready to Monitor Incidents</h2>
          <p style={{ color: '#888' }} className="mb-6 text-center max-w-xl">
            ATOM is a real-time incident intelligence agent. Click "Start Incident" to begin a
            simulated demo incident with full voice, screen, and log monitoring.
          </p>

          <div
            className="bg-gray-900 bg-opacity-50 border border-gray-700 rounded p-6 max-w-xl"
            style={{ backgroundColor: '#1a1a1f' }}
          >
            <h3 className="font-bold mb-3">How it works:</h3>
            <ul style={{ color: '#aaa' }} className="space-y-2 text-sm">
              <li>• ATOM monitors microphone, screen, and production logs simultaneously</li>
              <li>• Detects correlation between errors and system changes</li>
              <li>• Speaks up proactively when SLA breach is imminent</li>
              <li>• Suggests root cause and resolution</li>
              <li>• Generates postmortem automatically</li>
            </ul>
          </div>

          <button
            onClick={handleStartIncident}
            className="mt-8 px-8 py-3 rounded font-bold text-lg transition-colors"
            style={{
              backgroundColor: '#00ff88',
              color: '#000',
            }}
          >
            Start Demo Incident
          </button>
        </div>
      ) : (
        <div className="h-full flex overflow-hidden">
          {/* Left Panel (40%) */}
          <div className="w-5/12 flex flex-col border-r border-gray-700 p-4 gap-4 overflow-hidden">
            <div className="flex-1 min-h-0">
              <WhispererFeed messages={messages} />
            </div>
            <div className="flex-1 min-h-0">
              <Timeline events={events} />
            </div>
          </div>

          {/* Right Panel (60%) */}
          <div className="w-7/12 flex flex-col p-4 gap-4 overflow-hidden">
            <div className="h-1/3 min-h-0">
              <SLACountdown slaSecondsRemaining={slaSecondsRemaining} isResolved={status === 'resolved'} />
            </div>
            <div className="h-2/3 min-h-0">
              <Postmortem incident={incident} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
