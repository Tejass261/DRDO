export default function Header({
  connected,
  sensorName,
  macId
}) {

  return (

    <header className="top-header">


      <div className="header-left">

        <div className="app-title">
          FCAD MONITORING SYSTEM
        </div>


        <div className="sensor-location">
          MAIN GATE
        </div>

      </div>


      <div className="header-sensor">

        <span>
          {sensorName}
        </span>


        <span className="header-separator">
          •
        </span>


        <span>
          {macId}
        </span>

      </div>


      <div
        className={
          `connection-status ${
            connected
              ? "connected"
              : "disconnected"
          }`
        }
      >

        <span className="connection-dot" />


        {
          connected
            ? "CONNECTED"
            : "DISCONNECTED"
        }

      </div>

    </header>
  );
}