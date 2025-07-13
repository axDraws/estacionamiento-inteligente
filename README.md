# 🚗 Estacionamiento Inteligente

Sistema de control de acceso vehicular para un fraccionamiento o condominio, que permite la entrada y salida de **residentes con tarjetas RFID** y de **visitantes mediante formulario QR**, usando una arquitectura híbrida: **Flask (backend web) + SQLite (base de datos) + Arduino (control físico de servos y pantalla OLED).**

---

## 📦 Tecnologías utilizadas

- 🐍 Python + Flask
- 🗃️ SQLite
- 💡 Arduino UNO
- 📶 Módulo RFID RC522
- 📟 Pantalla OLED I2C
- ⚙️ Servomotores SG90
- 🌐 HTML + CSS + JS
- 📲 QR para formulario de visitante

---

## 🧠 Funcionalidades principales

### 👤 Residentes

- Registro de residentes con UID de su tarjeta RFID.
- Acceso automatizado: si la tarjeta está registrada como **fuera**, abre la **entrada**; si está **dentro**, abre la **salida**.
- Se calcula el tiempo de permanencia.

### 🎫 Visitantes

- Acceden a un formulario web escaneando un código QR.
- Ingresan sus datos y el nombre del residente que los autoriza.
- Al enviar el formulario, se abre la pluma de entrada y se registra el acceso en la base de datos.

### 🛠️ Administrador

- Panel web para:
  - Registrar y eliminar residentes.
  - Ver el historial de accesos.
  - Simular la apertura de barreras.
  - Monitorear estado de pantalla OLED.

---

## 🔧 Estructura del proyecto

