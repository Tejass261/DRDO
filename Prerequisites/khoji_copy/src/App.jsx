import {
  useEffect,
  useState
} from "react";

import "./App.css";

import Dashboard from "./components/Dashboard";
import Header from "./components/Header";

import {
  valueOrDash
} from "./components/DataBox";


const WS_URL =
  "ws://127.0.0.1:8765";


const initialData = {

  sensorName: "--",
  macId: "--",

  gValue: "--",
  hValue: "--",

  koRipG: "--",
  koRipH: "--",

  ripAmpG: "--",
  ripAmpH: "--",

  ko1G: "--",
  ko2G: "--",
  ko3G: "--",

  ko1H: "--",
  ko2H: "--",
  ko3H: "--",

  ampGKo1: "--",
  ampGKo2: "--",
  ampGKo3: "--",

  ampHKo1: "--",
  ampHKo2: "--",
  ampHKo3: "--",

  atmosphericPressureG: "--",
  atmosphericPressureH: "--",

  gPressure: "--",
  hPressure: "--",

  hoursRunSinceLastRecharge: "--",

  gDuty: "--",
  hDuty: "--",

  bodyTemperature: "--",
  nozzleTemperature: "--",

  battery: "--",

  hvFeedbackG: "--",
  hvFeedbackH: "--",

  flowInOuterLoop: "--",

  hvGTemperature: "--",
  hvHTemperature: "--",

  digitalBoardTemperature: "--",
  sensorBoardTemperature: "--",
  displayBoardTemperature: "--",

  readyState: "--",

  packetLength: "--"
};


function App() {

  const [
    data,
    setData
  ] = useState(
    initialData
  );


  /*
   * IMPORTANT:
   *
   * This represents the SENSOR connection,
   * not the WebSocket connection.
   *
   * It becomes true only after actual FCAD
   * data is received.
   */

  const [
    sensorConnected,
    setSensorConnected
  ] = useState(false);


  const [
    lastUpdate,
    setLastUpdate
  ] = useState("--");


  useEffect(() => {

    let websocket;

    let reconnectTimer;

    let stopped = false;


    const connect = () => {

      if (stopped) {
        return;
      }


      console.log(
        "[Frontend] Connecting to backend..."
      );


      websocket =
        new WebSocket(
          WS_URL
        );


      websocket.onopen = () => {

        console.log(
          "[Frontend] WebSocket connected."
        );

        /*
         * DO NOT set sensorConnected here.
         *
         * WebSocket connection only means that
         * the frontend can talk to the backend.
         *
         * Backend will send sensor_status when
         * actual sensor data is available.
         */
      };


      websocket.onmessage = (
        event
      ) => {

        try {

          const message =
            JSON.parse(
              event.data
            );


          // ==============================================
          // SENSOR STATUS
          // ==============================================

          if (
            message.event ===
            "sensor_status"
          ) {

            setSensorConnected(
              Boolean(
                message.connected
              )
            );


            return;
          }


          // ==============================================
          // SENSOR DATA
          // ==============================================

          if (
            message.event ===
            "reading"
            &&
            message.data
          ) {

            setData(
              previous => ({
                ...previous,
                ...message.data
              })
            );


            setLastUpdate(
              new Date()
                .toLocaleTimeString()
            );


            /*
             * A reading itself also proves that
             * the sensor is connected.
             *
             * This makes reconnection immediate even
             * before a separate status message is
             * processed.
             */

            setSensorConnected(
              true
            );
          }


        } catch (error) {

          console.error(
            "[Frontend] Invalid WebSocket message:",
            error
          );
        }
      };


      websocket.onclose = () => {

        /*
         * If the backend connection itself dies,
         * the frontend cannot receive sensor data,
         * therefore show DISCONNECTED.
         */

        setSensorConnected(
          false
        );


        if (!stopped) {

          reconnectTimer =
            setTimeout(
              connect,
              2000
            );
        }
      };


      websocket.onerror = (
        error
      ) => {

        console.error(
          "[Frontend] WebSocket error:",
          error
        );
      };

    };


    connect();


    return () => {

      stopped = true;

      clearTimeout(
        reconnectTimer
      );

      websocket?.close();

    };

  }, []);


  return (

    <div className="app">


      <Header

        connected={
          sensorConnected
        }

        sensorName={
          valueOrDash(
            data.sensorName
          )
        }

        macId={
          valueOrDash(
            data.macId
          )
        }

      />


      <Dashboard
        data={data}
      />


      <footer className="footer">

        <div>
          FCAD • MAIN GATE
        </div>


        <div>
          LAST UPDATE: {lastUpdate}
        </div>

      </footer>

    </div>
  );
}


export default App;