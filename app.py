from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime
import serial
import time

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura' # ¡Cambia esto por una clave más robusta en producción!
DATABASE = 'estacionamiento.db'

# Configurciónción del puerto serial de Arduino
# ¡IMPORTANTE! Hemos confirmado que tu Arduino está en '/dev/ttyUSB0' en EndeavourOS.
# Asegúrate de que la velocidad de baudios (9600) coincida con la de tu Arduino.
arduino_serial = None
try:
    # Para Linux/macOS, usa el puerto identificado (ej. '/dev/ttyUSB0')
    arduino_serial = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
    time.sleep(2) # Espera a que la conexión serial se establezca
    print("Conexión serial con Arduino establecida en /dev/ttyUSB0.")
except serial.SerialException as e:
    arduino_serial = None
    print(f"No se pudo conectar con Arduino en /dev/ttyUSB0: {e}. Las funciones de barrera no estarán disponibles.")
except Exception as e:
    arduino_serial = None
    print(f"Error inesperado al intentar conectar con Arduino: {e}.")

# Función para enviar comandos a Arduino
def send_command_to_arduino(command):
    if arduino_serial:
        try: 
            arduino_serial.write(command.encode('utf-8')) # Codificar el comando a bytes
            print(f"Comando enviado a Arduino: {command}")
        except serial.SerialTimeoutException:
            print("Tiempo de espera agotado al enviar comando a Arduino.")
        except Exception as e:
            print(f"Error al enviar comando a Arduino: {e}")
    else:
        print("Arduino no conectado. No se puede enviar comando.")

# Función para conectar con SQLite
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login_admin', methods=['POST'])
def login_admin():
    usuario = request.form['usuario']
    password = request.form['password']
    conn = get_db()
    admin = conn.execute('SELECT * FROM administradores WHERE usuario = ? AND password = ?', (usuario, password)).fetchone()
    conn.close()
    if admin:
        session['admin'] = admin['nombre']
        return redirect(url_for('admin'))
    flash(f'Usuario o contraseña incorrectos.', 'error')
    return redirect(url_for('login'))

@app.route('/visitante')
def visitante():
    # La lista de visitantes pendientes ya no es necesaria aquí para el registro de salida manual
    return render_template('visitante.html')

@app.route('/admin')
def admin():
    if 'admin' not in session:
        flash('Debes iniciar sesión como administrador para acceder.', 'warning')
        return redirect(url_for('login'))
    conn = get_db()
    residentes = conn.execute('SELECT * FROM residentes').fetchall()
    visitantes = conn.execute('SELECT * FROM visitantes').fetchall()
    historial = conn.execute('SELECT * FROM historial ORDER BY fecha_hora_entrada DESC').fetchall() # Ordenar historial
    conn.close()
    return render_template('admin.html', residentes=residentes, visitantes=visitantes, historial=historial)

@app.route('/registro_visitante', methods=['POST'])
def registro_visitante():
    data = request.form
    entrada = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO visitantes (nombre, apellidos, telefono, modelo_carro, color_carro, placas, residente_uid, fecha_hora_entrada, fecha_hora_salida)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)
    ''', (data['nombre'], data['apellidos'], data['telefono'], data['modelo_carro'], data['color_carro'], data['placas'], data['residente_uid'], entrada))
    
    # También se inserta en el historial con la entrada (fecha_hora_salida NULL inicialmente)
    c.execute('''
        INSERT INTO historial (nombre, apellido, status, fecha_hora_entrada, fecha_hora_salida)
        VALUES (?, ?, 'visitante', ?, NULL)
    ''', (data['nombre'], data['apellidos'], entrada))
    
    conn.commit()
    conn.close()
    
    send_command_to_arduino("ABRIR_ENTRADA")
    flash('¡Entrada de visitante registrada con éxito! La barrera de entrada se ha abierto.', 'success')
    return redirect(url_for('visitante'))

# Ruta para registrar la salida del visitante por placas
@app.route('/registro_salida_visitante', methods=['POST'])
def registro_salida_visitante():
    placas = request.form['placas_salida'].strip() # Obtener las placas del formulario
    salida = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = get_db()
    c = conn.cursor()

    # Buscar el visitante por placas que no tenga una fecha de salida registrada
    # Se busca la entrada más reciente para esas placas en la tabla 'visitantes'
    visitante_a_salir = conn.execute('''
        SELECT id, nombre, apellidos FROM visitantes 
        WHERE placas = ? AND fecha_hora_salida IS NULL 
        ORDER BY fecha_hora_entrada DESC LIMIT 1
    ''', (placas,)).fetchone()
    
    if visitante_a_salir:
        visitante_id = visitante_a_salir['id']
        visitante_nombre = visitante_a_salir['nombre']
        visitante_apellido = visitante_a_salir['apellidos']

        # Actualizar la hora de salida del visitante en la tabla visitantes
        c.execute('''
            UPDATE visitantes
            SET fecha_hora_salida = ?
            WHERE id = ?
        ''', (salida, visitante_id))

        # --- Lógica para actualizar HISTORIAL: Primero obtenemos el ID, luego actualizamos ---
        historial_entry_id = conn.execute('''
            SELECT id FROM historial
            WHERE nombre = ? AND apellido = ? AND status = 'visitante' AND fecha_hora_salida IS NULL
            ORDER BY fecha_hora_entrada DESC LIMIT 1
        ''', (visitante_nombre, visitante_apellido)).fetchone()

        if historial_entry_id:
            # Actualizar la entrada en la tabla 'historial' usando el ID encontrado
            c.execute('''
                UPDATE historial
                SET fecha_hora_salida = ?
                WHERE id = ?
            ''', (salida, historial_entry_id['id']))
        else:
            # Esto no debería ocurrir si se encontró un visitante, pero es un fallback
            print(f"Advertencia: No se encontró entrada en historial para {visitante_nombre} {visitante_apellido} sin salida.")
        # --- FIN LÓGICA DE HISTORIAL ---
            
        conn.commit()
        conn.close()

        send_command_to_arduino("ABRIR_SALIDA")
        flash(f'¡Salida de {placas} registrada con éxito! La barrera de salida se ha abierto.', 'success')
    else:
        conn.close()
        flash(f'No se encontró un registro de entrada pendiente para las placas: {placas}. Por favor, verifique el número.', 'error')
    
    return redirect(url_for('visitante'))

@app.route('/registro_residente', methods=['POST'])
def registro_residente():
    data = request.form
    conn = get_db()
    conn.execute('''
        INSERT INTO residentes (nombre, apellidos, direccion, modelo_carro, color_carro, placas, rfid_uid, fecha_hora_entrada, fecha_hora_salida)
        VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL) # RFID y fechas de entrada/salida inicialmente nulas
    ''', (data['nombre'], data['apellidos'], data['direccion'], data['modelo_carro'], data['color_carro'], data['placas'], data['rfid_uid']))
    conn.commit()
    conn.close()
    flash('¡Residente registrado con éxito!', 'success')
    return redirect(url_for('admin'))

@app.route('/registro_admin', methods=['POST'])
def registro_admin():
    data = request.form
    conn = get_db()
    conn.execute('''
        INSERT INTO administradores (usuario, password, nombre)
        VALUES (?, ?, ?)
    ''', (data['usuario'], data['password'], data['nombre']))
    conn.commit()
    conn.close()
    flash('¡Administrador registrado con éxito!', 'success')
    return redirect(url_for('admin'))

@app.route('/eliminar_residente/<int:id>')
def eliminar_residente(id):
    if 'admin' not in session:
        flash('Debes iniciar sesión como administrador para realizar esta acción.', 'warning')
        return redirect(url_for('login'))
    conn = get_db()
    conn.execute('DELETE FROM residentes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Residente eliminado con éxito.', 'info')
    return redirect(url_for('admin'))

@app.route('/abrir_barrera/<string:tipo_barrera>')
def abrir_barrera(tipo_barrera):
    if 'admin' not in session:
        flash('Debes iniciar sesión como administrador para controlar las barreras.', 'warning')
        return redirect(url_for('login'))
    
    if tipo_barrera == 'entrada':
        send_command_to_arduino("ABRIR_ENTRADA")
        flash('Barrera de entrada abierta desde el panel de administrador.', 'info')
    elif tipo_barrera == 'salida':
        send_command_to_arduino("ABRIR_SALIDA")
        flash('Barrera de salida abierta desde el panel de administrador.', 'info')
    else:
        flash('Tipo de barrera desconocido.', 'error')
    
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

