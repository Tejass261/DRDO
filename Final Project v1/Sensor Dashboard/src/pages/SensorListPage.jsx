import SensorRow from "../components/SensorRow.jsx";

// ============================================================
// SENSOR LIST PAGE
// ============================================================
//
// Shows every configured sensor as a clickable row. Clicking a
// row opens that sensor's detail tab (via the onOpen callback
// passed down from App.jsx).
// ============================================================

export default function SensorListPage({ sensors, readings, now, onOpen }) {
  return (
    <section>

      <div className="page-heading">
        <div>
          <p className="eyebrow">LIVE MONITORING</p>
          <h1>All configured sensors</h1>
        </div>
        <span className="count-pill">{sensors.length} sensors</span>
      </div>

      <div className="sensor-list">
        {sensors.map(sensor => (
          <SensorRow
            key={sensor.id}
            sensor={sensor}
            readings={readings}
            now={now}
            onOpen={onOpen}
          />
        ))}
      </div>

    </section>
  );
}
