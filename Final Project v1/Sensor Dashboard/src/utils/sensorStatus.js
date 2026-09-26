// ============================================================
// SENSOR / BUILDING STATUS LOGIC
// ============================================================
//
// GREY  = no recent data (offline)
// RED   = online + alarm active
// GREEN = online + no alarm
//
// This is the ONLY place in the app that decides these colors,
// so every component (Sidebar, BuildingCard, SensorRow,
// SensorDetailPage) shows the same status for the same sensor.
// ============================================================

// A sensor is "online" if its last reading is newer than this
// many milliseconds. Sensors send data every ~3s, so 10s gives
// room for a delayed message or two.
const ONLINE_TIMEOUT_MS = 10000;

export function isOnline(reading, now) {
  if (!reading) {
    return false;
  }
  return now - new Date(reading.receivedAt).getTime() < ONLINE_TIMEOUT_MS;
}

export function sensorStatus(reading, now) {
  if (!isOnline(reading, now)) {
    return "grey";
  }
  return reading.alarm ? "red" : "green";
}

export function statusText(status) {
  if (status === "green") return "Online";
  if (status === "red") return "Alarm";
  return "Offline";
}

// Building status from its sensors (priority order):
//   RED   = at least one ONLINE sensor has an active alarm
//   GREY  = no sensor in the building is online
//   GREEN = at least one sensor online, none in alarm
export function buildingStatus(sensors, readings, now) {
  let anyOnline = false;
  let anyAlarm = false;

  for (const sensor of sensors) {
    const reading = readings[sensor.id];
    if (isOnline(reading, now)) {
      anyOnline = true;
      if (reading.alarm) {
        anyAlarm = true;
      }
    }
  }

  if (anyAlarm) return "red";
  if (anyOnline) return "green";
  return "grey";
}

export function buildingText(status) {
  if (status === "green") return "Online / Normal";
  if (status === "red") return "Alarm";
  return "Offline";
}
