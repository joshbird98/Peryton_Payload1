/* IMPORTANT 
/ For accurate conversion between atmospheric pressure and altitude,
/ the current sea level pressure and the outside temperature must be
/ known. These change a lot!
/ Find out the most recent measurement for the launch site here:
/ https://meteologix.com/uk/observations/cambridgeshire/pressure-qnh/20210622-1900z.html
/ Make sure to change #define sea_level_pr and #define outside_temp
/ below, and then reupload the code to the payload.
/ Note that if these values are incorrect, the altitude conversion will 
/ be wrong, and a manual conversion from atmospheric pressure is required.
*/
#define sea_level_pr 1022.0   // [hPa] update with latest value for launch site location
#define outside_temp 22.0     // [C] update with latest value for launch site location

#include <SdFat.h>            // SD card config
#define FILENAME "fd.csv"
SdFat sd;
SdFile file;
const int sd_cs = 6;

#include "BlueDot_BME280.h"   // BME280 config
BlueDot_BME280 bme;
int bmeDetected = 0;
#define BME_ADDRESS 0x76

#include "MPU9250.h"          // MPU9250 config
MPU9250 IMU(Wire,0x68);
int mpuStatus;

// Prototype functions
void flashLed(uint16_t period, uint8_t cycles);
void sdSetup();
void bmeSetup();
void mpuSetup();

void setup() {
  //Serial.begin(9600);
  Wire.begin();
  pinMode(9, OUTPUT);
  flashLed(1000,3);            // Powered up!
 
  sdSetup();
  bmeSetup();
  mpuSetup();
}

// Write data to csv file repeatedly
void loop() {
  file.print(String(millis()));
  file.write(',');
  file.print(String(bme.readTempC()));
  file.write(',');
  file.print(String(bme.readHumidity()));
  file.write(',');
  file.print(String(bme.readPressure()));
  file.write(',');
  file.print(String(bme.readAltitudeMeter())); 
  file.print(',');
  PORTB = PORTB | B00000010;                          // turn LED on
  IMU.readSensor();
  file.print(String(IMU.getAccelX_mss(),6));
  file.write(',');
  file.print(String(IMU.getAccelY_mss(),6));
  file.write(',');
  file.print(String(IMU.getAccelZ_mss(),6));
  file.write(',');
  file.print(String(IMU.getGyroX_rads(),6));
  file.write(',');
  file.print(String(IMU.getGyroY_rads(),6));
  file.write(',');
  file.print(String(IMU.getGyroZ_rads(),6));
  file.write(',');
  file.print(String(IMU.getMagX_uT(),6));
  file.write(',');
  file.print(String(IMU.getMagY_uT(),6));
  file.write(',');
  file.println(String(IMU.getMagZ_uT(),6));
  
  if (file.sync() && !file.getWriteError()) {
    PORTB = PORTB & B11111101;                        // turn LED off
  }
}



// LED blinker used for diagnostics when serial monitor unavailable.
void flashLed(uint16_t period, uint8_t cycles) {
  for (uint8_t i = 0; i < cycles; i++) {
    PORTB = PORTB | B00000010;                        // turn LED on
    delay(period);
    PORTB = PORTB & B11111101;                        // turn LED off
    delay(period);
  }
}

// Tests the SD card and appends an opening line to the flight_data file
void sdSetup() {
  if (sd.begin(sd_cs, SD_SCK_MHZ(8))) {
    //Serial.println("SD Card initialized!");
    if (file.open(FILENAME, O_WRONLY | O_CREAT | O_AT_END)) {
      file.print(String(sea_level_pr));
      file.write(',');
      file.println(String(outside_temp));
      file.sync();
      file.getWriteError();
    }
    else {
      //Serial.println("Couldn't open file.");
      flashLed(500, 10);
    }
  }
  else {
    //Serial.println("Couldn't init SD card.");
    flashLed(500, 10);
  }
}

// Sets up the BME280 with some register values, and tests comms
void bmeSetup() {
  bme.parameter.communication = 0;
  bme.parameter.I2CAddress = BME_ADDRESS;
  bme.parameter.sensorMode = 0b11;
  bme.parameter.IIRfilter = 0b100;
  bme.parameter.humidOversampling = 0b101;
  bme.parameter.tempOversampling = 0b101;
  bme.parameter.pressOversampling = 0b101;
  bme.parameter.pressureSeaLevel = sea_level_pr;    // default to 1013.25
  bme.parameter.tempOutsideCelsius = outside_temp;  // default to 15
  
  if (bme.init() != 0x60) {
    bmeDetected = 0;
    //println("BME280 not detected...");
    flashLed(1000, 5);
  }
  else {
    bmeDetected = 1;
    //Serial.println("BME280 detected!");
  }
}

void mpuSetup() {
  mpuStatus = IMU.begin();
  if (mpuStatus < 0) {
    //Serial.println("MPU9250 not detected...");
    flashLed(3000, 15);
  }
  else {
    //IMU.setAccelRange(MPU9250::ACCEL_RANGE_16G);        // 2,4,8,16 G
    //IMU.setGyroRange(MPU9250::GYRO_RANGE_2000DPS);      // 250,500,1000,2000 DPS
    //IMU.setDlpfBandwidth(MPU9250::DLPF_BANDWIDTH_184HZ); // 184,92,41,20,10,5 HZ
    IMU.setSrd(19); // set SRD to 19 for a 50 Hz
    //IMU.calibrateGyro();
    //IMU.calibrateAccel();
    //IMU.calibrateMag(); // rotate payload in figure 8...
  }
}
