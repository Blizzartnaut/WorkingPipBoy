//Serial out for arduino sensor package
//Pins for sensors

const int MQ4 = 10;   //Pin for Sensor Package
const int MQ6 = 11; //These are ADC
const int MQ135 = 9;  //Pins for analog signals
const int potPin = A1; // Analog pin connected to the potentiometer wiper

//Geiger counter pin and setup
volatile unsigned long pulseCount = 0; // counts pulses in the current interval
volatile int pulseClicks = 0;           // Count pulses for click generation
unsigned long previousMillis = 0;
const unsigned long interval = 1000;  // Interval for counting (in milliseconds)
const int interruptPin = 2;           // Change this to the Arduino pin connected to the geiger tube's interrupt output

//Pin for piezo speaker
const int piezoPin = 3;
//static const int DHT_SENSOR_PIN = 7;

//Pins for screen selector
const int s1 = 44;  //Pins for D(44, 46, 48, 50, 52)
const int s2 = 46;
const int s3 = 48;
const int s4 = 50;
const int s5 = 52;
int screen = 1;

//#include <dht_nonblocking.h>

/* Uncomment according to your sensortype. */
//#define DHT_SENSOR_TYPE DHT_TYPE_11
//#define DHT_SENSOR_TYPE DHT_TYPE_21
//#define DHT_SENSOR_TYPE DHT_TYPE_22

//DHT_nonblocking dht_sensor( DHT_SENSOR_PIN, DHT_SENSOR_TYPE );

// Interrupt Service Routine (ISR): Called each time a rising edge is detected on interruptPin. For Geiger counter
void countPulse() {
  pulseCount++;  // Increment the pulse counter
  pulseClicks++;
}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(19200); //Starts serial port with Baud of 9600 bits per second
  pinMode(interruptPin, INPUT);       // Set the interruptPin as an input
  // attachInterrupt tells the Arduino to call countPulse() whenever a rising edge occurs on the interruptPin.
  attachInterrupt(digitalPinToInterrupt(interruptPin), countPulse, RISING);
}

/*static bool measure_environment( float *temperature, float *humidity )
{
  static unsigned long measurement_timestamp = millis( );

  /* Measure once every four seconds. */
  /*if( millis( ) - measurement_timestamp > 3000ul )
  {
    if( dht_sensor.measure( temperature, humidity ) == true )
    {
      measurement_timestamp = millis( );
      return( true );
    }
  }

  return( false );
}*/

// --- Variables for managing click timing ---
unsigned long lastClickTime = 0;
const unsigned long clickInterval = 13;  // Minimum time (ms) between clicks

void loop() {
  // put your main code here, to run repeatedly:
  int sens4 = analogRead(MQ4);  //Reads ADC Pin
  int sens6 = analogRead(MQ6);   //^
  int sens135 = analogRead(MQ135);  //^
  // Read analog value (0-1023)
  int analogValue = analogRead(potPin);

  int val1 = digitalRead(s1); //to store values for screen select
  int val2 = digitalRead(s2);
  int val3 = digitalRead(s3);
  int val4 = digitalRead(s4);
  int val5 = digitalRead(s5);

  // Map the analog value to a range of 0-99
  int volume = map(analogValue, 0, 1023, 0, 99);

  unsigned long currentMillis = millis();  // Get the current time in milliseconds

  // Check if one second has passed since the last measurement.
  if (currentMillis - previousMillis >= interval) {
    noInterrupts();              // Disable interrupts to ensure pulseCount is read atomically
    unsigned long cps = pulseCount;  // Copy the current pulse count into a local variable (cps = counts per second)
    pulseCount = 0;              // Reset the global pulse count for the next interval
    interrupts();                // Re-enable interrupts

  /* Measure temperature and humidity.  If the functions returns
     true, then a measurement is available. */

  if (val1 == 1){
    screen = 1;}
  else if(val2 == 1){
    screen = 2;}
  else if(val3 == 1){
    screen = 3;}
  else if(val4 == 1){
    screen = 4;}
  else if(val5 == 1){
    screen = 5;}

  // float temp;
  // float humidity;

  /* Measure temperature and humidity.  If the functions returns
     true, then a measurement is available. */
  //if( measure_environment( &temp, &humidity ) == true )

  // Try to measure environment (temp and humidity)
  //bool envMeasured = measure_environment(&temperature, &humidity)
  //if not measured keep previous reading or send 0

  //Serial.print("MQ4,"); //Sets up reciever to parse message correctly using white space for seperate values
  Serial.print(sens4);
  Serial.print(",");

  //Serial.print("MQ6,");
  Serial.print(sens6);
  Serial.print(",");

  //Serial.print("MQ135,"); //Sets up reciever to parse message correctly using white space for seperate values
  Serial.print(sens135);
  Serial.print(",");

  //Serial.print("CPS,"); //Sets up reciever to parse message correctly using white space for seperate values
  Serial.print(cps);
  Serial.print(",");

  //Serial.print("RAD,"); //Sets up reciever to parse message correctly using white space for seperate values
  Serial.print(temp);
  Serial.print(",");

  Serial.print( (int)round(1.8*temp+32));
  Serial.print(",");
  
  //Serial.print("Screen,"); //Sets up reciever to parse message correctly using white space for seperate values
  Serial.print(screen);
  Serial.print(",");

  Serial.print(volume);
  Serial.print('\n');

  previousMillis = currentMillis; // Update previousMillis to the current time for the next 1-second interval

  }
  
  // --- Process Piezo Clicks ---
  // Check if there are any pending pulse clicks and enough time has passed
  if (pulseClicks > 0 && (currentMillis - lastClickTime > clickInterval)) {
    tone(piezoPin, 1500, 10);  // Generate a 2000Hz tone for 10ms (adjust frequency/duration as desired)
    lastClickTime = currentMillis; // Update last click time
    pulseClicks--;  // Process one click
  }
}