export const fcadFields = {
  sensorName: { label: "Unit Name", type: "text" },
  macId: { label: "MAC ID", type: "text" },

  gValue: { label: "G Value", type: "number" },
  hValue: { label: "H Value", type: "number" },

  gKoChemical: { label: "G KO", type: "number" },
  hKoChemical: { label: "H KO", type: "number" },

  koRipG: { label: "KO RIP G", type: "number" },
  koRipH: { label: "KO RIP H", type: "number" },
  ripAmpG: { label: "RIP Amp G", type: "number" },
  ripAmpH: { label: "RIP Amp H", type: "number" },

  ko1G: { label: "KO-1 G", type: "number" },
  ko2G: { label: "KO-2 G", type: "number" },
  ko3G: { label: "KO-3 G", type: "number" },
  ampGKo1: { label: "Amp G KO-1", type: "number" },
  ampGKo2: { label: "Amp G KO-2", type: "number" },
  ampGKo3: { label: "Amp G KO-3", type: "number" },

  ko1H: { label: "KO-1 H", type: "number" },
  ko2H: { label: "KO-2 H", type: "number" },
  ko3H: { label: "KO-3 H", type: "number" },
  ampHKo1: { label: "Amp H KO-1", type: "number" },
  ampHKo2: { label: "Amp H KO-2", type: "number" },
  ampHKo3: { label: "Amp H KO-3", type: "number" },

  atmosphericPressureG: { label: "Atmospheric Pressure G", type: "number", unit: "Torr" },
  atmosphericPressureH: { label: "Atmospheric Pressure H", type: "number", unit: "Torr" },
  gPressure: { label: "G Pressure", type: "number", unit: "Torr" },
  hPressure: { label: "H Pressure", type: "number", unit: "Torr" },

  hoursRunSinceLastRecharge: { label: "Hours Since Recharge", type: "number", unit: "hrs" },
  gDuty: { label: "G Duty", type: "number" },
  hDuty: { label: "H Duty", type: "number" },

  bodyTemperature: { label: "Body Temperature", type: "number", unit: "°C" },
  nozzleTemperature: { label: "Nozzle Temperature", type: "number", unit: "°C" },
  hvGTemperature: { label: "HV-G Temperature", type: "number", unit: "°C" },
  hvHTemperature: { label: "HV-H Temperature", type: "number", unit: "°C" },
  digitalBoardTemperature: { label: "Digital Board Temperature", type: "number", unit: "°C" },
  sensorBoardTemperature: { label: "Sensor Board Temperature", type: "number", unit: "°C" },
  displayBoardTemperature: { label: "Display Board Temperature", type: "number", unit: "°C" },

  hvFeedbackG: { label: "HV Feedback G", type: "number", unit: "V" },
  hvFeedbackH: { label: "HV Feedback H", type: "number", unit: "V" },
  flowInOuterLoop: { label: "Flow Outer Loop", type: "number" },

  readyState: { label: "State", type: "text" },
  battery: { label: "Battery", type: "number", unit: "%" },
};
