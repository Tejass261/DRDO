import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

const fallbackSensors = [
  { id: "bio-main-gate-01", type: "bio", location: "main-gate", ip: "127.0.0.1", port: 5050, topic: "sensors/main-gate/bio/bio-main-gate-01" },
  { id: "chem-main-gate-01", type: "chem", location: "main-gate", ip: "127.0.0.1", port: 5051, topic: "sensors/main-gate/chem/chem-main-gate-01" },
  { id: "bio-director-office-01", type: "bio", location: "director-office", ip: "127.0.0.1", port: 5052, topic: "sensors/director-office/bio/bio-director-office-01" },
  { id: "chem-director-office-01", type: "chem", location: "director-office", ip: "127.0.0.1", port: 5053, topic: "sensors/director-office/chem/chem-director-office-01" }
];

// Use Electron IPC when available. The fallback keeps the interface visible
// even when the app is accidentally opened as an ordinary browser page.
let sensorAPI;
let usingElectron = false;

if (window.sensorAPI) {
  sensorAPI = window.sensorAPI;
  usingElectron = true;
} else if (typeof window.require === "function") {
  const { ipcRenderer } = window.require("electron");
  sensorAPI = {
    getSensors: () => ipcRenderer.invoke("sensors:get"),
    getSensorTypes: () => ipcRenderer.invoke("types:get"),
    addSensor: (sensor) => ipcRenderer.invoke("sensors:add", sensor),
    onReading: (callback) => ipcRenderer.on("sensor:reading", (_, reading) => callback(reading)),
    onBrokerStatus: (callback) => ipcRenderer.on("broker:status", (_, status) => callback(status))
  };
  usingElectron = true;
} else {
  sensorAPI = {
    getSensors: async () => fallbackSensors,
    getSensorTypes: async () => ["bio", "chem", "fcad"],
    addSensor: async () => { throw new Error("Open this dashboard through Electron to add a sensor."); },
    onReading: () => {},
    onBrokerStatus: () => {}
  };
}

function getReadingValues(reading) {
  if (!reading) return [];
  return reading.payload.split(",");
}

function getIndicator(reading) {
  if (!reading) return "Waiting";
  const seconds = (Date.now() - new Date(reading.receivedAt).getTime()) / 1000;
  return seconds < 10 ? "Online" : "No recent data";
}

function DetailView({ sensor, reading }) {
  const values = getReadingValues(reading);
  const labels = {
    bio: ["Sample type", "Small particle count", "Large particle count", "Small biological load", "Large biological load", "Alarm"],
    chem: ["Date", "Time", "G value", "H value", "Mode"],
    fcad: ["Sensor name", "G value", "H value", "Atmospheric pressure G", "Atmospheric pressure H", "G pressure", "H pressure", "Battery", "Mode"]
  };

  return (
    <section className="detail-view">
      <p className="eyebrow">{sensor.location.replaceAll("-", " ")} · {sensor.type}</p>
      <h1>{sensor.id}</h1>
      <div className="status-line">
        <span className={`status ${getIndicator(reading) === "Online" ? "online" : "waiting"}`}>{getIndicator(reading)}</span>
        <span>{reading ? `Last received: ${new Date(reading.receivedAt).toLocaleTimeString()}` : "No reading received yet"}</span>
      </div>

      <div className="detail-grid">
        <div><span>Location</span><strong>{sensor.location}</strong></div>
        <div><span>Type</span><strong>{sensor.type}</strong></div>
        <div><span>IP address</span><strong>{sensor.ip}:{sensor.port}</strong></div>
        <div><span>MQTT topic</span><strong className="topic">{sensor.topic}</strong></div>
      </div>

      <h2>Latest reading</h2>
      {reading ? (
        <div className="reading-grid">
          {values.map((value, index) => <div key={index}><span>{labels[sensor.type]?.[index] || `Value ${index + 1}`}</span><strong>{value}</strong></div>)}
        </div>
      ) : <p className="empty-copy">Start the sensor and its Python converter to see live data here.</p>}
    </section>
  );
}

function AddSensor({ types, onClose, onSave }) {
  const [form, setForm] = useState({ id: "", type: types[0] || "bio", location: "", ip: "127.0.0.1", port: "", request: "", request_interval: "3" });
  const [error, setError] = useState("");

  function change(event) {
    setForm({ ...form, [event.target.name]: event.target.value });
  }

  async function submit(event) {
    event.preventDefault();
    try {
      await onSave(form);
      onClose();
    } catch (problem) {
      setError(problem.message);
    }
  }

  return (
    <div className="modal-backdrop">
      <form className="modal" onSubmit={submit}>
        <div className="modal-heading"><h2>Add location sensor</h2><button type="button" className="icon-button" onClick={onClose}>×</button></div>
        <p>This adds one physical sensor to the Python <code>Config.txt</code> file.</p>
        <label>Sensor ID<input name="id" required placeholder="bio-admin-office-01" value={form.id} onChange={change} /></label>
        <label>Sensor type<select name="type" value={form.type} onChange={change}>{types.map(type => <option key={type}>{type}</option>)}</select></label>
        <label>Location<input name="location" required placeholder="admin office" value={form.location} onChange={change} /></label>
        <div className="two-fields"><label>IP address<input name="ip" required value={form.ip} onChange={change} /></label><label>Port<input name="port" required type="number" value={form.port} onChange={change} /></label></div>
        <label>Request text<input name="request" required placeholder="send bio-admin-office-01" value={form.request} onChange={change} /></label>
        <label>Request interval, seconds<input name="request_interval" type="number" min="1" value={form.request_interval} onChange={change} /></label>
        {error && <p className="form-error">{error}</p>}
        <button className="save-button">Add sensor</button>
      </form>
    </div>
  );
}

function App() {
  const [sensors, setSensors] = useState([]);
  const [sensorTypes, setSensorTypes] = useState([]);
  const [readings, setReadings] = useState({});
  const [openTabs, setOpenTabs] = useState([]);
  const [activeTab, setActiveTab] = useState("overview");
  const [brokerStatus, setBrokerStatus] = useState("connecting");
  const [showAdd, setShowAdd] = useState(false);

  useEffect(() => {
    sensorAPI.getSensors().then(setSensors).catch(() => setSensors(fallbackSensors));
    sensorAPI.getSensorTypes().then(setSensorTypes).catch(() => setSensorTypes(["bio", "chem", "fcad"]));
    sensorAPI.onReading((reading) => setReadings(old => ({ ...old, [reading.id]: reading })));
    sensorAPI.onBrokerStatus(setBrokerStatus);
  }, []);

  function openSensor(id) {
    if (!openTabs.includes(id)) setOpenTabs([...openTabs, id]);
    setActiveTab(id);
  }

  function closeTab(event, id) {
    event.stopPropagation();
    const remaining = openTabs.filter(tab => tab !== id);
    setOpenTabs(remaining);
    if (activeTab === id) setActiveTab("overview");
  }

  async function addSensor(form) {
    const sensor = await sensorAPI.addSensor(form);
    setSensors([...sensors, sensor]);
    openSensor(sensor.id);
  }

  const selected = sensors.find(sensor => sensor.id === activeTab);
  return (
    <main className="app-shell">
      <header><div><span className="logo-dot"></span><strong>Sensor Display Environment</strong></div><span className={`broker ${brokerStatus}`}>{usingElectron ? `Broker: ${brokerStatus}` : "Preview mode"}</span></header>
      <div className="workspace">
        <aside className="sidebar">
          <button className={`side-tab overview-tab ${activeTab === "overview" ? "active" : ""}`} onClick={() => setActiveTab("overview")}><span>All sensors</span><small>{sensors.length} configured</small></button>
          {openTabs.map(id => {
            const sensor = sensors.find(item => item.id === id);
            return sensor && <button className={`side-tab ${activeTab === id ? "active" : ""}`} key={id} onClick={() => setActiveTab(id)}><span>{sensor.id}</span><small>{sensor.location}</small><b onClick={(event) => closeTab(event, id)}>×</b></button>;
          })}
        </aside>

        <section className="content">
          {activeTab === "overview" ? <>
            <div className="page-heading"><div><p className="eyebrow">LIVE MONITORING</p><h1>All configured sensors</h1></div><span className="count-pill">{sensors.length} sensors</span></div>
            <div className="sensor-list">
              {sensors.map(sensor => <button className="sensor-row" key={sensor.id} onClick={() => openSensor(sensor.id)}><div><strong>{sensor.id}</strong><span>{sensor.type}</span></div><span>{sensor.location.replaceAll("-", " ")}</span><span className={`status ${getIndicator(readings[sensor.id]) === "Online" ? "online" : "waiting"}`}>{getIndicator(readings[sensor.id])}</span></button>)}
            </div>
          </> : <DetailView sensor={selected} reading={readings[selected?.id]} />}
          <button className="add-button" onClick={() => setShowAdd(true)}><span>+</span> Add sensor</button>
        </section>
      </div>
      {showAdd && <AddSensor types={sensorTypes} onClose={() => setShowAdd(false)} onSave={addSensor} />}
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
