#include <DHT_U.h>
#include <DHT.h>


#define DHTTYPE DHT22   // DHT 22  (AM2302)


unsigned long lastSendTime = 0;
unsigned long sendInterval = 5000; // Default send interval
const int maxSensors = 10;
int sensorPins[maxSensors] = {-1}; // Default sensor pin
String sensorTypes[maxSensors] = {""}; // Default sensor type
String sensorIds[maxSensors] = {""}; // Default sensor id
DHT* dhtSensors[maxSensors] = {nullptr}; // Array to store DHT sensor objects
int sensorCount = 0; // Number of sensors currently configured

void setup()
{ 
   Serial.begin(9600);
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "GET_DATA") {
      Serial.println("arduino/logs Received GET_DATA command");
      sendSensorData();
    } else if (command.startsWith("SET_INTERVAL")) {
      sendInterval = command.substring(12).toInt(); // Extract the new interval from the command
      Serial.println("arduino/logs Set send interval to: " + sendInterval);
    } else if (command.startsWith("ADD_SENSOR")) {
      String params = command.substring(11); // Remove the command (ADD_SENSOR with space)
      int spaceIndex = params.indexOf(' '); // Find the space between pin and type
      int pinValue = params.substring(0, spaceIndex).toInt(); // Extract the pin number from the command
      String typeAndId = params.substring(spaceIndex + 1); // Extract the type and id from the command
      int spaceIndex2 = typeAndId.indexOf(' '); // Find the space between type and id
      String sensorType = typeAndId.substring(0, spaceIndex2); // Extract the sensor type from the command
      String sensorId = typeAndId.substring(spaceIndex2 + 1); // Extract the sensor id from the command
      Serial.println("arduino/logs Added sensor: " + sensorType + " " + sensorId + " on pin: " + pinValue);
      if (sensorCount < maxSensors) {
        sensorPins[sensorCount] = pinValue;
        sensorTypes[sensorCount] = sensorType;
        sensorIds[sensorCount] = sensorId;
        if (sensorType == "dht") {
          dhtSensors[sensorCount] = new DHT(pinValue, DHTTYPE);
          dhtSensors[sensorCount]->begin();
        }
        sensorCount++;
      }
    } else if (command.startsWith("REMOVE_SENSOR")) {
      int pin = command.substring(13).toInt(); // Extract the pin number from the command
      for (int i = 0; i < sensorCount; i++) {
        if (sensorPins[i] == pin) {
          // Shift all subsequent sensors down to fill the gap
          for (int j = i; j < sensorCount - 1; j++) {
            sensorPins[j] = sensorPins[j + 1];
            sensorTypes[j] = sensorTypes[j + 1];
            sensorIds[j] = sensorIds[j + 1];
            dhtSensors[j] = dhtSensors[j + 1];
          }
          sensorCount--;
          Serial.println("arduino/logs Removed sensor on pin: " + pin);
          break;
        }
      }
    } else if (command == "CLEAR_ALL") {
      // Hard reset to the initial defaults
      lastSendTime = 0;
      sendInterval = 5000;
      sensorCount = 0;
      for (int i = 0; i < maxSensors; i++) {
        sensorPins[i] = -1;
        sensorTypes[i] = "";
        sensorIds[i] = "";
        dhtSensors[i] = nullptr;
      }
      Serial.println("arduino/logs Cleared all sensors and settings");
    }
  }
  
  if (millis() - lastSendTime >= sendInterval) {
    lastSendTime = millis();
    sendSensorData();
  }
}

void sendSensorData() {
  for (int i = 0; i < sensorCount; i++) {
    String sensorValue;
    if (sensorTypes[i] == "dht") {
      float humidity = dhtSensors[i]->readHumidity();
      float temperature = dhtSensors[i]->readTemperature();
      sensorValue = String(humidity) + " " + String(temperature);
    } else {
      sensorValue = String(analogRead(sensorPins[i]));
    }
    Serial.println("sensor/" + sensorTypes[i] + " " + sensorIds[i] + " " + sensorValue);
  }
}

// Example commands for documentation:
// GET_DATA: Request the current sensor data
// SET_INTERVAL <interval>: Set the interval for sending sensor data (in milliseconds)
// ADD_SENSOR <pin> <type> <id>: Add a new sensor with the specified pin, type and id
// REMOVE_SENSOR <pin>: Remove the sensor with the specified pin
// CLEAR_ALL: Hard reset to the initial defaults, including all sensors and everything

// Example usage:
// GET_DATA
// SET_INTERVAL 10000
// ADD_SENSOR 2 soil_moisture 2
// ADD_SENSOR 3 DHT 1
// REMOVE_SENSOR 2
// CLEAR_ALL
