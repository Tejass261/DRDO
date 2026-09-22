import React, { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

export default function App() {
  const [sensors, setSensors] = useState({});
  const [status, setStatus] = useState('Disconnected');

  useEffect(() => {
    // 1. Connect to WebSocket server on Subscriber.py
    const ws = new WebSocket('ws://127.0.0.1:8765');

    ws.onopen = () => setStatus('Connected');
    ws.onclose = () => setStatus('Disconnected');

    // 2. Hear new data from backend
    ws.onmessage = (event) => {
      const payload = JSON.parse(event.data);

      if (payload.event === 'reading') {
        const id = payload.id;
        const type = payload.type;
        const time = new Date(payload.receivedAt).toLocaleTimeString();

        // 3. Build a simple data point using standard if/else
        let newPoint = { time: time };

        if (type === 'bio') {
          newPoint.smallParticleCount = Number(payload.data.smallParticleCount);
        } else if (type === 'chem' || type === 'fcad') {
          newPoint.gValue = Number(payload.data.gValue);
          newPoint.hValue = Number(payload.data.hValue);
        }

        // 4. Update the React state step-by-step
        setSensors((prevSensors) => {
          // Get current history or start an empty list
          const existingSensor = prevSensors[id];
          const oldHistory = existingSensor ? existingSensor.history : [];

          // Add new point to the end of history
          const newHistory = [...oldHistory, newPoint];

          // If history gets longer than 20 items, remove the oldest (first) item
          if (newHistory.length > 20) {
            newHistory.shift(); // Keeps graph moving right-to-left
          }

          // Return updated object with new history
          return {
            ...prevSensors,
            [id]: {
              id: id,
              type: type,
              location: payload.location,
              history: newHistory
            }
          };
        });
      }
    };

    return () => ws.close();
  }, []);

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      <h1>Sensor Dashboard</h1>
      <p>Status: <strong>{status}</strong></p>

      {/* Loop through each sensor and draw its graph */}
      {Object.values(sensors).map((sensor) => (
        <div
          key={sensor.id}
          style={{
            marginBottom: '30px',
            padding: '15px',
            border: '1px solid #ccc',
            borderRadius: '8px'
          }}
        >
          <h3>
            {sensor.id} ({sensor.type.toUpperCase()}) — {sensor.location}
          </h3>

          <div style={{ width: '100%', height: 250 }}>
            <ResponsiveContainer>
              <LineChart data={sensor.history}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Legend />

                {/* Single line for BIO sensor */}
                {sensor.type === 'bio' && (
                  <Line
                    type="monotone"
                    dataKey="smallParticleCount"
                    stroke="#8884d8"
                    name="Small Particle Count"
                    isAnimationActive={false}
                  />
                )}

                {/* Two lines for CHEM and FCAD sensors */}
                {(sensor.type === 'chem' || sensor.type === 'fcad') && (
                  <>
                    <Line
                      type="monotone"
                      dataKey="gValue"
                      stroke="#82ca9d"
                      name="gValue"
                      isAnimationActive={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="hValue"
                      stroke="#ff7300"
                      name="hValue"
                      isAnimationActive={false}
                    />
                  </>
                )}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      ))}
    </div>
  );
}