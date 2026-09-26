import { statusText } from "../utils/sensorStatus.js";

// ============================================================
// STATUS LED
// ============================================================
//
// Small reusable dot used everywhere a sensor/building status
// needs to be shown: grey = offline, green = online, red = alarm.
// ============================================================

export default function StatusLED({ color }) {
  return (
    <span className={`led ${color}`} aria-label={statusText(color)} />
  );
}
