import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";


// ============================================================
// BACKEND WEBSOCKET ADDRESS
// ============================================================

const WEBSOCKET_URL = "ws://127.0.0.1:8765";


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
// SENSOR ONLINE STATUS
// ============================================================

function getIndicator(reading) {

  if (!reading) {
    return "Waiting";
  }

  const seconds =
    (Date.now() -
      new Date(reading.receivedAt).getTime()) /
    1000;

  return seconds < 10
    ? "Online"
    : "No recent data";
}


// ============================================================
// DETAIL VIEW
// ============================================================

function DetailView({ sensor, reading }) {

  return (

    <section className="detail-view">

      <p className="eyebrow">
        {sensor.location.replaceAll("-", " ")}
        {" · "}
        {sensor.type}
      </p>

      <h1>{sensor.id}</h1>


      <div className="status-line">

        <span
          className={
            `status ${
              getIndicator(reading) === "Online"
                ? "online"
                : "waiting"
            }`
          }
        >
          {getIndicator(reading)}
        </span>

        <span>

          {reading
            ? `Last received: ${
                new Date(
                  reading.receivedAt
                ).toLocaleTimeString()
              }`
            : "No reading received yet"
          }

        </span>

      </div>


      <div className="detail-grid">

        <div>

          <span>Location</span>

          <strong>
            {sensor.location}
          </strong>

        </div>


        <div>

          <span>Type</span>

          <strong>
            {sensor.type}
          </strong>

        </div>


        <div>

          <span>IP address</span>

          <strong>
            {sensor.ip}:{sensor.port}
          </strong>

        </div>


        <div>

          <span>MQTT topic</span>

          <strong className="topic">

            {sensor.topic}

          </strong>

        </div>

      </div>


      <h2>
        Latest reading
      </h2>


      {reading ? (

        <div className="reading-grid">

          {Object.entries(
            reading.data || {}
          ).map(
            ([key, value]) => (

              <div key={key}>

                <span>

                  {labels[
                    sensor.type
                  ]?.[key] || key}

                </span>

                <strong>
                  {String(value)}
                </strong>

              </div>

            )
          )}

        </div>

      ) : (

        <p className="empty-copy">

          Start the sensor and its Python
          converter to see live data here.

        </p>

      )}

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


  const [
    readings,
    setReadings
  ] = useState({});


  const [
    openTabs,
    setOpenTabs
  ] = useState([]);


  const [
    activeTab,
    setActiveTab
  ] = useState("overview");


  const [
    backendStatus,
    setBackendStatus
  ] = useState("connecting");


  // ==========================================================
  // WEBSOCKET CONNECTION
  // ==========================================================

  useEffect(() => {

    console.log(
      `[WebSocket] Connecting to ${WEBSOCKET_URL}`
    );


    const socket =
      new WebSocket(
        WEBSOCKET_URL
      );


    // --------------------------------------------------------
    // CONNECTION OPEN
    // --------------------------------------------------------

    socket.onopen = () => {

      console.log(
        "[WebSocket] Connected to backend."
      );

      setBackendStatus(
        "connected"
      );

    };


    // --------------------------------------------------------
    // MESSAGE RECEIVED
    // --------------------------------------------------------

    socket.onmessage = (
      event
    ) => {

      try {

        const message =
          JSON.parse(
            event.data
          );


        // ----------------------------------------------------
        // Backend sends sensor configuration.
        // ----------------------------------------------------

        if (
          message.event ===
          "config"
        ) {

          setSensors(
            message.sensors || []
          );

          setSensorTypes(
            message.sensorTypes || []
          );

          return;
        }


        // ----------------------------------------------------
        // Backend sends a sensor reading.
        // ----------------------------------------------------

        if (
          message.event ===
          "reading"
        ) {

          setReadings(
            old => ({
              ...old,
              [message.id]:
                message
            })
          );

          return;
        }

      }

      catch (error) {

        console.error(
          "[WebSocket] Invalid message:",
          error
        );

      }

    };


    // --------------------------------------------------------
    // CONNECTION CLOSED
    // --------------------------------------------------------

    socket.onclose = () => {

      console.log(
        "[WebSocket] Backend disconnected."
      );

      setBackendStatus(
        "offline"
      );

    };


    // --------------------------------------------------------
    // CONNECTION ERROR
    // --------------------------------------------------------

    socket.onerror = (
      error
    ) => {

      console.error(
        "[WebSocket] Connection error:",
        error
      );

      setBackendStatus(
        "error"
      );

    };


    // --------------------------------------------------------
    // CLEANUP
    // --------------------------------------------------------

    return () => {

      socket.close();

    };

  }, []);


  // ==========================================================
  // OPEN SENSOR TAB
  // ==========================================================

  function openSensor(id) {

    if (
      !openTabs.includes(id)
    ) {

      setOpenTabs(
        [
          ...openTabs,
          id
        ]
      );

    }

    setActiveTab(id);
  }


  // ==========================================================
  // CLOSE SENSOR TAB
  // ==========================================================

  function closeTab(
    event,
    id
  ) {

    event.stopPropagation();


    const remaining =
      openTabs.filter(
        tab => tab !== id
      );


    setOpenTabs(
      remaining
    );


    if (
      activeTab === id
    ) {

      setActiveTab(
        "overview"
      );

    }

  }


  const selected =
    sensors.find(
      sensor =>
        sensor.id ===
        activeTab
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

          <span
            className="logo-dot"
          />

          <strong>
            Sensor Display Environment
          </strong>

        </div>


        <span
          className={
            `broker ${backendStatus}`
          }
        >

          Backend: {backendStatus}

        </span>

      </header>


      <div className="workspace">


        {/* ================================================= */}
        {/* SIDEBAR */}
        {/* ================================================= */}

        <aside className="sidebar">


          <button
            className={
              `side-tab overview-tab ${
                activeTab ===
                "overview"
                  ? "active"
                  : ""
              }`
            }

            onClick={() =>
              setActiveTab(
                "overview"
              )
            }
          >

            <span>
              All sensors
            </span>

            <small>
              {sensors.length}
              {" "}
              configured
            </small>

          </button>


          {openTabs.map(
            id => {

              const sensor =
                sensors.find(
                  item =>
                    item.id === id
                );


              if (!sensor) {
                return null;
              }


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
                    {sensor.id}
                  </span>

                  <small>
                    {sensor.location}
                  </small>


                  <b
                    onClick={event =>
                      closeTab(
                        event,
                        id
                      )
                    }
                  >
                    ×
                  </b>

                </button>

              );

            }
          )}

        </aside>


        {/* ================================================= */}
        {/* CONTENT */}
        {/* ================================================= */}

        <section className="content">


          {activeTab ===
          "overview" ? (

            <>

              <div
                className="page-heading"
              >

                <div>

                  <p className="eyebrow">
                    LIVE MONITORING
                  </p>

                  <h1>
                    All configured sensors
                  </h1>

                </div>


                <span
                  className="count-pill"
                >

                  {sensors.length}
                  {" "}
                  sensors

                </span>

              </div>


              <div
                className="sensor-list"
              >

                {sensors.map(
                  sensor => (

                    <button

                      className="sensor-row"

                      key={sensor.id}

                      onClick={() =>
                        openSensor(
                          sensor.id
                        )
                      }

                    >

                      <div>

                        <strong>
                          {sensor.id}
                        </strong>

                        <span>
                          {sensor.type}
                        </span>

                      </div>


                      <span>

                        {sensor.location
                          .replaceAll(
                            "-",
                            " "
                          )}

                      </span>


                      <span
                        className={
                          `status ${
                            getIndicator(
                              readings[
                                sensor.id
                              ]
                            ) ===
                            "Online"
                              ? "online"
                              : "waiting"
                          }`
                        }
                      >

                        {getIndicator(
                          readings[
                            sensor.id
                          ]
                        )}

                      </span>

                    </button>

                  )
                )}

              </div>

            </>

          ) : (

            selected && (

              <DetailView

                sensor={selected}

                reading={
                  readings[
                    selected.id
                  ]
                }

              />

            )

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
  document.getElementById(
    "root"
  )
).render(
  <App />
);