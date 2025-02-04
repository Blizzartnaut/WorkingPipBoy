//Serial out for arduino sensor package
//Pins for sensors

const int MQ4 = 9;   //Pin for Sensor Package
const int MQ6 = 10; //These are ADC
const int MQ135 = 11;  //Pins for analog signals
const int RAD = 4;  //Digital Pin for counting rads
const int Humid = 7;
const int Temp = 6;

//Pins for screen selector
const int s1 = 44;  //Pins for D(44, 46, 48, 50, 52)
const int s2 = 46;
const int s3 = 48;
const int s4 = 50;
const int s5 = 52;
int screen = 1;

#include <dht_nonblocking.h>

/* Uncomment according to your sensortype. */
#define DHT_SENSOR_TYPE DHT_TYPE_11
//#define DHT_SENSOR_TYPE DHT_TYPE_21
//#define DHT_SENSOR_TYPE DHT_TYPE_22

static const int DHT_SENSOR_PIN = 2;
DHT_nonblocking dht_sensor( DHT_SENSOR_PIN, DHT_SENSOR_TYPE );

void setup() {
  // put your setup code here, to run once:
  Serial.begin(19200); //Starts serial port with Baud of 9600 bits per second
}

static bool measure_environment( float *temperature, float *humidity )
{
  static unsigned long measurement_timestamp = millis( );

  /* Measure once every four seconds. */
  if( millis( ) - measurement_timestamp > 3000ul )
  {
    if( dht_sensor.measure( temperature, humidity ) == true )
    {
      measurement_timestamp = millis( );
      return( true );
    }
  }

  return( false );
}

void loop() {
  // put your main code here, to run repeatedly:
  int sens4 = analogRead(MQ4);  //Reads ADC Pin
  int sens6 = analogRead(MQ6);   //^
  int sens135 = analogRead(MQ135);  //^
  int rad = digitalRead(RAD); //Reads Digital Pin (1 or 0) count or no count, higher baud rate?

  int val1 = digitalRead(s1); //to store values for screen select
  int val2 = digitalRead(s2);
  int val3 = digitalRead(s3);
  int val4 = digitalRead(s4);
  int val5 = digitalRead(s5);

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

  float temperature = 0.0;
  float humidity = 0.0;

  // Try to measure environment (temp and humidity)
  bool envMeasured = measure_environment(&temperature, &humidity)
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

  //Serial.print("RAD,"); //Sets up reciever to parse message correctly using white space for seperate values
  Serial.print(rad);
  Serial.print(",");

  //Serial.print("RAD,"); //Sets up reciever to parse message correctly using white space for seperate values
  Serial.print(temperature);
  Serial.print(",");

  Serial.print(humidity);
  Serial.print(",");
  
  //Serial.print("Screen,"); //Sets up reciever to parse message correctly using white space for seperate values
  Serial.print(screen);
  Serial.print("\n");

  delay(1000); //Allows for Radiation count of 6000CPM (delay of 10)

  //100CPM is warning level
  //
  //10,000 is dangerous with an increase of cancer risk
  //Still tolerable for a day.
}
