"""
Crowd Simulator — runs on Render without any CV/ML packages.
Simulates realistic crowd density with patterns, spikes, and flow.
"""
import asyncio
import random
import numpy as np
from datetime import datetime
from collections import deque
from models import Zone, Alert, AlertLevel

_broadcast_fn = None

def set_broadcast(fn):
    global _broadcast_fn
    _broadcast_fn = fn

DEFAULT_ZONES = [
    {"zone_id": "A", "name": "Entrance Plaza", "capacity": 850, "location": "North Gate"},
    {"zone_id": "B", "name": "Main Hall",       "capacity": 850, "location": "Central"},
    {"zone_id": "C", "name": "Gate B",          "capacity": 850, "location": "East Wing"},
    {"zone_id": "D", "name": "Food Court",      "capacity": 850, "location": "South Block"},
    {"zone_id": "E", "name": "Corridor E",      "capacity": 850, "location": "West Passage"},
    {"zone_id": "F", "name": "Exit Area",       "capacity": 850, "location": "South Gate"},
]

BASE_COUNTS = {"A": 289, "B": 500, "C": 550, "D": 382, "E": 520, "F": 247}

def density_status(pct):
    if pct >= 80: return AlertLevel.critical
    if pct >= 60: return AlertLevel.warning
    return AlertLevel.safe

def risk_score(pct, flow_delta, predicted_pct):
    return round(min(100, max(0, pct * 0.6 + predicted_pct * 0.3 + min(10, max(-5, flow_delta * 0.5)))))

class ZoneState:
    def __init__(self, zone_id, base_count, capacity):
        self.zone_id  = zone_id
        self.capacity = capacity
        self.count    = base_count
        self.pct      = round(base_count / capacity * 100, 1)
        self.prev     = self.count
        self.history  = deque([self.pct] * 10, maxlen=30)

    def tick(self):
        self.prev  = self.count
        bias       = 0.3 if self.zone_id == "C" else (-0.1 if self.zone_id == "F" else 0.0)
        delta      = random.gauss(bias, 3)
        # Occasional spike (crowd event)
        if random.random() > 0.97:
            delta += random.uniform(15, 30)
        self.count = max(10, min(self.capacity, int(self.count + delta * 8)))
        self.pct   = round(self.count / self.capacity * 100, 1)
        self.history.append(self.pct)

    @property
    def flow_delta(self):
        return self.count - self.prev

    @property
    def predicted_pct(self):
        # Simple linear prediction from recent history
        h = list(self.history)
        if len(h) < 2:
            return self.pct
        trend = (h[-1] - h[0]) / len(h)
        return round(min(100, max(0, self.pct + trend * 5)), 1)

    @property
    def flow_direction(self):
        d = self.flow_delta
        if d > 10:  return "influx ▲"
        if d < -10: return "outflow ▼"
        return "stable ─"


states = {}
prev_status = {}

async def seed_zones():
    for z in DEFAULT_ZONES:
        exists = await Zone.find_one(Zone.zone_id == z["zone_id"])
        bc = BASE_COUNTS.get(z["zone_id"], 200)
        if not exists:
            await Zone(**z, count=bc, density_pct=round(bc / z["capacity"] * 100, 1)).insert()
        if z["zone_id"] not in states:
            states[z["zone_id"]] = ZoneState(z["zone_id"], bc, z["capacity"])

async def run():
    await asyncio.sleep(2)
    await seed_zones()
    print("🤖 Crowd Simulator running")

    while True:
        await asyncio.sleep(2)
        payload = []
        all_zones = await Zone.find_all().to_list()

        for zone in all_zones:
            zid = zone.zone_id
            if zid not in states:
                states[zid] = ZoneState(zid, zone.count or 200, zone.capacity)

            s          = states[zid]
            s.tick()
            new_status = density_status(s.pct)
            prev       = prev_status.get(zid, AlertLevel.safe)
            rs         = risk_score(s.pct, s.flow_delta, s.predicted_pct)

            zone.count       = s.count
            zone.density_pct = s.pct
            zone.status      = new_status
            zone.updated_at  = datetime.utcnow()
            await zone.save()

            if new_status != prev and new_status != AlertLevel.safe:
                msg = (
                    f"Zone {zid} density at {s.pct}% (Risk: {rs}/100) — "
                    + ("STAMPEDE RISK! Deploy emergency response."
                       if new_status == AlertLevel.critical
                       else "Approaching critical. Increase monitoring.")
                )
                await Alert(
                    zone_id=zid, zone_name=zone.name,
                    level=new_status, message=msg,
                    density_pct=s.pct, count=s.count
                ).insert()

            prev_status[zid] = new_status
            payload.append({
                "zone_id":        zid,
                "name":           zone.name,
                "count":          s.count,
                "pct":            s.pct,
                "status":         new_status.value,
                "capacity":       zone.capacity,
                "flow_direction": s.flow_direction,
                "risk_score":     rs,
                "predicted_pct":  s.predicted_pct,
            })

        if _broadcast_fn:
            await _broadcast_fn({
                "type":  "zone_update",
                "zones": payload,
                "ts":    datetime.utcnow().isoformat(),
            })
