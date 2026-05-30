from app.core.config import get_settings
from app.services.tools.base import ToolResult


class IoTTool:
    name = "iot"
    description = "IoT integration layer for MQTT, ESP32, and home automation commands."
    input_schema = {
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "payload": {"type": "object"},
        },
        "required": ["topic", "payload"],
    }

    async def run(self, payload: dict) -> ToolResult:
        settings = get_settings()
        if not settings.mqtt_broker_url:
            return ToolResult(ok=False, output="MQTT broker not configured", metadata={})
        return ToolResult(
            ok=False,
            output="MQTT execution adapter is reserved for deployment-specific credentials.",
            metadata={"broker": settings.mqtt_broker_url, "topic": payload.get("topic")},
        )
