// ============================================================
// BACKEND WEBSOCKET SERVICE
// ============================================================
//
// This is the ONLY place in the app that talks to the Python
// backend directly. React components never touch a WebSocket
// object - they just get called back through the `handlers`
// passed into connectToBackend().
//
// React must NOT connect directly to MQTT or edit Config.txt.
// This file only opens a WebSocket to the already-running
// Python backend at WEBSOCKET_URL.
// ============================================================

const WEBSOCKET_URL = "ws://127.0.0.1:8765";

// How long to wait (ms) before trying to reconnect when the
// backend WebSocket is not available.
const RECONNECT_DELAY_MS = 2000;

// Connects to the backend and keeps reconnecting automatically
// if the connection drops.
//
// `handlers` is an object with:
//   onStatusChange(status)      - "connecting" | "connected" | "reconnecting"
//   onConfig(message)           - backend sent sensor configuration
//   onReading(message)          - backend sent a sensor reading
//   onAddSensorResult(message)  - result of an "add sensor" command
//
// Returns an object with:
//   sendAddSensor(sensor) - sends an add-sensor command to the
//                            backend. Returns { success: false, message }
//                            immediately if there is no open connection.
//   disconnect()          - closes the connection and stops reconnecting.
//                            Call this when the app is unmounting.
export function connectToBackend(handlers) {

  let socket = null;
  let reconnectTimer = null;
  let closedByUs = false;

  function handleMessage(event) {
    try {
      const message = JSON.parse(event.data);

      // Backend sends sensor configuration.
      if (message.event === "config") {
        handlers.onConfig(message);
        return;
      }

      // Backend sends a sensor reading.
      if (message.event === "reading") {
        handlers.onReading(message);
        return;
      }

      // Result of an "add sensor" command.
      if (message.event === "add_sensor_result") {
        handlers.onAddSensorResult(message);
        return;
      }
    } catch (error) {
      console.error("[WebSocket] Invalid message:", error);
    }
  }

  function connect() {
    console.log(`[WebSocket] Connecting to ${WEBSOCKET_URL}`);

    handlers.onStatusChange("connecting");

    socket = new WebSocket(WEBSOCKET_URL);

    socket.onopen = () => {
      console.log("[WebSocket] Connected to backend.");
      handlers.onStatusChange("connected");
    };

    socket.onmessage = handleMessage;

    socket.onclose = () => {
      if (closedByUs) {
        return;
      }

      console.log("[WebSocket] Connection lost. Retrying soon…");

      handlers.onStatusChange("reconnecting");

      // Try again after a short pause.
      reconnectTimer = setTimeout(connect, RECONNECT_DELAY_MS);
    };

    socket.onerror = () => {
      // Close the broken socket so onclose fires and the
      // reconnect timer starts.
      socket.close();
    };
  }

  connect();

  function sendAddSensor(sensor) {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      return {
        success: false,
        message: "Backend is not connected. Cannot add sensor right now."
      };
    }

    socket.send(
      JSON.stringify({
        event: "add_sensor",
        sensor: sensor
      })
    );

    return { success: true };
  }

  function disconnect() {
    closedByUs = true;
    clearTimeout(reconnectTimer);
    if (socket) {
      socket.close();
    }
  }

  return { sendAddSensor, disconnect };
}
