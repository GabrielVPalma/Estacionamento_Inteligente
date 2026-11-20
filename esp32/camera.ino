#include "secrets.h"
#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

// Mapeamento de pinos da placa AI-Thinker ESP32-CAM
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// =========================================================================
// CREDENCIAIS DA REDE WI-FI (PREENCHA ANTES DE FAZER O UPLOAD)
// =========================================================================
const char* ssid = WIFI_SSID;
const char* password = WIFI_PASSWORD;

WebServer server(80);

// Rota HTTP que captura e envia um frame JPEG quando requisitada pelo Python
void handleCapture() {
  camera_fb_t * fb = esp_camera_fb_get();
  if (!fb) {
    server.send(500, "text/plain", "Erro ao capturar imagem da camera");
    return;
  }
  
  server.sendHeader("Content-Type", "image/jpeg");
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send_P(200, "image/jpeg", (const char *)fb->buf, fb->len);
  
  // Libera a memória do buffer para o próximo frame
  esp_camera_fb_return(fb);
}

void setup() {
  // Desativa o detector de Brownout para evitar reinicializações por picos do Wi-Fi
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

  Serial.begin(115200);
  delay(1000);

  // Configurações de hardware da câmera
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  
  // Clock em 10MHz evita o superaquecimento do sensor OV2640
  config.xclk_freq_hz = 10000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_VGA; // Resolução 640x480
  config.jpeg_quality = 12;          // Qualidade JPEG (menor = melhor qualidade)
  config.fb_count = 1;

  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("Falha ao inicializar a camera!");
    return;
  }

  // Ajustes do sensor para estabilizar cores e evitar tonalidade rosa/roxa
  sensor_t * s = esp_camera_sensor_get();
  if (s != NULL) {
    s->set_whitebal(s, 1);       // Balanço de branco automático (AWB) ligado
    s->set_awb_gain(s, 1);       // Ganho de AWB ligado
    s->set_wb_mode(s, 0);        // Modo automático
    s->set_exposure_ctrl(s, 1);  // Exposição automática
    s->set_gain_ctrl(s, 1);      // Controle de ganho automático
    s->set_brightness(s, 0);     // Brilho neutro
    s->set_saturation(s, -1);    // Reduz levemente a saturação de cor
  }

  // Conexão com o Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Conectando a rede Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWi-Fi Conectado!");
  Serial.print("Endereco IP da camera: http://");
  Serial.println(WiFi.localIP());

  // Inicializa o servidor web na rota /capture
  server.on("/capture", handleCapture);
  server.begin();
}

void loop() {
  server.handleClient();
  delay(50); // Pausa breve para estabilidade térmica e de rede
}