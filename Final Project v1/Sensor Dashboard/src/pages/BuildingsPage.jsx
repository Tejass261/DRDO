import BuildingCard from "../components/BuildingCard.jsx";
import { buildingStatus } from "../utils/sensorStatus.js";

// ============================================================
// BUILDINGS OVERVIEW PAGE
// ============================================================
//
// Groups all sensors by location and shows one BuildingCard
// per location.
// ============================================================

export default function BuildingsPage({ sensors, readings, now }) {

  // ---- Group sensors by location ----

  const byLocation = {};

  for (const sensor of sensors) {
    if (!byLocation[sensor.location]) {
      byLocation[sensor.location] = [];
    }
    byLocation[sensor.location].push(sensor);
  }

  const locations = Object.keys(byLocation).sort();

  return (
    <section>

      <div className="page-heading">
        <div>
          <p className="eyebrow">OVERVIEW</p>
          <h1>Buildings</h1>
        </div>
        <span className="count-pill">{locations.length} locations</span>
      </div>

      <div className="building-grid">
        {locations.map(location => {

          const buildingSensors = byLocation[location];
          const status = buildingStatus(buildingSensors, readings, now);

          return (
            <BuildingCard
              key={location}
              location={location}
              status={status}
              sensors={buildingSensors}
              readings={readings}
              now={now}
            />
          );
        })}
      </div>

    </section>
  );
}
