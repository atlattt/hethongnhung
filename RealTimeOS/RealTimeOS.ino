
#include <Arduino.h>


TaskHandle_t task1Handle = NULL;
TaskHandle_t task2Handle = NULL;

void task1(void *parameter) {
  const int LED_PIN=2;

  pinMode(LED_PIN, OUTPUT);
  while(1) {
    digitalWrite(LED_PIN,HIGH);
    Serial.println("LED bật");
    vTaskDelay(1000/portTICK_PERIOD_MS);

    
    digitalWrite(LED_PIN,LOW);
    Serial.println("LED tắt");
    vTaskDelay(1000/portTICK_PERIOD_MS);
  }
}

void task2(void *parameter){
  while(1) {
    Serial.println("Task giám sát đang chạy ....");
    vTaskDelay(3000/portTICK_PERIOD_MS);
    }  
}
void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);

  xTaskCreatePinnedToCore(
    task1,
    "LED TASK",
    (uint16_t)2048,
    NULL,
    3,
    &task1Handle,
    0
    );
    
  xTaskCreatePinnedToCore(
    task2,
    "MONITOR TASK",
    (uint16_t)2048,
    NULL,
    2,
    &task2Handle,
    1
    );
}

void loop() {
  // put your main code here, to run repeatedly:

}
