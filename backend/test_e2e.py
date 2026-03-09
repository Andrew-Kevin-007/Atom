"""End-to-end test: WS message flow including postmortem generation."""
import asyncio
import json
import urllib.request

import websockets


async def test():
    uri = "wss://atom-backend-803244244025.asia-south1.run.app/ws"
    async with websockets.connect(uri, open_timeout=10) as ws:
        print("WS connected")

        # Start incident via HTTP
        req = urllib.request.Request(
            "https://atom-backend-803244244025.asia-south1.run.app/incident/start",
            data=json.dumps({"name": "E2E Test", "incident_type": "simulated"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            r = json.loads(resp.read())
            print(f"Incident started: {r['incident_id']}")

        # Collect messages for up to 200 seconds (11 logs * 15s + postmortem)
        types_seen = set()
        for _ in range(400):
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=0.5)
                msg = json.loads(raw)
                t = msg.get("type", "?")
                types_seen.add(t)
                if t == "log_event":
                    sev = msg.get("severity", "?")
                    txt = msg.get("message", "")[:60]
                    print(f"  LOG: {sev} - {txt}")
                elif t == "sla_update":
                    print(f"  SLA: {msg.get('sla_seconds_remaining')}s remaining")
                elif t == "atom_response":
                    print(f"  ATOM: {msg.get('text', '')[:80]}")
                elif t == "postmortem_update":
                    content = msg.get("content", {})
                    print(f"  POSTMORTEM: summary={str(content.get('summary', '?'))[:60]}")
                    print(f"  POSTMORTEM: rootCause={str(content.get('rootCause', '?'))[:60]}")
                    items = content.get("actionItems", [])
                    print(f"  POSTMORTEM: {len(items)} action items")
                elif t == "incident_resolved":
                    print("  RESOLVED!")
                elif t == "incident_error":
                    print(f"  ERROR: {msg.get('error', '?')[:80]}")
                elif t == "incident_started":
                    print(f"  STARTED: {msg.get('incident_id')}")
                elif t != "ping":
                    print(f"  OTHER: {t}")
            except asyncio.TimeoutError:
                continue

            if "incident_resolved" in types_seen or "incident_error" in types_seen:
                break

        print(f"\nMessage types seen: {sorted(types_seen)}")

        checks = {
            "incident_started": "incident_started" in types_seen,
            "log_events": "log_event" in types_seen,
            "sla_update": "sla_update" in types_seen,
            "postmortem (WB-9)": "postmortem_update" in types_seen,
            "resolved OR error": "incident_resolved" in types_seen or "incident_error" in types_seen,
        }
        for name, ok in checks.items():
            status = "PASS" if ok else "FAIL"
            print(f"  {status}: {name}")


asyncio.run(test())
