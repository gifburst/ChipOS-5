#include <i2c_t3.h>
#include <TinyGPS++.h>
#include <Encoder.h>
#include <Bounce.h>
                 
#define PIN_VOL A1
#define PIN_ENC_1_A 4
#define PIN_ENC_1_B 3
#define PIN_ENC_2_A 6
#define PIN_ENC_2_B 5
#define LED_SYSTEM 14
#define LED_STATUS 13
#define LED_DATA   20
#define LED_CLOSE  11
#define PIN_BTN_SYSTEM 10
#define PIN_BTN_STATUS 9
#define PIN_BTN_DATA   8 
#define PIN_BTN_CLOSE  7
#define PIN_BTN_ENTER  2
#define PIN_SW_AUDIO   16

TinyGPSPlus gps;
Bounce buttonSystem = Bounce(PIN_BTN_SYSTEM, 10);
Bounce buttonStatus = Bounce(PIN_BTN_STATUS, 10);
Bounce buttonData = Bounce(PIN_BTN_DATA, 10);
Bounce buttonClose = Bounce(PIN_BTN_CLOSE, 10);
Bounce buttonEnter = Bounce(PIN_BTN_ENTER, 10);
Encoder encoderScroll(PIN_ENC_1_A, PIN_ENC_1_B);
Encoder encoderTab(PIN_ENC_2_A, PIN_ENC_2_B);

int curLed = 0;
int lastLed = 0;
boolean switchState = false;
int lastScrollPos = -999;
int lastTabPos = -999;
int rawVolume = 0;
int curVolume = 80;
int lastVolume = 0;

unsigned long curTime = 0;
unsigned long lastTime = -1;
unsigned long updateInterval = 900;

void setup(){
  
  pinMode(PIN_BTN_SYSTEM, INPUT_PULLUP);
  pinMode(PIN_BTN_STATUS, INPUT_PULLUP);
  pinMode(PIN_BTN_DATA, INPUT_PULLUP);
  pinMode(PIN_BTN_CLOSE, INPUT_PULLUP);
  pinMode(PIN_BTN_ENTER, INPUT_PULLUP);
  pinMode(PIN_SW_AUDIO, INPUT_PULLUP);

  pinMode(LED_SYSTEM, OUTPUT);
  pinMode(LED_STATUS, OUTPUT);
  pinMode(LED_DATA, OUTPUT);
  pinMode(LED_CLOSE, OUTPUT);
  digitalWrite(LED_SYSTEM, HIGH);
  Wire.begin(I2C_MASTER, 0x00, I2C_PINS_18_19, I2C_PULLUP_EXT, 400000);
  Wire.setDefaultTimeout(10000); // 10ms          
  Serial.begin(9600);
  Serial1.begin(9600);
  
}

void loop(){

  updateInput();
  
  curTime = millis();
  
  if (curTime - lastTime > updateInterval){ 
    // only bother to encode GPS data about 1 a second since it's only a 1hz output anyway
    while (Serial1.available()){
      gps.encode(Serial1.read());
    }
    
    lastTime = curTime;
    
    getEnvironmentalData();
    
    Serial.print(" LON: "); Serial.print(gps.location.lng(), 4);
    Serial.print(" LAT: "); Serial.println(gps.location.lat(), 4);
    
  }
  
}

void updateInput(){

  rawVolume = analogRead(PIN_VOL);
  curVolume = map(rawVolume, 0, 1023, 0, 100);
  switchState = !digitalRead(PIN_SW_AUDIO);
  
  buttonSystem.update();
  buttonStatus.update();
  buttonData.update();
  buttonClose.update();
  buttonEnter.update();

  if (buttonSystem.fallingEdge()) {
    Keyboard.press(KEY_Z);
    Keyboard.release(KEY_Z);
    digitalWrite(LED_SYSTEM, HIGH); // This could be more elegant, but there are only three static modes, so this is faster
    digitalWrite(LED_STATUS, LOW);
    digitalWrite(LED_DATA, LOW);
  }
  if (buttonStatus.fallingEdge()) {
    Keyboard.press(KEY_X);
    Keyboard.release(KEY_X);
    digitalWrite(LED_SYSTEM, LOW);
    digitalWrite(LED_STATUS, HIGH);
    digitalWrite(LED_DATA, LOW);
  }
  if (buttonData.fallingEdge()) {
    Keyboard.press(KEY_C);
    Keyboard.release(KEY_C);
    digitalWrite(LED_SYSTEM, LOW);
    digitalWrite(LED_STATUS, LOW);
    digitalWrite(LED_DATA, HIGH);
  }
  if (buttonClose.fallingEdge()) {
    Keyboard.press(KEY_V);
    Keyboard.release(KEY_V);
    digitalWrite(LED_CLOSE, HIGH);
  }
  if (buttonEnter.fallingEdge()) {
    Keyboard.press(KEY_SPACE);
    Keyboard.release(KEY_SPACE);
  }
  if (buttonClose.risingEdge()) {
    digitalWrite(LED_CLOSE, LOW);
  }

  long newScrollPos = encoderScroll.read();
  long newTabPos = encoderTab.read();
  
  if (abs(newScrollPos - lastScrollPos) >= 4) { // there are roughly four presses detected from each rotation to the next detent
    if (newScrollPos - lastScrollPos > -1){ // positive increase
      Keyboard.press(KEY_W);
      Keyboard.release(KEY_W); 
    } else {
      Keyboard.press(KEY_S);
      Keyboard.release(KEY_S);
    }
    lastScrollPos = newScrollPos;
  }
  
  if (abs(newTabPos - lastTabPos) >= 4) { // there are roughly four presses detected from each rotation to the next detent
    if (newTabPos - lastTabPos > -1){ // positive increase
      Keyboard.press(KEY_D);
      Keyboard.release(KEY_D);
    } else {
      Keyboard.press(KEY_A);
      Keyboard.release(KEY_A);
    }
    lastTabPos = newTabPos;
  }
  
}

void getEnvironmentalData(){
 
  uint8_t ADDRESS_AMBIMATE_SENSOR = 0x2A;
  uint8_t REGISTER_START_SCAN = 0xC0;

  // Individual sensor addresses
  uint8_t REGISTER_STATUS = 0x00;
  uint8_t REGISTER_TEMP_HIGH = 0x01;
  uint8_t REGISTER_TEMP_LOW = 0x02;
  uint8_t REGISTER_HUMID_HIGH = 0x03;
  uint8_t REGISTER_HUMID_LOW = 0x04;
  uint8_t REGISTER_LIGHT_HIGH = 0x05;
  uint8_t REGISTER_LIGHT_LOW = 0x06;
  uint8_t REGISTER_CO2_HIGH = 0x0B;
  uint8_t REGISTER_CO2_LOW = 0x0C;
  uint8_t REGISTER_VOC_HIGH = 0x0D;
  uint8_t REGISTER_VOC_LOW = 0x0E;

  uint8_t read_data[16];

  // Request that all sensor registers update
  Wire.beginTransmission(ADDRESS_AMBIMATE_SENSOR);
  Wire.write(REGISTER_START_SCAN);
  Wire.write(0xFF); // set all sensor bits to update
  Wire.endTransmission();

  Wire.beginTransmission(ADDRESS_AMBIMATE_SENSOR);
  Wire.write(REGISTER_STATUS);
  Wire.endTransmission();
  
  Wire.requestFrom(ADDRESS_AMBIMATE_SENSOR, 15);

  int n = 0;
  while (Wire.available()){
    read_data[n] = Wire.read();
    n++;
  }

  //boolean state_motion = bitRead(read_data[0])
  float temp_C = float(read_data[1] * 256 + read_data[2]) / 10.0;
  float temp_F = 32.0 + ((9.0 / 5.0) * temp_C);
  float lvl_rel_humidity = float(read_data[3] * 256 + read_data[4]) / 10.0;
  int lvl_amb_light = read_data[5] * 256 + read_data[6];
  int lvl_CO2 = read_data[11] * 256 + read_data[12];
  int lvl_VOC = read_data[13] * 256 + read_data[14];

  //Serial.print("Motion: "); Serial.println(state_motion);
  //Serial.print("Temp C: "); Serial.println(temp_C);
  Serial.print("Temp F: "); Serial.print(temp_F);
  Serial.print(" Humidity: "); Serial.print(lvl_rel_humidity);
  //Serial.print("Light: "); Serial.println(lvl_amb_light);
  /* 
   *  CO2 < 350 (Fresh/Outdoor)
   *  350 < CO2 < 1,000 (Avg Indoor) 
   *  1,000 CO2 < 2,000 (Poor, drowsiness)
   *  2,000 < CO2 < 5,000 (Very Poor, stagnant, physcial discomfort)
   *  5Kppm < CO2 < 40Kppm (Hazardous)
   *  C02 > 40Kppm (Lethal)
  */ 
  Serial.print(" AIR: "); Serial.print(float(lvl_CO2)); // the python code will only properly parse floating point values
  //Serial.print("VOC: "); Serial.println(lvl_VOC);
   
}

