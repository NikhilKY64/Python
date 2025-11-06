/* --- Firefighting Robot: De-glitched & Debounced --- */

#define ENA 3
#define ENB 9          // use PWM-capable pin for better control
#define IN1 4
#define IN2 5
#define IN3 6
#define IN4 7

#define FLAME_LEFT   A1
#define FLAME_CENTER A2
#define FLAME_RIGHT  A3

#define WATER_PUMP 2
#define RELAY_ON   LOW     // set to HIGH if your relay is active-HIGH
#define RELAY_OFF  HIGH

// Sensor behavior: many flame modules pull LOW when flame detected.
// If yours go HIGH on flame, set SENSORS_ACTIVE_LOW to 0.
#define SENSORS_ACTIVE_LOW 1

// Filtering / timing
#define SAMPLES        7      // odd number for majority vote
#define SAMPLE_DELAY   5      // ms between sensor samples
#define MIN_PUMP_ON    1200   // ms minimum ON time
#define MIN_PUMP_OFF   600    // ms minimum OFF time
#define DRIVE_SPEED    200    // 0..255

unsigned long lastPumpChange = 0;
bool pumpState = false; // false = OFF

inline bool rawFlameRead(int pin) {
  int v = digitalRead(pin);
  return SENSORS_ACTIVE_LOW ? (v == LOW) : (v == HIGH);
}

// Majority vote across SAMPLES
bool flameStable(int pin) {
  int count = 0;
  for (int i = 0; i < SAMPLES; i++) {
    if (rawFlameRead(pin)) count++;
    delay(SAMPLE_DELAY);
  }
  return count > (SAMPLES / 2);
}

void motorsEnable(uint8_t spd) {
  analogWrite(ENA, spd);
  analogWrite(ENB, spd);        // both on PWM now
}

void motorsStop() {
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
  digitalWrite(IN1, LOW); digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW); digitalWrite(IN4, LOW);
}

void forward(uint8_t spd) {
  motorsEnable(spd);
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
}
void leftTurn(uint8_t spd) {
  motorsEnable(spd);
  digitalWrite(IN1, LOW);  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
}
void rightTurn(uint8_t spd) {
  motorsEnable(spd);
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);  digitalWrite(IN4, HIGH);
}

void setPump(bool on) {
  // Enforce min ON/OFF time to prevent chatter
  unsigned long now = millis();
  if (on && !pumpState && (now - lastPumpChange) < MIN_PUMP_OFF) return;
  if (!on && pumpState && (now - lastPumpChange) < MIN_PUMP_ON)  return;

  pumpState = on;
  digitalWrite(WATER_PUMP, on ? RELAY_ON : RELAY_OFF);
  lastPumpChange = now;
}

void setup() {
  pinMode(ENA, OUTPUT); pinMode(ENB, OUTPUT);
  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT);
  motorsStop();

  // Use pull-ups to avoid floating inputs
  pinMode(FLAME_LEFT,   INPUT_PULLUP);
  pinMode(FLAME_CENTER, INPUT_PULLUP);
  pinMode(FLAME_RIGHT,  INPUT_PULLUP);

  pinMode(WATER_PUMP, OUTPUT);
  digitalWrite(WATER_PUMP, RELAY_OFF); // OFF at boot
  lastPumpChange = millis();

  Serial.begin(9600);
  Serial.println("De-glitched firefighting robot ready");
}

void loop() {
  // Debounced sensor reads
  bool L = flameStable(FLAME_LEFT);
  bool C = flameStable(FLAME_CENTER);
  bool R = flameStable(FLAME_RIGHT);

  // Debug
  Serial.print("L="); Serial.print(L);
  Serial.print(" C="); Serial.print(C);
  Serial.print(" R="); Serial.print(R);
  Serial.print(" | Pump="); Serial.println(pumpState);

  // Decide motion
  if (C) {
    motorsStop();
    setPump(true);                 // keep ON for at least MIN_PUMP_ON
  } else if (L && !R) {
    setPump(false);
    leftTurn(DRIVE_SPEED);
  } else if (R && !L) {
    setPump(false);
    rightTurn(DRIVE_SPEED);
  } else if (L && R) {
    setPump(false);
    forward(DRIVE_SPEED - 30);
  } else {
    setPump(false);
    forward(DRIVE_SPEED);
  }

  // Small loop delay; most timing handled by sampling and min ON/OFF guards
  delay(20);
}
