// ============================================================
// HEADER
// ============================================================
//
// Top bar: app name and backend connection status pill.
// ============================================================

export default function Header({ backendStatus }) {
  return (
    <header>

      <div>
        <span className="logo-dot" />
        <strong>Sensor Display Environment</strong>
      </div>

      <span className={`broker ${backendStatus}`}>
        Backend: {backendStatus}
      </span>

    </header>
  );
}
