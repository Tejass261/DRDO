import StatusLED from "./StatusLED.jsx";
import { sensorStatus, statusText } from "../utils/sensorStatus.js";

// ============================================================
// SENSOR ROW
// ============================================================
//
// One row in the Sensor List page. Clicking it opens the
// sensor's detail tab.
// ============================================================

export default function SensorRow({ sensor, readings, now, onOpen }) {

  const reading = readings[sensor.id];
  const status = sensorStatus(reading, now);

  return (
    <button className="sensor-row" onClick={() => onOpen(sensor.id)}>

      <span className="row-status">
        <StatusLED color={status} />
      </span>

      <div className="row-main">
        <strong>{sensor.id}</strong>
        <small>
          {sensor.type}
          {" · "}
          {sensor.location.replaceAll("-", " ")}
        </small>
      </div>

      <span className={`row-state ${status}`}>
        {statusText(status)}
      </span>

      <span className="row-time">
        {reading ? new Date(reading.receivedAt).toLocaleTimeString() : "no data yet"}
      </span>

    </button>
  );
}
