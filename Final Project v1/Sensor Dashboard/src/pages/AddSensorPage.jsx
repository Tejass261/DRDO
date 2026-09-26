import { useState } from "react";

// ============================================================
// ADD SENSOR PAGE
// ============================================================
//
// A form that sends an "add_sensor" command through the
// WebSocket service (via the onSubmit callback from App.jsx).
// The frontend never edits Config.txt directly - the backend
// validates the data and updates Config.txt itself.
// ============================================================

export default function AddSensorPage({ sensorTypes, onSubmit, result }) {

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

    if (!Number.isInteger(port) || port < 1 || port > 65535) {
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

      <form className="add-form" onSubmit={handleSubmit}>

        <label>
          Sensor ID
          <input
            value={form.id}
            onChange={event => update("id", event.target.value)}
            placeholder="bio-perimeter-01"
          />
        </label>

        <div className="two-fields">

          <label>
            Sensor type
            <select
              value={form.type}
              onChange={event => update("type", event.target.value)}
            >
              <option value="">Select type…</option>
              {sensorTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </label>

          <label>
            Location
            <input
              value={form.location}
              onChange={event => update("location", event.target.value)}
              placeholder="main-gate"
            />
          </label>

        </div>

        <div className="two-fields">

          <label>
            IP address
            <input
              value={form.ip}
              onChange={event => update("ip", event.target.value)}
            />
          </label>

          <label>
            Port
            <input
              value={form.port}
              onChange={event => update("port", event.target.value)}
              placeholder="5060"
            />
          </label>

        </div>

        <label>
          Request string
          <input
            value={form.request}
            onChange={event => update("request", event.target.value)}
            placeholder="send bio-perimeter-01"
          />
        </label>

        <label>
          Request interval (seconds)
          <input
            value={form.request_interval}
            onChange={event => update("request_interval", event.target.value)}
          />
        </label>

        {error && <p className="form-error">{error}</p>}

        {result && (
          <p className={result.success ? "form-success" : "form-error"}>
            {result.message}
          </p>
        )}

        <button className="save-button" type="submit">
          Add sensor
        </button>

      </form>

    </section>
  );
}
