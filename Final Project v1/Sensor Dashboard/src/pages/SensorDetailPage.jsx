import StatusLED from "../components/StatusLED.jsx";
import ReadingCard from "../components/ReadingCard.jsx";
import SensorGraph from "../components/SensorGraph.jsx";
import { sensorStatus, statusText } from "../utils/sensorStatus.js";

// ============================================================
// DISPLAY LABELS
// ============================================================
//
// These are only UI labels, used to build the reading grid on
// this page. The actual parsing of the sensor payload happens
// in Python - the frontend only reads already-parsed fields.
// ============================================================

const labels = {

  bio: {
    sampleType: "Sample type",
    smallParticleCount: "Small particle count",
    largeParticleCount: "Large particle count",
    smallBiologicalLoad: "Small biological load",
    largeBiologicalLoad: "Large biological load",
    alarm: "Alarm"
  },

  chem: {
    date: "Date",
    time: "Time",
    gValue: "G value",
    hValue: "H value",
    mode: "Mode"
  },

  fcad: {
    sensorName: "Sensor name",
    gValue: "G value",
    hValue: "H value",
    atmosphericPressureG: "Atmospheric pressure G",
    atmosphericPressureH: "Atmospheric pressure H",
    gPressure: "G pressure",
    hPressure: "H pressure",
    battery: "Battery",
    mode: "Mode"
  }
};

// ============================================================
// GRAPH DEFINITIONS
// ============================================================
//
// Which already-parsed backend values each sensor type plots
// on its live graph. The frontend never parses raw payloads -
// it only reads these fields from message.data.
// ============================================================

const graphConfig = {

  bio: [
    { key: "smallParticleCount", label: "Small particle count", color: "#2868d7" }
  ],

  chem: [
    { key: "gValue", label: "G value", color: "#2868d7" },
    { key: "hValue", label: "H value", color: "#d97b28" }
  ],

  fcad: [
    { key: "gValue", label: "G value", color: "#2868d7" },
    { key: "hValue", label: "H value", color: "#d97b28" }
  ]
};

// ============================================================
// SENSOR DETAIL PAGE
// ============================================================
//
// Layout:
//   - Sensor name + status LED at the top
//   - Reading boxes (empty boxes with "—" until data arrives)
//   - Live graph at the bottom
// ============================================================

export default function SensorDetailPage({ sensor, reading, history, now }) {

  const status = sensorStatus(reading, now);
  const typeLabels = labels[sensor.type] || {};
  const config = graphConfig[sensor.type];

  // Build the graph series from the backend-parsed values that
  // are already inside each reading's `data` object.
  const series = config
    ? config.map(line => ({
        ...line,
        points: history.map(item => Number(item.data?.[line.key]))
      }))
    : [];

  return (
    <section className="detail-view">

      <p className="eyebrow">
        {sensor.location.replaceAll("-", " ")}
        {" · "}
        {sensor.type}
      </p>

      <div className="detail-title-row">
        <h1>{sensor.id}</h1>

        <span className="detail-status">
          <StatusLED color={status} />
          {statusText(status)}
        </span>
      </div>

      <p className="detail-subline">
        {sensor.ip}:{sensor.port}
        {" · "}
        <span className="topic">{sensor.topic}</span>
        {" · "}
        {reading
          ? `Last received: ${new Date(reading.receivedAt).toLocaleTimeString()}`
          : "No reading received yet"}
      </p>

      {/* -------- Reading boxes -------- */}

      <div className="reading-grid">
        {Object.entries(typeLabels).map(([key, text]) => (
          <ReadingCard
            key={key}
            label={text}
            value={reading ? String(reading.data?.[key] ?? "—") : "—"}
            hasReading={!!reading}
          />
        ))}
      </div>

      {!reading && (
        <p className="empty-copy">
          Waiting for data from this sensor.
          The boxes above will fill in automatically.
        </p>
      )}

      {/* -------- Live graph -------- */}

      {config && (
        <>
          <h2>Live graph</h2>
          <SensorGraph
            series={series}
            yLabel={config.length === 1 ? config[0].label : "Value"}
          />
        </>
      )}

    </section>
  );
}
