import { useEffect, useState } from 'react';

function App() {
  const [sensorData, setSensorData] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('Connecting...');

  useEffect(() => {
    // Connect to Python WebSocket server
    const ws = new WebSocket('ws://localhost:8765');

    ws.onopen = () => setConnectionStatus('Connected');

    ws.onclose = () => setConnectionStatus('Disconnected');

    ws.onmessage = (event) => {
      // Parse JSON payload sent from Python
      const received = JSON.parse(event.data);
      setSensorData(received);
    };

    // Cleanup connection when React component unmounts
    return () => ws.close();
  }, []);

  return (
    <div
      style={{
        padding: '30px',
        fontFamily: 'sans-serif',
        backgroundColor: '#1e1e1e'
      }}
    >
      <h2>Desktop Dashboard</h2>

      <p>
        Backend Status:{' '}
        <strong
          style={{
            color: connectionStatus === 'Connected' ? 'green' : 'red'
          }}
        >
          {connectionStatus}
        </strong>
      </p>

      {sensorData ? (
        <div
          style={{
            border: '1px solid #444',
            padding: '20px',
            borderRadius: '8px'
          }}
        >
          <h3>Live Metrics</h3>

          <p>
            <strong>Temperature:</strong> {sensorData.temperature} °C
          </p>

          <p>
            <strong>Humidity:</strong> {sensorData.humidity} %
          </p>

          <p>
            <strong>Status:</strong> {sensorData.status}
          </p>
        </div>
      ) : (
        <p>Waiting for data stream from Python...</p>
      )}
    </div>
  );
}

export default App;