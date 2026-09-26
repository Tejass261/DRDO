import StatusLED from "./StatusLED.jsx";
import { sensorStatus } from "../utils/sensorStatus.js";

// ============================================================
// SIDEBAR
// ============================================================
//
// Tab navigation:
//   - Buildings (permanent)
//   - All sensors (permanent)
//   - one closable tab per currently open sensor
//   - Add sensor (permanent)
// ============================================================

export default function Sidebar({
  sensors,
  readings,
  now,
  openTabs,
  activeTab,
  onSelectTab,
  onCloseTab
}) {
  return (
    <aside className="sidebar">

      {/* -------- Permanent: Buildings tab -------- */}

      <button
        className={`side-tab permanent-tab ${activeTab === "buildings" ? "active" : ""}`}
        onClick={() => onSelectTab("buildings")}
      >
        <span>Buildings</span>
        <small>Overview</small>
      </button>

      {/* -------- Permanent: List tab -------- */}

      <button
        className={`side-tab permanent-tab ${activeTab === "list" ? "active" : ""}`}
        onClick={() => onSelectTab("list")}
      >
        <span>All sensors</span>
        <small>{sensors.length} configured</small>
      </button>

      {/* -------- Closable sensor tabs -------- */}

      {openTabs.map(id => {

        const sensor = sensors.find(item => item.id === id);

        if (!sensor) {
          return null;
        }

        const status = sensorStatus(readings[id], now);

        return (
          <button
            className={`side-tab ${activeTab === id ? "active" : ""}`}
            key={id}
            onClick={() => onSelectTab(id)}
          >
            <span>
              <StatusLED color={status} />
              {sensor.id}
            </span>

            <small>{sensor.location}</small>

            <b onClick={event => onCloseTab(event, id)}>×</b>
          </button>
        );
      })}

      {/* -------- Add sensor (permanent entry) -------- */}

      <button
        className={`side-tab add-tab ${activeTab === "add" ? "active" : ""}`}
        onClick={() => onSelectTab("add")}
      >
        <span>＋ Add sensor</span>
      </button>

    </aside>
  );
}
