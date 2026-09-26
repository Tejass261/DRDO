import StatusLED from "./StatusLED.jsx";
import { sensorStatus, buildingText } from "../utils/sensorStatus.js";

// ============================================================
// BUILDING CARD
// ============================================================
//
// One card in the Buildings overview grid: building status LED,
// name, state text, sensor count, and a list of its sensors.
// ============================================================

export default function BuildingCard({ location, status, sensors, readings, now }) {
  return (
    <div className="building-card">

      <div className="building-led-row">
        <StatusLED color={status} />
      </div>

      <h2>{location.replaceAll("-", " ")}</h2>

      <p className={`building-state ${status}`}>
        {buildingText(status)}
      </p>

      <p className="building-count">
        {sensors.length} sensor{sensors.length !== 1 ? "s" : ""}
      </p>

      <ul className="building-sensors">
        {sensors.map(sensor => (
          <li key={sensor.id}>
            <StatusLED color={sensorStatus(readings[sensor.id], now)} />
            {sensor.id}
          </li>
        ))}
      </ul>

    </div>
  );
}
