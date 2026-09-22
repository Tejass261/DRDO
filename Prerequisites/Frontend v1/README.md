# Sensor Display Environment

This Electron + React app monitors the MQTT topics created by Main Project v4.

## First setup

1. Install Node.js.
2. Open a terminal in this folder.
3. Run `npm install` once.
4. Start Mosquitto and the Python backend from Main Project v4.
5. Run `npm run dev`.

Vite and Electron start together. Do not open the Vite URL in Chrome or Edge; wait for the separate Electron dashboard window to appear.

The app expects the Python configuration here by default:

`../Main Project v4/Config.txt`

If the configuration is elsewhere, start the app with the `SENSOR_CONFIG_PATH` environment variable set to the full path of that file.

## How it works

- The initial left tab is **All sensors**.
- Selecting a sensor opens a new closable tab in the left panel.
- The right panel shows the latest MQTT reading and sensor information.
- **Add sensor** creates a new physical-sensor entry in `Config.txt`. It does not create a sensor type and does not start a Python converter automatically.
- The app listens to `sensors/#`, so it receives every location-based sensor topic.

Topics use this structure:

`sensors/<location>/<type>/<sensor-id>`
