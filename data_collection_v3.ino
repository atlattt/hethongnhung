#include <Arduino.h>
#include <driver/i2s.h>
#include <WiFi.h> // Thư viện WiFi

// Các khai báo hiện tại (SAMPLE_BUFFER_SIZE, SAMPLE_RATE, chân I2S, cấu hình I2S...)
// ...

// You shouldn't need to change these settings

#define SAMPLE_BUFFER_SIZE 512

//#define SAMPLE_RATE 8000
#define SAMPLE_RATE 16000


// Most microphones will default to the left channel, but you may need to tie the L/R pin low

#define I2S_MIC_CHANNEL I2S_CHANNEL_FMT_ONLY_LEFT

// Pin definitions

#define I2S_MIC_SERIAL_CLOCK GPIO_NUM_14

#define I2S_MIC_LEFT_RIGHT_CLOCK GPIO_NUM_15

#define I2S_MIC_SERIAL_DATA GPIO_NUM_32

// I2S configuration

i2s_config_t i2s_config = {

    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),

    .sample_rate = SAMPLE_RATE,

    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,

    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,

    .communication_format = I2S_COMM_FORMAT_I2S,

    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,

    .dma_buf_count = 4,

    .dma_buf_len = 1024,

    .use_apll = false,

    .tx_desc_auto_clear = false,

    .fixed_mclk = 0};


// Pin configuration for I2S

i2s_pin_config_t i2s_mic_pins = {

    .bck_io_num = I2S_MIC_SERIAL_CLOCK,

    .ws_io_num = I2S_MIC_LEFT_RIGHT_CLOCK,

    .data_out_num = I2S_PIN_NO_CHANGE,

    .data_in_num = I2S_MIC_SERIAL_DATA};


// Thông tin WiFi (điền thông tin mạng WiFi của bạn)
const char* ssid = "ATLAT";
const char* password = "12345678";

// Cổng TCP server (chọn một cổng bất kỳ, ví dụ 8888)
const int serverPort = 8888;

WiFiServer server(serverPort);
WiFiClient client; // Client TCP (sẽ được khởi tạo khi có kết nối đến)

// ... (Các khai báo hiện tại)

void setup() {
  Serial.begin(115200);

  // Kết nối WiFi
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP()); // In địa chỉ IP của ESP32

  i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &i2s_mic_pins);

  server.begin(); // Khởi động TCP server
  Serial.print("TCP server started on port ");
  Serial.println(serverPort);
}

// ... (phần còn lại của code)

// ... (Các khai báo và hàm setup như trên)

int32_t raw_samples[SAMPLE_BUFFER_SIZE];  // Buffer for audio data
void loop() {
  if (!client) { // Nếu chưa có client kết nối hoặc client đã ngắt kết nối
    Serial.println("Waiting for client connection...");
    client = server.available(); // Chờ kết nối từ client
    if (client) {
      Serial.println("Client connected!");
    }
  }

  if (client.connected()) { // Nếu có client đang kết nối
    size_t bytes_read = 0;
    i2s_read(I2S_NUM_0, raw_samples, sizeof(int32_t) * SAMPLE_BUFFER_SIZE, &bytes_read, portMAX_DELAY);
//     int samples_read = bytes_read / sizeof(int32_t); // Không cần dùng biến này nữa

    // Gửi dữ liệu âm thanh qua TCP
    client.write((const byte*)raw_samples, bytes_read);

    // (Bỏ phần Serial.println để vẽ đồ thị vì giờ chúng ta stream qua TCP)
//     for (int i = 0; i < samples_read; i++) {
//       Serial.println(raw_samples[i]);
//     }
  } else {
    // Client không kết nối, chờ kết nối mới trong vòng lặp tiếp theo
    delay(1000); // Đợi một chút trước khi kiểm tra lại kết nối
  }
}
