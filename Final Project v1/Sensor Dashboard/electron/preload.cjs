const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("sensorAPI", {
  getSensors: () => ipcRenderer.invoke("sensors:get"),
  getSensorTypes: () => ipcRenderer.invoke("types:get"),
  addSensor: (sensor) => ipcRenderer.invoke("sensors:add", sensor),
  onReading: (callback) => ipcRenderer.on("sensor:reading", (_, reading) => callback(reading)),
  onBrokerStatus: (callback) => ipcRenderer.on("broker:status", (_, status) => callback(status))
});
