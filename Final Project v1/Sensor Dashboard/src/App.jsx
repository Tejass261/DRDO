import { useEffect, useRef, useState } from "react";

import { connectToBackend } from "./services/websocket.js";

import Header from "./components/Header.jsx";
import Sidebar from "./components/Sidebar.jsx";

import BuildingsPage from "./pages/BuildingsPage.jsx";
import SensorListPage from "./pages/SensorListPage.jsx";
import SensorDetailPage from "./pages/SensorDetailPage.jsx";
import AddSensorPage from "./pages/AddSensorPage.jsx";

// ============================================================
// MAIN APPLICATION
// ============================================================
//
// App.jsx owns all the shared state (sensors, readings,
// history, which tab is active, backend connection status)
// and decides which page to show. The actual WebSocket
// connection lives in services/websocket.js - App.jsx just
// reacts to the events it reports.
// ============================================================

// How many recent readings each graph keeps in memory.
const MAX_GRAPH_POINTS = 60;

export default function App() {

  const [sensors, setSensors] = useState([]);
  const [sensorTypes, setSensorTypes] = useState([]);

  // Latest reading per sensor: { sensorId: readingMessage }
  const [readings, setReadings] = useState({});

  // Recent readings per sensor (for the graphs):
  // { sensorId: [readingMessage, ...] } max MAX_GRAPH_POINTS
  const [history, setHistory] = useState({});

  const [openTabs, setOpenTabs] = useState([]);

  // "buildings" | "list" | "add" | <sensorId>
  const [activeTab, setActiveTab] = useState("buildings");

  const [backendStatus, setBackendStatus] = useState("connecting");

  const [addResult, setAddResult] = useState(null);

  // Holds the connection object returned by connectToBackend(),
  // so the Add Sensor page can send commands through it.
  const connectionRef = useRef(null);

  // Current time, updated once per second so that the
  // Online / Offline LEDs refresh automatically even when
  // no new data arrives.
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    const timer = setInterval(() => {
      setNow(Date.now());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // ==========================================================
  // BACKEND CONNECTION
  // ==========================================================

  useEffect(() => {

    const connection = connectToBackend({

      onStatusChange: setBackendStatus,

      onConfig: (message) => {
        setSensors(message.sensors || []);
        setSensorTypes(message.sensorTypes || []);
      },

      onReading: (message) => {
        setReadings(old => ({
          ...old,
          [message.id]: message
        }));

        setHistory(old => {
          const points = old[message.id] || [];
          return {
            ...old,
            [message.id]: [
              ...points.slice(-(MAX_GRAPH_POINTS - 1)),
              message
            ]
          };
        });
      },

      onAddSensorResult: (message) => {
        setAddResult({
          success: message.success,
          message: message.message
        });
      }

    });

    connectionRef.current = connection;

    // Cleanup when the React app closes/unmounts.
    return () => {
      connection.disconnect();
    };

  }, []);

  // ==========================================================
  // SEND ADD SENSOR COMMAND TO THE BACKEND
  // ==========================================================

  function sendAddSensor(sensor) {
    setAddResult(null);

    const connection = connectionRef.current;
    const result = connection ? connection.sendAddSensor(sensor) : null;

    // The service reports failures (e.g. not connected) right
    // away. Successes are confirmed later by an
    // "add_sensor_result" message from the backend.
    if (result && !result.success) {
      setAddResult(result);
    }
  }

  // ==========================================================
  // OPEN SENSOR TAB
  // ==========================================================

  function openSensor(id) {
    if (!openTabs.includes(id)) {
      setOpenTabs([...openTabs, id]);
    }
    setActiveTab(id);
  }

  // ==========================================================
  // CLOSE SENSOR TAB
  // ==========================================================

  function closeTab(event, id) {
    event.stopPropagation();

    setOpenTabs(openTabs.filter(tab => tab !== id));

    if (activeTab === id) {
      setActiveTab("list");
    }
  }

  const selected = sensors.find(sensor => sensor.id === activeTab);

  // ==========================================================
  // UI
  // ==========================================================

  return (
    <main className="app-shell">

      <Header backendStatus={backendStatus} />

      <div className="workspace">

        <Sidebar
          sensors={sensors}
          readings={readings}
          now={now}
          openTabs={openTabs}
          activeTab={activeTab}
          onSelectTab={setActiveTab}
          onCloseTab={closeTab}
        />

        <section className="content">

          {activeTab === "buildings" && (
            <BuildingsPage
              sensors={sensors}
              readings={readings}
              now={now}
            />
          )}

          {activeTab === "list" && (
            <SensorListPage
              sensors={sensors}
              readings={readings}
              now={now}
              onOpen={openSensor}
            />
          )}

          {activeTab === "add" && (
            <AddSensorPage
              sensorTypes={sensorTypes}
              onSubmit={sendAddSensor}
              result={addResult}
            />
          )}

          {!["buildings", "list", "add"].includes(activeTab) && selected && (
            <SensorDetailPage
              sensor={selected}
              reading={readings[selected.id]}
              history={history[selected.id] || []}
              now={now}
            />
          )}

        </section>

      </div>

    </main>
  );
}
