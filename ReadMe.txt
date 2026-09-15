|
|--Main Project v1
	|--Virtual Sensors
		|--Bio_Sensor_1.py
		|--Chem_Seosor_1.py
	|--Convertors
		|--Convertor_Bio_Sensor_1.py
		|--Convertor_Chem_Sensor_1.py
		|--fcad_convertor.py
	|--Monitoring Station
		|--Subscriber.py
	|--   log
		|--log_bio_sensor
			|--Bio_Sensor_1_2026-08-25 ....
		|--log_chem_sensor
			|--Chem_Sensor_1_2026-08-25 ...
		|--log_fcad_sensor
			|--fcad_Sensor_2026-08-25 .....
	|--config


--> The v1 of the project deals with different convertor codes for each type of sensor that is available, run seperately.
--> First a Sensor is started, its respective convertor is started, then the subscriber can be started to receive updates and log.
--> the broker used is mosquito, that is based on mqtt protocol.
--> conversion of oem protocols to a singular protocol (mqtt) leads to different convertors for each sensor.
--> logs are created seperately for each sensor and a file is created on each new day the sensor is running, named as shown.
--> universal config file is used and every program picks up values from centralized config file, making it easy to edit variables.
--> An attempt at a universal convertor is attempted in v2 of this project. 

-->version 2 deals with the universal convertor, where, we implemented the learning of all topics and created a universal convertor
-->the universal convertor architecture is as follows
	sensor_bio  --> uni_conevertor --|
	sensor_fcad --> uni_conevertor --|-->subscriber
	sensor_chem --> uni_conevertor --|

--> if a new sensor is to be added it is directly added by just adding values in config file no need to edit code
--> each sensor doesn't need its respective convertor, just a universal convertor working separately for each sensor

--> version 3 includes major code improvements, like proper error control and voluntary closing of servers, subscriber, or convertors
    manually in a way it doesn't crash
--> it also impliments the fact that the 3 sensors earlier created were just types and sensors can be any one of the type
--> there can be various sensors of the same type and be located on different locations, differenciating them on teh basis of location
--> in version 3 our backend is fully complete and now we can move to ui or frontend learning.
#-----------------------------------------------------------------------------------------------------------------------------------------
Data Conversions from OEM or other protocols to MQTT string passing
	
	-->FCAD
		--> The data received is in the form of 119 Bytes that is then received by udp protocol
		--> The data is stored in Byte Array format and accessed via specific index values for specific data (defined by OEM protocol)
		--> The data is sent via mqtt (mosquito) mqtt as a string format the string format is as follows
		
			payload = f"TT2_Sensor,{gvalue},{hvalue},{atmospheric_pressure_g},{atmospheric_pressure_h},{g_pressure},{h_pressure},{battery},{mode}"
		
		--> These respective values are received by client who is supposed to know the sequence of these values to log and display them.