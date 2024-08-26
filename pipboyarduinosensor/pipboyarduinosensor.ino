//Serial out for arduino sensor package
//Pins for sensors

const int MQ4 = 9;   //Pin for Sensor Package
const int MQ6 = 10; //These are ADC
const int MQ135 = 11;  //Pins for analog signals
const int RAD = 4;  //Digital Pin for counting rads

//Pins for screen selector
const int s1 = 13;  //Pins for D13 - D9
const int s2 = 12;
const int s3 = 11;
const int s4 = 10;
const int s5 = 9;
int screen = 1;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(19200); //Starts serial port with Baud of 9600 bits per second
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

  if (val1 == 1){
    screen = 1;}
  else if(val2 == 1){
    screen = 2;}
  else if(val3 == 1){
    screen = 3;}
  else if(val4 == 1){
    screen = 4;}
  else if(val5 == 4){
    screen = 5;}

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

  //Serial.print("Screen,"); //Sets up reciever to parse message correctly using white space for seperate values
  Serial.print(screen);
  Serial.print("\n");

  delay(1000); //Allows for Radiation count of 6000CPM (delay of 10)

  //100CPM is warning level
  //
  //10,000 is dangerous with an increase of cancer risk
  //Still tolerable for a day.
}
