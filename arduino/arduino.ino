
void setup()
{ 
   Serial.begin(9600);
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "GET_DATA") {
      sendSensorData();
    }
  }
  
  delay(5000); // Regelmäßiges Senden der Sensordaten
  sendSensorData();
}

void sendSensorData() {
  int soilMoisture = analogRead(A0);
  Serial.print("sensor/soil_moisture ");
  Serial.println(soilMoisture);
}
