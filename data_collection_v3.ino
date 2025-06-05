#include <Arduino.h>
#include <driver/i2s.h>
#include <WiFi.h>

// ====== THIẾT LẬP ======
#define SAMPLE_BUFFER_SIZE 512
#define SAMPLE_RATE 16000

#define I2S_MIC_CHANNEL I2S_CHANNEL_FMT_ONLY_LEFT

#define I2S_MIC_SERIAL_CLOCK GPIO_NUM_14
#define I2S_MIC_LEFT_RIGHT_CLOCK GPIO_NUM_15
#define I2S_MIC_SERIAL_DATA GPIO_NUM_32

// WiFi settings
const char* ssid = "ATLAT";
const char* password = "12345678";
bool wifi_connected = false;

// Server settings
const int serverPort = 8888;
WiFiServer server(serverPort);
WiFiClient client;

// ====== CẤU HÌNH I2S ======
i2s_config_t i2s_config = {
  .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
  .sample_rate = SAMPLE_RATE,
  .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
  .channel_format = I2S_MIC_CHANNEL,
  .communication_format = I2S_COMM_FORMAT_I2S,
  .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
  .dma_buf_count = 4,
  .dma_buf_len = 1024,
  .use_apll = false,
  .tx_desc_auto_clear = false,
  .fixed_mclk = 0
};

i2s_pin_config_t i2s_mic_pins = {
  .bck_io_num = I2S_MIC_SERIAL_CLOCK,
  .ws_io_num = I2S_MIC_LEFT_RIGHT_CLOCK,
  .data_out_num = I2S_PIN_NO_CHANGE,
  .data_in_num = I2S_MIC_SERIAL_DATA
};

// ====== TASK KIỂM TRA VÀ QUẢN LÝ KẾT NỐI WIFI ======
void wifi_monitor_task(void *parameter) {
  int retryCount = 0;
  const int maxRetries = 10;
  
  while(true) {
    if(WiFi.status() != WL_CONNECTED) {
      if(wifi_connected) {
        Serial.println("WiFi đã ngắt kết nối!");
        wifi_connected = false;
        // Nếu server đang chạy, dừng lại
        server.end();
      }
      
      // Thử kết nối lại
      if(retryCount < maxRetries || maxRetries == 0) {
        Serial.println("Đang kết nối lại WiFi...");
        WiFi.disconnect();
        WiFi.begin(ssid, password);
        
        // Đợi tối đa 10 giây cho kết nối
        unsigned long startAttemptTime = millis();
        while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < 10000) {
          Serial.print(".");
          vTaskDelay(pdMS_TO_TICKS(500));
        }
        
        if(WiFi.status() == WL_CONNECTED) {
          Serial.println("\nWiFi đã kết nối lại thành công");
          Serial.print("Địa chỉ IP: ");
          Serial.println(WiFi.localIP());
          wifi_connected = true;
          retryCount = 0;
          
          // Khởi động lại server
          server.begin();
          Serial.print("TCP Server khởi động lại tại cổng: ");
          Serial.println(serverPort);
        } else {
          retryCount++;
          Serial.print("Kết nối thất bại. Lần thử: ");
          Serial.println(retryCount);
        }
      } else {
        Serial.println("Quá nhiều lần thử kết nối không thành công. Khởi động lại ESP...");
        ESP.restart();
      }
    } else if(!wifi_connected) {
      // WiFi đã kết nối nhưng cờ chưa được cập nhật
      Serial.println("WiFi đã kết nối");
      Serial.print("Địa chỉ IP: ");
      Serial.println(WiFi.localIP());
      wifi_connected = true;
      retryCount = 0;
      
      // Đảm bảo server đang chạy
      server.begin();
      Serial.print("TCP Server bắt đầu tại cổng: ");
      Serial.println(serverPort);
    }
    
    // Kiểm tra mỗi 5 giây
    vTaskDelay(pdMS_TO_TICKS(5000));
  }
}

// ====== TASK GHI ÂM VÀ STREAM TCP ======
void i2s_stream_task(void *arg) {
  int32_t raw_samples[SAMPLE_BUFFER_SIZE];
  size_t bytes_read;

  while (true) {
    // Chỉ tiếp tục nếu WiFi đã kết nối
    if (!wifi_connected) {
      vTaskDelay(pdMS_TO_TICKS(1000));
      continue;
    }

    if (!client || !client.connected()) {
      Serial.println("Đang chờ client kết nối...");
      client = server.available();  // Đợi client mới
      vTaskDelay(pdMS_TO_TICKS(1000));
      continue;
    }

    // Đọc dữ liệu từ microphone
    i2s_read(I2S_NUM_0, raw_samples, sizeof(raw_samples), &bytes_read, portMAX_DELAY);

    // Gửi qua TCP
    if (client.connected()) {
      client.write((const uint8_t*)raw_samples, bytes_read);
    } else {
      Serial.println("Client đã ngắt kết nối.");
    }
  }
}

// ====== HÀM SETUP ======
void setup() {
  Serial.begin(115200);
  Serial.println("\nBắt đầu khởi động ESP32 Audio Server");

  // Khởi tạo WiFi ở chế độ Station
  WiFi.mode(WIFI_STA);
  Serial.println("Đang kết nối WiFi ban đầu...");
  WiFi.begin(ssid, password);

  // Khởi tạo I2S
  i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &i2s_mic_pins);
  Serial.println("I2S đã được khởi tạo");

  // Tạo task quản lý WiFi
  xTaskCreate(
    wifi_monitor_task,   // Hàm xử lý
    "WiFi_Monitor",      // Tên task
    4096,                // Stack size
    NULL,                // Tham số
    1,                   // Độ ưu tiên
    NULL                 // Không cần handle
  );

  // Tạo task ghi âm và stream qua TCP
  xTaskCreate(
    i2s_stream_task,     // Hàm xử lý
    "I2S_Stream",        // Tên task
    4096,                // Stack size
    NULL,                // Tham số
    1,                   // Độ ưu tiên
    NULL                 // Không cần handle
  );
  
  Serial.println("Các task đã được khởi tạo");
}

// ====== VÒNG LẶP CHÍNH ======
void loop() {
  // Không cần làm gì, mọi thứ do FreeRTOS xử lý
  delay(1000);  // Giảm tải cho CPU khi không cần xử lý gì trong loop()
}
