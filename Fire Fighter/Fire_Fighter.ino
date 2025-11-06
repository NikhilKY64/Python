/* ================================================================
   Firefighting Robot – Startup-Safe, Ultra-Fast Analog Response
   - No pump flicker at power-on (software-only fix)
   - Instant fire detection via analog AO inputs
   - L298N motor driver pins included (motors optional to debug later)
   ================================================================ */

#define ENA 3
#define ENB 9
#define IN1 4
#define IN2 5
#define IN3 6
#define IN4 7

// Use AO outputs of the flame sensors:
#define FLAME_LEFT   A1
#define FLAME_CENTER A2
#define FLAME_RIGHT  A3

// Pump control (relay or MOSFET on D2)
#define WATER_PUMP 2
#define RELAY_ON   LOW      // change to HIGH if your board is active-HIGH
#define RELAY_OFF  HIGH

// Tuning
#define THRESHOLD    400    // lower = more sensitive; calibrate with Serial if needed
#define DRIVE_SPEED  220
#define MIN_PUMP_ON  300    // ms (short debounce to prevent chatter)
#define MIN_PUMP_OFF 150

// State
bool pumpState = false;
unsigned long lastPumpChange_us = 0;

// ----------------- Inline Motor Helpers -----------------
inline void motorsStop() {
  analogWrite(ENA, 0); analogWrite(ENB, 0);
  digitalWrite(IN1, LOW); digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW); digitalWrite(IN4, LOW);
}
inline void forward(uint8_t spd) {
  analogWrite(ENA, spd); analogWrite(ENB, spd);
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
}
inline void leftTurn(uint8_t spd) {
  analogWrite(ENA, spd/2); analogWrite(ENB, spd);
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
}
inline void rightTurn(uint8_t spd) {
  analogWrite(ENA, spd); analogWrite(ENB, spd/2);
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
}

// ----------------- Pump Control (startup-safe) -----------------
inline void setPump(bool on) {
  unsigned long now_us = micros();
  if (on && !pumpState && (now_us - lastPumpChange_us) < (MIN_PUMP_OFF * 1000UL)) return;
  if (!on && pumpState && (now_us - lastPumpChange_us) < (MIN_PUMP_ON  * 1000UL)) return;
  pumpState = on;
  digitalWrite(WATER_PUMP, on ? RELAY_ON : RELAY_OFF);
  lastPumpChange_us = now_us;
}

// ----------------- Setup -----------------
void setup() {
  // --- SOFTWARE-ONLY STARTUP FIX: force pump OFF before pinMode ---
  digitalWrite(WATER_PUMP, RELAY_OFF);  // bias line safely using internal circuitry
  pinMode(WATER_PUMP, OUTPUT);          // now make it an output already OFF

  // Motor pins
  pinMode(ENA, OUTPUT); pinMode(ENB, OUTPUT);
  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT);
  motorsStop();

  // (Optional) Speed up ADC for faster analogRead (~13µs):
  bitClear(ADCSRA, ADPS2); bitSet(ADCSRA, ADPS1); bitClear(ADCSRA, ADPS0);

  // If you want to calibrate later, you can enable Serial prints.
  // Serial.begin(9600);
}

// ----------------- Main Loop -----------------
void loop() {
  // Ultra-fast analog reads from AO pins
  int L = analogRead(FLAME_LEFT);
  int C = analogRead(FLAME_CENTER);
  int R = analogRead(FLAME_RIGHT);

  bool fireL = (L < THRESHOLD);
  bool fireC = (C < THRESHOLD);
  bool fireR = (R < THRESHOLD);

  // Immediate reaction to center flame
  if (fireC) {
    motorsStop();
    setPump(true);
  } else if (fireL && !fireR) {
    setPump(false);
    leftTurn(DRIVE_SPEED);
  } else if (fireR && !fireL) {
    setPump(false);
    rightTurn(DRIVE_SPEED);
  } else if (fireL && fireR) {
    setPump(false);
    forward(DRIVE_SPEED - 40);
  } else {
    setPump(false);
    forward(DRIVE_SPEED);
  }

  // No delay() → continuous fast loop
  // (Leave out Serial.prints for max speed; add only when calibrating.)
}
