#include "esp_camera.h"
#include <WiFi.h>
#include "esp_http_server.h"

// --- CẤU HÌNH PIN XIAO S3 SENSE ---
#define PWDN_GPIO_NUM  -1
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM  10
#define SIOD_GPIO_NUM  40
#define SIOC_GPIO_NUM  39
#define Y9_GPIO_NUM    48
#define Y8_GPIO_NUM    11
#define Y7_GPIO_NUM    12
#define Y6_GPIO_NUM    14
#define Y5_GPIO_NUM    16
#define Y4_GPIO_NUM    18
#define Y3_GPIO_NUM    17
#define Y2_GPIO_NUM    15
#define VSYNC_GPIO_NUM 38
#define HREF_GPIO_NUM  47
#define PCLK_GPIO_NUM  13

const char* ssid = "WIFI_PROMAX_ULTIMATE";
const char* pass = "12345678";

httpd_handle_t capture_httpd = NULL;

// --- HÀM XỬ LÝ CHỤP 1 ẢNH ---
static esp_err_t capture_handler(httpd_req_t *req) {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    httpd_resp_send_500(req);
    return ESP_FAIL;
  }

  esp_err_t res = httpd_resp_set_type(req, "image/jpeg");
  if (res == ESP_OK) {
    res = httpd_resp_send(req, (const char *)fb->buf, fb->len);
  }
  esp_camera_fb_return(fb);
  return res;
}

void setup() {
  Serial.begin(115200);

  // Cấu hình Camera
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM; config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM; config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM; config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM; config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM; config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM; config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM; config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM; config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.grab_mode = CAMERA_GRAB_LATEST;

  if (psramFound()) {
    config.frame_size = FRAMESIZE_VGA;
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_QVGA;
    config.fb_count = 1;
  }

  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("Lỗi khởi tạo Camera!");
    return;
  }

  // Phát WiFi (Access Point)
  WiFi.softAP(ssid, pass);

  // Khởi động Server ảnh tĩnh (cổng 81)
  httpd_config_t st_config = HTTPD_DEFAULT_CONFIG();
  st_config.server_port = 81;

  // Định nghĩa đường dẫn /capture (mỗi request trả 1 ảnh)
  httpd_uri_t capture_uri = {
    .uri       = "/capture",
    .method    = HTTP_GET,
    .handler   = capture_handler,
    .user_ctx  = NULL
  };

  if (httpd_start(&capture_httpd, &st_config) == ESP_OK) {
    httpd_register_uri_handler(capture_httpd, &capture_uri);
  }

  Serial.println("\n--- HỆ THỐNG ĐÃ SẴN SÀNG ---");
  Serial.print("Vào link này để chụp 1 ảnh: http://");
  Serial.print(WiFi.softAPIP());
  Serial.println(":81/capture");
}

void loop() {
  delay(1000);
}