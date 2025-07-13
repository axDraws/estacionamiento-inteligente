#include <Wire.h> // Para la pantalla OLED
#include <Adafruit_GFX.h> // Para la pantalla OLED
#include <Adafruit_SSD1306.h> // Para la pantalla OLED
#include <Servo.h> // Para los servos

// Definiciones para la pantalla OLED
#define SCREEN_WIDTH 128 // Ancho de la pantalla OLED, en píxeles
#define SCREEN_HEIGHT 64 // Alto de la pantalla OLED, en píxeles
#define OLED_RESET -1 // Reset pin # (o -1 si está conectado al reset de Arduino)
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// Definiciones para los Servos
Servo servoEntrada;
Servo servoSalida;

const int PIN_SERVO_ENTRADA = 9; // Pin digital para el servo de entrada
const int PIN_SERVO_SALIDA = 10; // Pin digital para el servo de salida

// Posiciones de los servos
const int POS_CERRADO = 0;   // Ángulo para barrera cerrada
const int POS_ABIERTO = 90;  // Ángulo para barrera abierta

void setup() {
  Serial.begin(9600); // Inicia comunicación serial a 9600 baudios
  while (!Serial); // Espera a que el monitor serial se conecte (solo para placas nativas USB)

  // Iniciar pantalla OLED
  // La dirección I2C común es 0x3C para pantallas 128x64, o 0x3D para otras
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { 
    Serial.println(F("Fallo en la asignación de SSD1306"));
    for(;;); // No continuar si falla
  }
  display.display();
  delay(2000); // Muestra el logo de Adafruit por 2 segundos
  display.clearDisplay();

  // Adjuntar servos a sus pines
  servoEntrada.attach(PIN_SERVO_ENTRADA);
  servoSalida.attach(PIN_SERVO_SALIDA);

  // Posición inicial de los servos (cerrado)
  servoEntrada.write(POS_CERRADO);
  servoSalida.write(POS_CERRADO);

  displayMessage("Sistema de", "Estacionamiento");
  delay(1000);
  displayMessage("Listo", "");
}

void loop() {
  if (Serial.available()) { // Si hay datos disponibles en el puerto serial
    String command = Serial.readStringUntil('\n'); // Lee la cadena hasta el salto de línea
    command.trim(); // Eliminar espacios en blanco y saltos de línea al final

    Serial.print("Comando recibido: ");
    Serial.println(command);

    if (command == "ABRIR_ENTRADA") {
      servoEntrada.write(POS_ABIERTO); // Abrir barrera de entrada
      displayMessage("Barrera Entrada", "ABIERTA");
      delay(3000); // Mantener abierta por 3 segundos
      servoEntrada.write(POS_CERRADO); // Cerrar barrera de entrada
      displayMessage("Barrera Entrada", "CERRADA");
    } else if (command == "ABRIR_SALIDA") {
      servoSalida.write(POS_ABIERTO); // Abrir barrera de salida
      displayMessage("Barrera Salida", "ABIERTA");
      delay(3000); // Mantener abierta por 3 segundos
      servoSalida.write(POS_CERRADO); // Cerrar barrera de salida
      displayMessage("Barrera Salida", "CERRADA");
    } else {
      displayMessage("Comando", "Desconocido");
    }
  }
}

// Función para mostrar mensajes en la pantalla OLED
void displayMessage(String line1, String line2) {
  display.clearDisplay(); // Limpia el buffer de la pantalla
  display.setTextSize(2); // Tamaño de texto 2 (más grande)
  display.setTextColor(SSD1306_WHITE); // Color del texto
  display.setCursor(0, 0); // Posición del cursor (columna, fila)
  display.println(line1); // Imprime la primera línea
  display.setTextSize(1); // Tamaño de texto 1 (más pequeño para la segunda línea)
  display.setCursor(0, 20); // Posición del cursor para la segunda línea
  display.println(line2); // Imprime la segunda línea
  display.display(); // Muestra el contenido del buffer en la pantalla
}