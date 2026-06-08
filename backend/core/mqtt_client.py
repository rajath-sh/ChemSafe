"""
ChemSafe IoT — MQTT Client (HiveMQ Cloud)

Singleton paho-mqtt client that connects to HiveMQ Cloud.
Used by the mqtt_ingestion module for subscribing to sensor topics,
and by any module that needs to publish MQTT messages.

Connection is TLS-secured by default (HiveMQ Cloud requirement).
"""

from __future__ import annotations

import json
import logging
import ssl
from typing import Any, Callable

import paho.mqtt.client as mqtt

from core.config import settings

logger = logging.getLogger(__name__)

# Type alias
MQTTMessageHandler = Callable[[str, dict[str, Any]], None]


class MQTTClient:
    """
    Wrapper around paho-mqtt for HiveMQ Cloud.
    Handles TLS, auto-reconnect, and structured message parsing.
    """

    def __init__(self):
        self._client: mqtt.Client | None = None
        self._connected = False
        self._message_handlers: dict[str, list[MQTTMessageHandler]] = {}

    @property
    def is_connected(self) -> bool:
        return self._connected

    def connect(self) -> None:
        """Initialize and connect the MQTT client to HiveMQ Cloud."""
        if self._client is not None:
            logger.warning("MQTT client already initialized")
            return

        self._client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=settings.MQTT_CLIENT_ID,
            protocol=mqtt.MQTTv5,
        )

        # Auth
        if settings.MQTT_USERNAME:
            self._client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

        # TLS (required for HiveMQ Cloud)
        if settings.MQTT_USE_TLS:
            self._client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)

        # Callbacks
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        try:
            self._client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, keepalive=60)
            self._client.loop_start()
            logger.info("MQTT: connecting to %s:%d ...", settings.MQTT_BROKER, settings.MQTT_PORT)
        except Exception as e:
            logger.error("MQTT: failed to connect to %s:%d. Broker unavailable or actively refused connection. (%s)", settings.MQTT_BROKER, settings.MQTT_PORT, str(e))

    def disconnect(self) -> None:
        """Gracefully disconnect the MQTT client."""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._client = None
            self._connected = False
            logger.info("MQTT: disconnected")

    def subscribe(self, topic: str, handler: MQTTMessageHandler) -> None:
        """
        Subscribe to a topic and register a handler.

        Args:
            topic: MQTT topic (supports wildcards: +, #)
            handler: function(topic: str, payload: dict) → None
        """
        if topic not in self._message_handlers:
            self._message_handlers[topic] = []
            if self._client and self._connected:
                self._client.subscribe(topic, qos=1)
                logger.info("MQTT: subscribed to '%s'", topic)

        self._message_handlers[topic].append(handler)

    def publish(self, topic: str, payload: dict[str, Any], qos: int = 1) -> None:
        """Publish a JSON message to a topic."""
        if not self._client or not self._connected:
            logger.warning("MQTT: cannot publish — not connected")
            return

        message = json.dumps(payload)
        self._client.publish(topic, message, qos=qos)
        logger.debug("MQTT: published to '%s'", topic)

    # ── Internal callbacks ────────────────────────────────────

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            self._connected = True
            logger.info("MQTT: connected successfully")
            # Re-subscribe to all registered topics
            for topic in self._message_handlers:
                client.subscribe(topic, qos=1)
                logger.info("MQTT: re-subscribed to '%s'", topic)
        else:
            logger.error("MQTT: connection failed with code %s", reason_code)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None):
        self._connected = False
        logger.warning("MQTT: disconnected (code=%s) — will auto-reconnect", reason_code)

    def _on_message(self, client, userdata, msg: mqtt.MQTTMessage):
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.warning("MQTT: invalid JSON on topic '%s'", topic)
            return

        # Dispatch to matching handlers (exact match + wildcard patterns)
        for pattern, handlers in self._message_handlers.items():
            if mqtt.topic_matches_sub(pattern, topic):
                for handler in handlers:
                    try:
                        handler(topic, payload)
                    except Exception:
                        logger.exception(
                            "MQTT: error in handler for topic '%s'", topic
                        )


# ── Singleton instance ────────────────────────────────────────
mqtt_client = MQTTClient()
