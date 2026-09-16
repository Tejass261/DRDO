const { app, BrowserWindow, ipcMain } = require("electron");
const fs = require("fs");
const path = require("path");
const mqtt = require("mqtt");

let mainWindow;
let mqttClient;

// Change SENSOR_CONFIG_PATH if Config.txt is stored somewhere else.
const configPath = process.env.SENSOR_CONFIG_PATH || path.resolve(__dirname, "..", "..", "Main Project v4", "Config.txt");

function readConfig() {
  return JSON.parse(fs.readFileSync(configPath, "utf8"));
}

function makeTopic(sensorId, sensor) {
  return `sensors/${sensor.location}/${sensor.type}/${sensorId}`;
}

function getSensors() {
  const config = readConfig();
  return Object.entries(config.sensors).map(([id, sensor]) => ({
    id,
    ...sensor,
    topic: makeTopic(id, sensor)
  }));
}

function sendToDashboard(channel, data) {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send(channel, data);
  }
}

function connectMqtt() {
  const config = readConfig();
  const url = `mqtt://${config.global.ip_broker}:${config.global.port_broker}`;
  mqttClient = mqtt.connect(url);

  mqttClient.on("connect", () => {
    mqttClient.subscribe("sensors/#");
    sendToDashboard("broker:status", "connected");
  });

  mqttClient.on("reconnect", () => sendToDashboard("broker:status", "reconnecting"));
  mqttClient.on("offline", () => sendToDashboard("broker:status", "offline"));
  mqttClient.on("error", () => sendToDashboard("broker:status", "error"));

  mqttClient.on("message", (topic, message) => {
    const parts = topic.split("/");
    if (parts.length !== 4 || parts[0] !== "sensors") return;

    sendToDashboard("sensor:reading", {
      topic,
      location: parts[1],
      type: parts[2],
      id: parts[3],
      payload: message.toString(),
      receivedAt: new Date().toISOString()
    });
  });
}

ipcMain.handle("sensors:get", () => getSensors());
ipcMain.handle("types:get", () => Object.keys(readConfig().sensor_types));

ipcMain.handle("sensors:add", (_, newSensor) => {
  const config = readConfig();
  const id = newSensor.id.trim();

  if (!id || config.sensors[id]) {
    throw new Error("Choose a new sensor ID.");
  }
  if (!config.sensor_types[newSensor.type]) {
    throw new Error("Choose an existing sensor type.");
  }

  config.sensors[id] = {
    type: newSensor.type,
    location: newSensor.location.trim().toLowerCase().replace(/\s+/g, "-"),
    ip: newSensor.ip.trim(),
    port: Number(newSensor.port),
    request: newSensor.request.trim(),
    request_interval: Number(newSensor.request_interval) || 3
  };

  fs.writeFileSync(configPath, JSON.stringify(config, null, 2) + "\n");
  return { id, ...config.sensors[id], topic: makeTopic(id, config.sensors[id]) };
});

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1250,
    height: 780,
    minWidth: 900,
    minHeight: 600,
    webPreferences: {
      // This is a local learning application. React can use Electron IPC
      // directly, which keeps the setup simple while you learn the frontend.
      contextIsolation: false,
      nodeIntegration: true,
      sandbox: false
    }
  });

  if (process.env.VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL);
  } else {
    mainWindow.loadFile(path.join(__dirname, "..", "dist", "index.html"));
  }
}

app.whenReady().then(() => {
  createWindow();
  connectMqtt();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("before-quit", () => {
  if (mqttClient) mqttClient.end();
});
