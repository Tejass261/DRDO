import DataBox from "./DataBox";
import MainValues from "./MainValues";
import Section from "./Section";


function displayValue(value) {

  return (
    value === undefined ||
    value === null ||
    value === ""
  )
    ? "--"
    : value;
}


/* ============================================================
   COMPACT METRIC ROW
   ============================================================ */

function MetricRow({
  label,
  value,
  unit = "",
  className = ""
}) {

  const shown =
    displayValue(
      value
    );


  return (

    <div
      className={
        `metric-row ${className}`.trim()
      }
    >

      <span className="metric-label">
        {label}
      </span>


      <span className="metric-value">

        {shown}

        {
          unit &&
          shown !== "--"
            ? ` ${unit}`
            : ""
        }

      </span>

    </div>
  );
}


/* ============================================================
   G / H CHANNEL PANEL
   ============================================================ */

function ChannelPanel({
  channel,
  data
}) {

  const isG =
    channel === "G";


  const values = isG

    ? {

        rip:
          data.koRipG,

        ripAmp:
          data.ripAmpG,

        ko1:
          data.ko1G,

        ko2:
          data.ko2G,

        ko3:
          data.ko3G,

        amp1:
          data.ampGKo1,

        amp2:
          data.ampGKo2,

        amp3:
          data.ampGKo3,

        atmospheric:
          data.atmosphericPressureG,

        pressure:
          data.gPressure,

        hv:
          data.hvFeedbackG,

        duty:
          data.gDuty
      }


    : {

        rip:
          data.koRipH,

        ripAmp:
          data.ripAmpH,

        ko1:
          data.ko1H,

        ko2:
          data.ko2H,

        ko3:
          data.ko3H,

        amp1:
          data.ampHKo1,

        amp2:
          data.ampHKo2,

        amp3:
          data.ampHKo3,

        atmospheric:
          data.atmosphericPressureH,

        pressure:
          data.hPressure,

        hv:
          data.hvFeedbackH,

        duty:
          data.hDuty
      };


  return (

    <div
      className={
        `channel-panel ${
          isG
            ? "g-panel"
            : "h-panel"
        }`
      }
    >


      {/* ====================================================
          CHANNEL HEADER
          ==================================================== */}

      <div className="channel-heading">

        <strong>
          {channel} CHANNEL
        </strong>

      </div>


      {/* ====================================================
          RIP
          ==================================================== */}

      <div className="channel-top-grid">

        <DataBox
          label="KO RIP"
          value={
            values.rip
          }
        />


        <DataBox
          label="RIP AMP"
          value={
            values.ripAmp
          }
        />

      </div>


      {/* ====================================================
          KO / AMPLIFIER
          ==================================================== */}

      <div className="mini-heading">
        KO / AMPLIFIER
      </div>


      <div className="ko-stack">


        {/* ================= KO-1 ================= */}

        <div className="ko-card">

          <MetricRow
            label="KO-1"
            value={
              values.ko1
            }
          />


          <MetricRow
            label="AMP"
            value={
              values.amp1
            }
          />

        </div>


        {/* ================= KO-2 ================= */}

        <div className="ko-card">

          <MetricRow
            label="KO-2"
            value={
              values.ko2
            }
          />


          <MetricRow
            label="AMP"
            value={
              values.amp2
            }
          />

        </div>


        {/* ================= KO-3 ================= */}

        <div className="ko-card">

          <MetricRow
            label="KO-3"
            value={
              values.ko3
            }
          />


          <MetricRow
            label="AMP"
            value={
              values.amp3
            }
          />

        </div>

      </div>


      {/* ====================================================
          PRESSURE / HV / DUTY
          ==================================================== */}

      <div className="mini-heading">
        PRESSURE / HV / DUTY
      </div>


      <div className="channel-bottom-grid">

        <MetricRow
          label="ATM PRESSURE"
          value={
            values.atmospheric
          }
          unit="Torr"
        />


        <MetricRow
          label={`${channel} PRESSURE`}
          value={
            values.pressure
          }
          unit="Torr"
        />


        <MetricRow
          label="HV FEEDBACK"
          value={
            values.hv
          }
          unit="V"
        />


        <MetricRow
          label="DUTY"
          value={
            values.duty
          }
        />

      </div>

    </div>
  );
}


/* ============================================================
   TEMPERATURE PANEL
   ============================================================ */

function TemperaturePanel({
  data
}) {

  const temperatures = [

    [
      "BODY",
      data.bodyTemperature
    ],

    [
      "NOZZLE",
      data.nozzleTemperature
    ],

    [
      "HV-G",
      data.hvGTemperature
    ],

    [
      "HV-H",
      data.hvHTemperature
    ],

    [
      "DIGITAL BOARD",
      data.digitalBoardTemperature
    ],

    [
      "SENSOR BOARD",
      data.sensorBoardTemperature
    ],

    [
      "DISPLAY BOARD",
      data.displayBoardTemperature
    ]

  ];


  return (

    <div
      className="
        info-panel
        temperature-panel
      "
    >

      <div className="panel-heading">
        TEMPERATURE
      </div>


      <div className="temperature-list">

        {
          temperatures.map(
            ([label, value]) => (

              <MetricRow
                key={label}
                label={label}
                value={value}
                unit="°C"
              />

            )
          )
        }

      </div>

    </div>
  );
}


/* ============================================================
   SYSTEM PANEL
   ============================================================ */

function SystemPanel({
  data
}) {

  const ready =
    data.readyState === "READY";


  return (

    <div
      className="
        info-panel
        system-panel
      "
    >

      <div className="panel-heading">
        SYSTEM STATUS
      </div>


      {/* ====================================================
          STATE / BATTERY
          ==================================================== */}

      <div className="system-primary">


        <div className="system-card">

          <span>
            STATE
          </span>


          <strong
            className={
              ready
                ? "ready"
                : "waiting"
            }
          >

            {
              displayValue(
                data.readyState
              )
            }

          </strong>

        </div>


        <div className="system-card">

          <span>
            BATTERY
          </span>


          <strong>

            {
              displayValue(
                data.battery
              )
            }


            {
              data.battery !== "--"
                ? " %"
                : ""
            }

          </strong>

        </div>

      </div>


      {/* ====================================================
          OPERATION
          ==================================================== */}

      <div className="mini-heading">
        OPERATION
      </div>


      <div className="system-list">

        <MetricRow
          label="HOURS SINCE RECHARGE"
          value={
            data.hoursRunSinceLastRecharge
          }
          unit="hrs"
        />


        <MetricRow
          label="FLOW OUTER LOOP"
          value={
            data.flowInOuterLoop
          }
        />


        <MetricRow
          label="PACKET"
          value={
            data.packetLength
          }
          unit="bytes"
        />

      </div>


      {/* ====================================================
          IDENTIFICATION
          ==================================================== */}

      <div className="mini-heading">
        IDENTIFICATION
      </div>


      <div className="system-list">

        <MetricRow
          label="UNIT NAME"
          value={
            data.sensorName
          }
        />


        <MetricRow
          label="MAC ID"
          value={
            data.macId
          }
        />

      </div>

    </div>
  );
}


/* ============================================================
   MAIN DASHBOARD
   ============================================================ */

export default function Dashboard({
  data
}) {

  return (

    <main className="dashboard">


      {/* ====================================================
          PRIMARY READINGS
          ==================================================== */}

      <Section
        title="PRIMARY READINGS"
        className="primary-section"
      >

        <MainValues
          data={data}
        />


        <div className="primary-status">

          <DataBox
            label="STATE"
            value={
              data.readyState
            }
            className="state-box"
          />


          <DataBox
            label="BATTERY"
            value={
              data.battery
            }
            unit="%"
          />


          <DataBox
            label="HOURS SINCE RECHARGE"
            value={
              data.hoursRunSinceLastRecharge
            }
            unit="hrs"
          />

        </div>

      </Section>


      {/* ====================================================
          MAIN FOUR-PANEL AREA
          ==================================================== */}

      <div className="main-grid">


        {/* ================= G ================= */}

        <Section
          title="G"
          className="channel-section"
        >

          <ChannelPanel
            channel="G"
            data={data}
          />

        </Section>


        {/* ================= H ================= */}

        <Section
          title="H"
          className="channel-section"
        >

          <ChannelPanel
            channel="H"
            data={data}
          />

        </Section>


        {/* ================= TEMPERATURE ================= */}

        <Section
          title="TEMPERATURE"
          className="info-section"
        >

          <TemperaturePanel
            data={data}
          />

        </Section>


        {/* ================= SYSTEM ================= */}

        <Section
          title="SYSTEM"
          className="info-section"
        >

          <SystemPanel
            data={data}
          />

        </Section>

      </div>

    </main>
  );
}