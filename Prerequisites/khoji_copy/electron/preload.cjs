const { contextBridge } = require("electron");

contextBridge.exposeInMainWorld(
  "electronAPI",
  {

    platform: process.platform,

    websocketURL:
      "ws://127.0.0.1:8765"

  }
);