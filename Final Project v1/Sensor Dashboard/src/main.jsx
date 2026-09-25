import { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";


// ============================================================
// BACKEND WEBSOCKET ADDRESS
// ============================================================

const WEBSOCKET_URL = "ws://127.0.0.1:8765";

// A sensor is "online" if its last reading is newer than
// this many milliseconds. Sensors send data every ~3 s,
// so 10 s gives room for a delayed message or two.
const ONLINE_TIMEOUT_MS = 10000;

// How many recent readings each graph keeps in memory.
const MAX_GRAPH_POINTS = 60;

// How long to wait (ms) before trying to reconnect when the
// backend WebSocket is not available.
const RECONNECT_DELAY_MS = 2000;


// ============================================================
// DISPLAY LABELS
// ============================================================
//
// These are only UI labels.
// The actual parsing of the sensor payload happens in Python.
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
// Which already-parsed backend values each sensor type
// plots on its live graph. The frontend never parses raw
// payloads — it only reads these fields from message.data.
// ============================================================

const graphConfig = {

  bio: [
    {
      key: "smallParticleCount",
      label: "Small particle count",
      color: "#2868d7"
    }
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
// STATUS HELPERS (LED LOGIC)
// ============================================================
//
// GREY = no recent data (offline)
// RED  = online + alarm active
// GREEN = online + no alarm
// ============================================================

function isOnline(reading, now) {
  if (!reading) {
    return false;
  }
  return (
    now - new Date(reading.receivedAt).getTime() <
    ONLINE_TIMEOUT_MS
  );
}

function sensorStatus(reading, now) {
  if (!isOnline(reading, now)) {
    return "grey";
  }
  return reading.alarm ? "red" : "green";
}

function statusText(status) {
  if (status === "green") return "Online";
  if (status === "red") return "Alarm";
  return "Offline";
}

// Building status from its sensors (priority order):
//   RED   = at least one ONLINE sensor has an active alarm
//   GREY  = no sensor in the building is online
//   GREEN = at least one sensor online, none in alarm
function buildingStatus(sensors, readings, now) {
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

function buildingText(status) {
  if (status === "green") return "Online / Normal";
  if (status === "red") return "Alarm";
  return "Offline";
}


// ============================================================
// STATUS LED
// ============================================================

function Led({ color }) {
  return (
    <span
      className={`led ${color}`}
      aria-label={statusText(color)}
    />
  );
}


// ============================================================
// LIVE GRAPH (SVG line chart, no libraries)
// ============================================================
//
// series = [
//   { label, color, points: [number, number, ...] }
// ]
//
// The newest point is the LAST item in each points array,
// so the newest value is drawn on the RIGHT side.
// ============================================================

function LiveGraph({ series, yLabel }) {

  // ---- Collect all values to scale the Y axis ----

  const allValues = [];

  for (const line of series) {
    for (const value of line.points) {
      if (Number.isFinite(value)) {
        allValues.push(value);
      }
    }
  }

  // Nothing to draw yet.
  if (allValues.length === 0) {
    return (
      <div className="graph-empty">
        Waiting for data to draw the graph…
      </div>
    );
  }

  let min = Math.min(...allValues);
  let max = Math.max(...allValues);

  // If every value is identical, give the axis some height
  // so the line doesn't fill the whole box.
  if (min === max) {
    min = min - 1;
    max = max + 1;
  }

  // ---- SVG drawing area ----

  const WIDTH = 600;
  const HEIGHT = 210;
  const PAD_LEFT = 48;
  const PAD_RIGHT = 12;
  const PAD_TOP = 12;
  const PAD_BOTTOM = 24;

  const innerWidth = WIDTH - PAD_LEFT - PAD_RIGHT;
  const innerHeight = HEIGHT - PAD_TOP - PAD_BOTTOM;

  const maxPoints = Math.max(
    ...series.map(line => line.points.length),
    2
  );

  function xFor(index) {
    return (
      PAD_LEFT +
      (index / (maxPoints - 1)) * innerWidth
    );
  }

  function yFor(value) {
    return (
      PAD_TOP +
      innerHeight -
      ((value - min) / (max - min)) * innerHeight
    );
  }

  // ---- Y axis grid lines ----

  const gridLines = [];

  for (let step = 0; step <= 4; step++) {
    const fraction = step / 4;
    const value = min + fraction * (max - min);
    const y = yFor(value);
    gridLines.push(
      <g key={step}>
        <line
          x1={PAD_LEFT}
          y1={y}
          x2={WIDTH - PAD_RIGHT}
          y2={y}
          className="graph-grid"
        />
        <text
          x={PAD_LEFT - 7}
          y={y + 4}
          textAnchor="end"
          className="graph-axis-text"
        >
          {value.toFixed(1)}
        </text>
      </g>
    );
  }

  // ---- Latest value per line (for the legend) ----

  const latestValues = series.map(line => {
    const numbers = line.points.filter(Number.isFinite);
    return numbers[numbers.length - 1];
  });

  return (
    <div className="graph-box">

      <div className="graph-legend">
        {series.map((line, index) => (
          <span key={line.key || line.label}>
            <i style={{ background: line.color }} />
            {line.label}
            {Number.isFinite(latestValues[index]) && (
              <b>: {latestValues[index]}</b>
            )}
          </span>
        ))}
      </div>

      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        className="live-graph"
        preserveAspectRatio="none"
      >
        {gridLines}

        <text
          x={10}
          y={HEIGHT / 2}
          textAnchor="middle"
          className="graph-axis-text"
          transform={`rotate(-90 10 ${HEIGHT / 2})`}
        >
          {yLabel}
        </text>

        {series.map(line => {
          const points = line.points
            .map((value, index) => {
              if (!Number.isFinite(value)) {
                return null;
              }
              return `${xFor(index)},${yFor(value)}`;
            })
            .filter(Boolean)
            .join(" ");

          if (!points) {
            return null;
          }

          return (
            <polyline
              key={line.key || line.label}
              points={points}
              fill="none"
              stroke={line.color}
              strokeWidth="2"
              vectorEffect="non-scaling-stroke"
            />
          );
        })}
      </svg>

    </div>
  );
}


// ============================================================
// BUILDINGS OVERVIEW VIEW
// ============================================================

function BuildingsView({ sensors, readings, now }) {

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
        <span className="count-pill">
          {locations.length} locations
        </span>
      </div>

      <div className="building-grid">

        {locations.map(location => {

          const buildingSensors =
            byLocation[location];

          const status = buildingStatus(
            buildingSensors,
            readings,
            now
          );

          return (
            <div
              className="building-card"
              key={location}
            >

              <div className="building-led-row">
                <Led color={status} />
              </div>

              <h2>
                {location.replaceAll("-", " ")}
              </h2>

              <p className={`building-state ${status}`}>
                {buildingText(status)}
              </p>

              <p className="building-count">
                {buildingSensors.length} sensor
                {buildingSensors.length !== 1
                  ? "s"
                  : ""}
              </p>

              <ul className="building-sensors">
                {buildingSensors.map(sensor => (
                  <li key={sensor.id}>
                    <Led
                      color={sensorStatus(
                        readings[sensor.id],
                        now
                      )}
                    />
                    {sensor.id}
                  </li>
                ))}
              </ul>

            </div>
          );
        })}

      </div>

    </section>
  );
}


// ============================================================
// SENSOR LIST VIEW
// ============================================================

function SensorListView({ sensors, readings, now, onOpen }) {

  return (
    <section>

      <div className="page-heading">
        <div>
          <p className="eyebrow">LIVE MONITORING</p>
          <h1>All configured sensors</h1>
        </div>
        <span className="count-pill">
          {sensors.length} sensors
        </span>
      </div>

      <div className="sensor-list">

        {sensors.map(sensor => {

          const reading = readings[sensor.id];
          const status = sensorStatus(reading, now);

          return (
            <button
              className="sensor-row"
              key={sensor.id}
              onClick={() => onOpen(sensor.id)}
            >

              <span className="row-status">
                <Led color={status} />
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
                {reading
                  ? new Date(
                      reading.receivedAt
                    ).toLocaleTimeString()
                  : "no data yet"}
              </span>

            </button>
          );
        })}

      </div>

    </section>
  );
}


// ============================================================
// DETAIL VIEW (single sensor tab)
// ============================================================
//
// Layout per request:
//   - Sensor name + status LED at the top
//   - Reading boxes below (empty boxes with "—" when no
//     data has been received yet)
//   - Live graph at the bottom
// No scrolling metadata blocks on top.
// ============================================================

function DetailView({ sensor, reading, history, now }) {

  const status = sensorStatus(reading, now);
  const typeLabels = labels[sensor.type] || {};
  const config = graphConfig[sensor.type];

  // Build the graph series from the backend-parsed values
  // that are already inside each reading's `data` object.
  const series = config
    ? config.map(line => ({
        ...line,
        points: history.map(item =>
          Number(item.data?.[line.key])
        )
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
          <Led color={status} />
          {statusText(status)}
        </span>

      </div>

      <p className="detail-subline">
        {sensor.ip}:{sensor.port}
        {" · "}
        <span className="topic">{sensor.topic}</span>
        {" · "}
        {reading
          ? `Last received: ${new Date(
              reading.receivedAt
            ).toLocaleTimeString()}`
          : "No reading received yet"}
      </p>


      {/* -------- Reading boxes -------- */}

      <div className="reading-grid">

        {Object.entries(typeLabels).map(
          ([key, text]) => (

            <div key={key}>

              <span>{text}</span>

              <strong
                className={
                  reading ? "" : "reading-empty"
                }
              >
                {reading
                  ? String(reading.data?.[key] ?? "—")
                  : "—"}
              </strong>

            </div>

          )
        )}

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
          <LiveGraph
            series={series}
            yLabel={
              config.length === 1
                ? config[0].label
                : "Value"
            }
          />
        </>
      )}

    </section>
  );
}


// ============================================================
// ADD SENSOR VIEW
// ============================================================

function AddSensorView({ sensorTypes, onSubmit, result }) {

  const [form, setForm] = useState({
    id: "",
    type: "",
    location: "",
    ip: "127.0.0.1",
    port: "",
    request: "",
    request_interval: "3"
  });

  const [error, setError] = useState("");

  function update(field, value) {
    setForm(old => ({ ...old, [field]: value }));
  }

  function handleSubmit(event) {
    event.preventDefault();

    // ---- Simple frontend validation ----

    if (
      !form.id.trim() ||
      !form.type ||
      !form.location.trim() ||
      !form.ip.trim() ||
      !form.request.trim()
    ) {
      setError("Please fill in every field.");
      return;
    }

    const port = Number(form.port);

    if (
      !Number.isInteger(port) ||
      port < 1 ||
      port > 65535
    ) {
      setError("Port must be a number between 1 and 65535.");
      return;
    }

    const interval = Number(form.request_interval);

    if (!Number.isFinite(interval) || interval <= 0) {
      setError("Request interval must be a number greater than 0.");
      return;
    }

    setError("");

    onSubmit({
      id: form.id.trim(),
      type: form.type,
      location: form.location.trim(),
      ip: form.ip.trim(),
      port: port,
      request: form.request.trim(),
      request_interval: interval
    });
  }

  return (
    <section className="add-view">

      <div className="page-heading">
        <div>
          <p className="eyebrow">CONFIGURATION</p>
          <h1>Add sensor</h1>
        </div>
      </div>

      <p className="empty-copy">
        Add one individual sensor. The sensor type must be one
        of the types already defined in Config.txt. The backend
        validates the information and updates Config.txt.
      </p>

      <form
        className="add-form"
        onSubmit={handleSubmit}
      >

        <label>
          Sensor ID
          <input
            value={form.id}
            onChange={event =>
              update("id", event.target.value)
            }
            placeholder="bio-perimeter-01"
          />
        </label>

        <div className="two-fields">

          <label>
            Sensor type
            <select
              value={form.type}
              onChange={event =>
                update("type", event.target.value)
              }
            >
              <option value="">
                Select type…
              </option>
              {sensorTypes.map(type => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </label>

          <label>
            Location
            <input
              value={form.location}
              onChange={event =>
                update("location", event.target.value)
              }
              placeholder="main-gate"
            />
          </label>

        </div>

        <div className="two-fields">

          <label>
            IP address
            <input
              value={form.ip}
              onChange={event =>
                update("ip", event.target.value)
              }
            />
          </label>

          <label>
            Port
            <input
              value={form.port}
              onChange={event =>
                update("port", event.target.value)
              }
              placeholder="5060"
            />
          </label>

        </div>

        <label>
          Request string
          <input
            value={form.request}
            onChange={event =>
              update("request", event.target.value)
            }
            placeholder="send bio-perimeter-01"
          />
        </label>

        <label>
          Request interval (seconds)
          <input
            value={form.request_interval}
            onChange={event =>
              update(
                "request_interval",
                event.target.value
              )
            }
          />
        </label>

        {error && (
          <p className="form-error">{error}</p>
        )}

        {result && (
          <p
            className={
              result.success
                ? "form-success"
                : "form-error"
            }
          >
            {result.message}
          </p>
        )}

        <button
          className="save-button"
          type="submit"
        >
          Add sensor
        </button>

      </form>

    </section>
  );
}


// ============================================================
// MAIN APPLICATION
// ============================================================

function App() {

  const [
    sensors,
    setSensors
  ] = useState([]);


  const [
    sensorTypes,
    setSensorTypes
  ] = useState([]);


  // Latest reading per sensor:
  // { sensorId: readingMessage }
  const [
    readings,
    setReadings
  ] = useState({});


  // Recent readings per sensor (for the graphs):
  // { sensorId: [readingMessage, ...] } max MAX_GRAPH_POINTS
  const [
    history,
    setHistory
  ] = useState({});


  const [
    openTabs,
    setOpenTabs
  ] = useState([]);


  // "buildings" | "list" | "add" | <sensorId>
  const [
    activeTab,
    setActiveTab
  ] = useState("buildings");


  const [
    backendStatus,
    setBackendStatus
  ] = useState("connecting");


  const [
    addResult,
    setAddResult
  ] = useState(null);


  // Reference to the live WebSocket so the Add Sensor form
  // can send commands through it.
  const socketRef = useRef(null);


  // Current time, updated once per second so that the
  // Online / Offline LEDs refresh automatically even when
  // no new data arrives.
  const [
    now,
    setNow
  ] = useState(Date.now());


  useEffect(() => {

    const timer = setInterval(() => {
      setNow(Date.now());
    }, 1000);

    return () => clearInterval(timer);

  }, []);


  // ==========================================================
  // WEBSOCKET CONNECTION (with automatic reconnect)
  // ==========================================================

  useEffect(() => {

    let socket = null;
    let reconnectTimer = null;
    let closedByUs = false;


    function handleMessage(event) {

      try {

        const message = JSON.parse(event.data);


        // ----------------------------------------------------
        // Backend sends sensor configuration.
        // ----------------------------------------------------

        if (message.event === "config") {

          setSensors(message.sensors || []);

          setSensorTypes(message.sensorTypes || []);

          return;
        }


        // ----------------------------------------------------
        // Backend sends a sensor reading.
        // ----------------------------------------------------

        if (message.event === "reading") {

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

          return;
        }


        // ----------------------------------------------------
        // Result of an "add sensor" command.
        // ----------------------------------------------------

        if (message.event === "add_sensor_result") {

          setAddResult({
            success: message.success,
            message: message.message
          });

          return;
        }

      }

      catch (error) {

        console.error(
          "[WebSocket] Invalid message:",
          error
        );

      }

    }


    function connect() {

      console.log(
        `[WebSocket] Connecting to ${WEBSOCKET_URL}`
      );

      setBackendStatus("connecting");

      socket = new WebSocket(WEBSOCKET_URL);
      socketRef.current = socket;


      socket.onopen = () => {

        console.log(
          "[WebSocket] Connected to backend."
        );

        setBackendStatus("connected");

      };


      socket.onmessage = handleMessage;


      socket.onclose = () => {

        if (closedByUs) {
          return;
        }

        console.log(
          "[WebSocket] Connection lost. " +
          "Retrying soon…"
        );

        setBackendStatus("reconnecting");

        // Try again after a short pause.
        reconnectTimer = setTimeout(
          connect,
          RECONNECT_DELAY_MS
        );

      };


      socket.onerror = () => {

        // Close the broken socket so onclose fires and
        // the reconnect timer starts.
        socket.close();

      };

    }


    connect();


    // --------------------------------------------------------
    // CLEANUP when the React app closes/unmounts.
    // --------------------------------------------------------

    return () => {

      closedByUs = true;

      clearTimeout(reconnectTimer);

      if (socket) {
        socket.close();
      }

    };

  }, []);


  // ==========================================================
  // SEND ADD SENSOR COMMAND TO THE BACKEND
  // ==========================================================

  function sendAddSensor(sensor) {

    setAddResult(null);

    const socket = socketRef.current;

    if (
      !socket ||
      socket.readyState !== WebSocket.OPEN
    ) {
      setAddResult({
        success: false,
        message:
          "Backend is not connected. " +
          "Cannot add sensor right now."
      });
      return;
    }

    socket.send(
      JSON.stringify({
        event: "add_sensor",
        sensor: sensor
      })
    );

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

    setOpenTabs(
      openTabs.filter(tab => tab !== id)
    );

    if (activeTab === id) {
      setActiveTab("list");
    }

  }


  const selected =
    sensors.find(
      sensor => sensor.id === activeTab
    );


  // ==========================================================
  // UI
  // ==========================================================

  return (

    <main className="app-shell">


      {/* ================================================== */}
      {/* HEADER */}
      {/* ================================================== */}

      <header>

        <div>

          <span className="logo-dot" />

          <strong>
            Sensor Display Environment
          </strong>

        </div>


        <span
          className={`broker ${backendStatus}`}
        >

          Backend: {backendStatus}

        </span>

      </header>


      <div className="workspace">


        {/* ================================================= */}
        {/* SIDEBAR */}
        {/* ================================================= */}

        <aside className="sidebar">


          {/* -------- Permanent: Buildings tab -------- */}

          <button
            className={
              `side-tab permanent-tab ${
                activeTab === "buildings"
                  ? "active"
                  : ""
              }`
            }
            onClick={() =>
              setActiveTab("buildings")
            }
          >

            <span>Buildings</span>

            <small>Overview</small>

          </button>


          {/* -------- Permanent: List tab -------- */}

          <button
            className={
              `side-tab permanent-tab ${
                activeTab === "list"
                  ? "active"
                  : ""
              }`
            }
            onClick={() =>
              setActiveTab("list")
            }
          >

            <span>All sensors</span>

            <small>
              {sensors.length} configured
            </small>

          </button>


          {/* -------- Closable sensor tabs -------- */}

          {openTabs.map(id => {

            const sensor =
              sensors.find(
                item => item.id === id
              );

            if (!sensor) {
              return null;
            }

            const status = sensorStatus(
              readings[id],
              now
            );

            return (

              <button
                className={
                  `side-tab ${
                    activeTab === id
                      ? "active"
                      : ""
                  }`
                }
                key={id}
                onClick={() =>
                  setActiveTab(id)
                }
              >

                <span>
                  <Led color={status} />
                  {sensor.id}
                </span>

                <small>
                  {sensor.location}
                </small>


                <b
                  onClick={event =>
                    closeTab(event, id)
                  }
                >
                  ×
                </b>

              </button>

            );
          })}


          {/* -------- Add sensor (permanent entry) -------- */}

          <button
            className={
              `side-tab add-tab ${
                activeTab === "add"
                  ? "active"
                  : ""
              }`
            }
            onClick={() =>
              setActiveTab("add")
            }
          >
            <span>＋ Add sensor</span>
          </button>


        </aside>


        {/* ================================================= */}
        {/* CONTENT */}
        {/* ================================================= */}

        <section className="content">


          {/* -------- Buildings overview -------- */}

          {activeTab === "buildings" && (
            <BuildingsView
              sensors={sensors}
              readings={readings}
              now={now}
            />
          )}


          {/* -------- Sensor list -------- */}

          {activeTab === "list" && (
            <SensorListView
              sensors={sensors}
              readings={readings}
              now={now}
              onOpen={openSensor}
            />
          )}


          {/* -------- Add sensor -------- */}

          {activeTab === "add" && (
            <AddSensorView
              sensorTypes={sensorTypes}
              onSubmit={sendAddSensor}
              result={addResult}
            />
          )}


          {/* -------- Individual sensor tab -------- */}

          {!["buildings", "list", "add"].includes(
            activeTab
          ) &&
            selected && (
              <DetailView
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


// ============================================================
// START REACT
// ============================================================

createRoot(
  document.getElementById("root")
).render(
  <App />
);
