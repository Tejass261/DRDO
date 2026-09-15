# Main Project v4 — Location-Based Sensors

Each entry under `sensors` in `Config.txt` is one physical sensor. A sensor has an ID, type, location, IP address and port.

The topic is made automatically by the converter:

`sensors/<location>/<type>/<sensor-id>`

Examples:

- `sensors/main-gate/bio/bio-main-gate-01`
- `sensors/director-office/chem/chem-director-office-01`

## Current virtual sensors

- Bio: Main Gate — port 5050
- Chem: Main Gate — port 5051
- Bio: Director Office — port 5052
- Chem: Director Office — port 5053

## Run the project

1. Install the MQTT Python library: `pip install -r requirements.txt`
2. Start the Mosquitto broker.
3. In `Virtual Sensors`, run `Start_All_Virtual_Sensors.bat`. It opens four separate virtual-sensor programs, one per physical sensor.
4. In `Convertors`, run `Start_All_Converters.bat`.
5. Run `python "Monitoring Station/Subscriber.py"` from the project folder.

The subscriber listens to `sensors/#`, so it receives every sensor at every location. It creates logs in this form:

`log/<location>/<type>/<sensor-id>_<date>.txt`

## Adding another Bio or Chem sensor

Add one more sensor entry in `Config.txt`, choose an unused port, then create a small virtual-sensor file for it if you need a simulator. No converter code needs to be copied.

FCAD remains available as a sensor type. When a real FCAD device is assigned a location, add an FCAD sensor entry with its ID, location, IP and port, then run `Universal_Convertor.py` with that ID.
