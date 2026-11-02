import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import time

app = FastAPI(
    title="Smart AI Safety & Health Monitoring API",
    description="High-performance backend for real-time accident detection, health monitoring, and break reminders.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SensorData(BaseModel):
    accel_x: float
    accel_y: float
    accel_z: float
    gyro_x: float
    gyro_y: float
    gyro_z: float
    speed: float
    latitude: float
    longitude: float

class HealthData(BaseModel):
    heart_rate: Optional[int] = None
    step_count: Optional[int] = None
    screen_time_minutes: int = 0

class SafetyEventReport(BaseModel):
    device_id: str
    timestamp: float = Field(default_factory=time.time)
    sensors: SensorData
    health: HealthData
    event_type: str = Field(..., description="NORMAL, ACCIDENT_DETECTED, HIGH_SCREEN_TIME_WARNING, HEALTH_ANOMALY")
    confidence_score: float

class EmergencyContact(BaseModel):
    name: str
    phone: str

class DeviceRegistration(BaseModel):
    device_id: str
    user_name: str
    emergency_contacts: List[EmergencyContact]

# In-memory store (Replace with Redis/PostgreSQL for production on Render)
active_alerts = []
registered_devices = {}

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Smart AI Safety Backend",
        "performance": "Ultra-fast FastAPI / Uvicorn ASGI",
        "endpoints": ["/api/v1/telemetry", "/api/v1/register", "/api/v1/alerts"]
    }

@app.post("/api/v1/register")
def register_device(data: DeviceRegistration):
    registered_devices[data.device_id] = data.dict()
    return {"status": "success", "message": f"Device {data.device_id} registered successfully."}

@app.post("/api/v1/telemetry")
def receive_telemetry(report: SafetyEventReport, background_tasks: BackgroundTasks):
    """
    Receives real-time sensor & health telemetry from Android client.
    Triggers emergency workflows if an accident or health anomaly is detected.
    """
    if report.event_type in ["ACCIDENT_DETECTED", "HEALTH_ANOMALY"]:
        alert_record = {
            "device_id": report.device_id,
            "event_type": report.event_type,
            "timestamp": report.timestamp,
            "location": {"lat": report.sensors.latitude, "lng": report.sensors.longitude},
            "confidence": report.confidence_score,
            "status": "ACTIVE_EMERGENCY"
        }
        active_alerts.append(alert_record)

        # Background task to dispatch SMS / Push Notifications to Emergency Contacts
        background_tasks.add_task(dispatch_emergency_notifications, report.device_id, alert_record)

    return {
        "status": "received",
        "action_required": report.event_type != "NORMAL",
        "server_timestamp": time.time()
    }

@app.get("/api/v1/alerts")
def get_active_alerts():
    return {"active_alerts": active_alerts}

def dispatch_emergency_notifications(device_id: str, alert: dict):
    # Integration point for Twilio SMS, Firebase Cloud Messaging (FCM), or Webhooks
    device_info = registered_devices.get(device_id, {})
    contacts = device_info.get("emergency_contacts", [])
    print(f"[EMERGENCY DISPATCH] Alert for device {device_id} at location {alert['location']}.")
    print(f"Notifying {len(contacts)} emergency contacts...")
    for contact in contacts:
        print(f" -> Sending emergency SMS to {contact['name']} ({contact['phone']})")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, workers=4)
