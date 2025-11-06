// Define motor control pins (L298N Motor Driver)
#define ENA 3  // PWM for Motor A
#define ENB 8   // PWM for Motor B
#define IN1 4  // Motor A
#define IN2 5
#define IN3 6   // Motor B
#define IN4 7

// Define flame sensor pins
#define FLAME_LEFT A1
#define FLAME_CENTER A2
#define FLAME_RIGHT A3

// Define water pump/fan pin
#define WATER_PUMP 2  

// Motor Speed (0 = Stop, 255 = Full Speed)
int motorSpeed = 120;  // Default speed (Adjustable)

void setup() {
    // Set motor pins as OUTPUT
    pinMode(IN1, OUTPUT);
    pinMode(IN2, OUTPUT);
    pinMode(IN3, OUTPUT);
    pinMode(IN4, OUTPUT);
    pinMode(ENA, OUTPUT);
    pinMode(ENB, OUTPUT);
    
    // Set sensor pins as INPUT
    pinMode(FLAME_LEFT, INPUT);
    pinMode(FLAME_CENTER, INPUT);
    pinMode(FLAME_RIGHT, INPUT);
    
    pinMode(WATER_PUMP, OUTPUT);
    Serial.begin(9600);
}

void loop() {
    int left = digitalRead(FLAME_LEFT);
    int center = digitalRead(FLAME_CENTER);
    int right = digitalRead(FLAME_RIGHT);
    
    Serial.print("Left: "); Serial.print(left);
    Serial.print(" Center: "); Serial.print(center);
    Serial.print(" Right: "); Serial.println(right);

    if (center == 0) {  // Fire detected in front
        stopMotors();
        digitalWrite(WATER_PUMP, HIGH);  // Turn on water pump/fan
        delay(5000);  // Keep spraying for 5 seconds
        digitalWrite(WATER_PUMP, LOW);   // Turn off water pump
    } 
    else if (left == 0) {  // Fire detected on the left
        turnLeft();
    } 
    else if (right == 0) {  // Fire detected on the right
        turnRight();
    } 
    else {
        moveForward();
    }
}

// Move forward with PWM speed control
void moveForward() {
    analogWrite(ENA, motorSpeed);
    analogWrite(ENB, motorSpeed);
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
}

// Turn left by reducing right motor speed
void turnLeft() {
    analogWrite(ENA, 60);  // Reduce left motor speed
    analogWrite(ENB, motorSpeed);
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
    delay(500);
}

// Turn right by reducing left motor speed
void turnRight() {
    analogWrite(ENA, motorSpeed);
    analogWrite(ENB, 60);  // Reduce right motor speed
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
    delay(500);
}

// Stop motors
void stopMotors() {
    analogWrite(ENA, 0);
    analogWrite(ENB, 0);
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, LOW);
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, LOW);
}
