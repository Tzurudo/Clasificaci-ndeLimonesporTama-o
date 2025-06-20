import cv2
import numpy as np
import serial
import time
import os
import sys
from datetime import datetime

xz = 0
# ==============================================
# FUNCIONES PARA COMUNICACIÓN SERIAL CON ARDUINO
# ==============================================

def find_arduino():
    """Busca automáticamente el puerto del Arduino"""
    common_paths = [
        '/dev/ttyACM',  # Arduinos modernos
        '/dev/ttyUSB',   # Clones CH340/CH341
        '/dev/ttyS'      # Puertos seriales
    ]
    
    for i in range(10):
        for base in common_paths:
            port = f"{base}{i}"
            if os.path.exists(port):
                return port
    
    try:
        ports = os.popen('ls /dev/tty* 2>/dev/null | grep -E "ACM|USB"').read().split()
        if ports:
            return ports[0]
    except:
        pass
    
    return None

def fix_linux_permissions(port):
    """Soluciona problemas de permisos en Linux"""
    try:
        if not os.access(port, os.R_OK | os.W_OK):
            print(f"Solucionando permisos para {port}...")
            os.system(f'sudo chmod a+rw {port}')
            time.sleep(1)
    except Exception as e:
        print(f"Error en permisos: {e}")

# ==============================================
# CONFIGURACIÓN INICIAL
# ==============================================

# Inicializar comunicación serial
puerto = find_arduino()
if not puerto:
    print("Error: Arduino no detectado")
    sys.exit(1)

print(f"Conectando a: {puerto}")

# Solucionar problemas de permisos en Linux
if sys.platform.startswith('linux'):
    fix_linux_permissions(puerto)

try:
    ser = serial.Serial(
        port=puerto,
        baudrate=9600,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=2
    )
    time.sleep(2)  # Esperar inicialización
    print("Conexión exitosa con Arduino")
    
except serial.SerialException as e:
    print(f"Error de comunicación: {e}")
    sys.exit(1)

# Función para controlar servomotores
def mover_servos(servo1, servo2):
    """Envía comandos a los servomotores"""
    comando = f"{servo1},{servo2}\n"
    ser.write(comando.encode('ascii'))
    ser.flush()
    time.sleep(0.1)
    
    # Leer respuesta (opcional)
    if ser.in_waiting:
        respuesta = ser.readline().decode().strip()
        print(f"Arduino: {respuesta}")

# ==============================================
# DETECCIÓN DE LIMONES CON INTERFAZ ARDUINO STYLE
# ==============================================

# Rangos HSV para detección de limones (ajustables)
verde_bajo = np.array([30, 50, 50])
verde_alto = np.array([85, 255, 255])

# Kernel para operaciones morfológicas
kernel = np.ones((5, 5), np.uint8)

# Estados de tamaño de limón
ULTIMO_ESTADO = None

# Iniciar captura de video
cap = cv2.VideoCapture(xz)
if not cap.isOpened():
    print("Error al abrir la cámara")
    ser.close()
    sys.exit(1)

# Configuración de pantalla completa
ANCHO_VENTANA = 1920
ALTO_VENTANA = 1080
PANEL_ANCHO = 400

# Paleta de colores Arduino (gris, dorado, azul)
COLOR_FONDO = (45, 45, 50)        # Gris oscuro
COLOR_PANEL = (60, 60, 70)        # Gris panel
COLOR_TITULO = (0, 180, 220)      # Azul Arduino
COLOR_TEXTO = (220, 220, 220)     # Gris claro
COLOR_DESTACADO = (0, 150, 255)   # Azul destacado
COLOR_ACENTO = (30, 180, 210)     # Azul acento
COLOR_DORADO = (0, 180, 220)      # Dorado/Ambar (simulado con azul)
COLOR_LED_ON = (0, 200, 220)      # Azul encendido
COLOR_LED_OFF = (70, 70, 80)      # Gris apagado
COLOR_ALARMA = (0, 100, 220)      # Azul alarma

# Colores para tamaños de limón
COLOR_PEQUENIO = (0, 150, 255)    # Azul anaranjado
COLOR_MEDIANO = (0, 180, 220)     # Dorado/Ambar
COLOR_GRANDE = (30, 180, 210)     # Azul Arduino

# Fuentes
FUENTE_TITULO = cv2.FONT_HERSHEY_DUPLEX
FUENTE_TEXTO = cv2.FONT_HERSHEY_SIMPLEX
FUENTE_DATOS = cv2.FONT_HERSHEY_COMPLEX_SMALL
FUENTE_MONO = cv2.FONT_HERSHEY_COMPLEX

# Variables para FPS
fps_prev_time = time.time()
fps_counter = 0
fps = 0

# Contadores
contador_pequenio = 0
contador_mediano = 0
contador_grande = 0

print("Iniciando sistema de clasificación con estilo Arduino...")

def dibujar_led(imagen, x, y, diametro, estado, color_on=COLOR_LED_ON):
    """Dibuja un LED indicador estilo Arduino"""
    color = color_on if estado else COLOR_LED_OFF
    # LED con efecto de brillo
    cv2.circle(imagen, (x, y), diametro, color, -1)
    cv2.circle(imagen, (x, y), diametro, (200, 200, 220), 1)
    cv2.circle(imagen, (x-2, y-2), diametro//3, (220, 220, 240), -1)

def dibujar_panel_datos(imagen, x, y, ancho, alto, titulo):
    """Dibuja un panel de datos estilo moderno"""
    # Panel principal con efecto de profundidad
    cv2.rectangle(imagen, (x, y), (x + ancho, y + alto), COLOR_PANEL, -1)
    cv2.rectangle(imagen, (x, y), (x + ancho, y + alto), (80, 80, 90), 1)
    
    # Efecto de bisel
    cv2.line(imagen, (x, y), (x + ancho, y), (90, 90, 100), 1)
    cv2.line(imagen, (x, y), (x, y + alto), (90, 90, 100), 1)
    cv2.line(imagen, (x + ancho, y), (x + ancho, y + alto), (40, 40, 50), 1)
    cv2.line(imagen, (x, y + alto), (x + ancho, y + alto), (40, 40, 50), 1)
    
    # Barra de título
    cv2.rectangle(imagen, (x, y), (x + ancho, y + 30), (40, 40, 50), -1)
    cv2.rectangle(imagen, (x, y), (x + ancho, y + 30), (70, 70, 80), 1)
    
    # Texto del título
    (text_width, _), _ = cv2.getTextSize(titulo, FUENTE_TEXTO, 0.7, 1)
    text_x = x + (ancho - text_width) // 2
    cv2.putText(imagen, titulo, (text_x, y + 22), 
               FUENTE_TEXTO, 0.7, COLOR_DORADO, 1)
    
    return y + 40  # Devuelve la posición Y para contenido

# Configurar pantalla completa
cv2.namedWindow('Sistema de Clasificacion Arduino', cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty('Sistema de Clasificacion Arduino', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error en captura de video")
            break
            
        # Calcular FPS
        fps_counter += 1
        if fps_counter == 10:
            fps_current_time = time.time()
            fps = 10 / (fps_current_time - fps_prev_time)
            fps_prev_time = fps_current_time
            fps_counter = 0

        # Crear lienzo principal
        lienzo = np.zeros((ALTO_VENTANA, ANCHO_VENTANA, 3), dtype=np.uint8)
        lienzo[:] = COLOR_FONDO
        
        # Dibujar barra superior con logo Arduino
        cv2.rectangle(lienzo, (0, 0), (ANCHO_VENTANA, 70), (30, 30, 40), -1)
        cv2.rectangle(lienzo, (0, 0), (ANCHO_VENTANA, 70), (70, 70, 80), 1)
        
        # Logo Arduino (simplificado)
        cv2.rectangle(lienzo, (30, 15), (180, 55), (0, 0, 0), -1)
        cv2.rectangle(lienzo, (40, 20), (70, 50), COLOR_ACENTO, -1)
        cv2.rectangle(lienzo, (85, 20), (115, 50), COLOR_DORADO, -1)
        cv2.rectangle(lienzo, (130, 20), (160, 50), COLOR_ACENTO, -1)
        cv2.putText(lienzo, "ARDUINO", (200, 45), 
                   FUENTE_TITULO, 1.2, COLOR_DORADO, 2)
        
        # Título del sistema
        cv2.putText(lienzo, "SISTEMA DE CLASIFICACION DE LIMONES", (450, 45), 
                   FUENTE_TITULO, 1.0, COLOR_TEXTO, 1)
        
        # Fecha y hora
        fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        cv2.putText(lienzo, fecha_hora, (ANCHO_VENTANA - 300, 45), 
                   FUENTE_TEXTO, 0.7, COLOR_TEXTO, 1)
        
        # Procesamiento de imagen
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mascara = cv2.inRange(hsv, verde_bajo, verde_alto)
        
        # Mejorar máscara
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, kernel)
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, kernel)
        
        # Detectar contornos
        contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Variables para seguimiento
        limon_detectado = False
        estado_actual = None
        contador_pequenio = 0
        contador_mediano = 0
        contador_grande = 0

        for cnt in contornos:
            area = cv2.contourArea(cnt)
            
            # Filtrar por tamaño
            if area < 3000:
                continue
                
            limon_detectado = True
            x, y, w, h = cv2.boundingRect(cnt)
            
            # Clasificar por tamaño y dibujar
            if 10000 <= area < 75000:
                color = COLOR_PEQUENIO
                texto = "Limon Pequenio"
                estado_actual = "PEQUENIO"
                contador_pequenio += 1
            if 75000 <= area < 110000:
                color = COLOR_MEDIANO
                texto = "Limon Mediano"
                estado_actual = "MEDIANO"
                contador_mediano += 1
            if  110000 < area:
                color = COLOR_GRANDE
                texto = "Limon Grande"
                estado_actual = "GRANDE"
                contador_grande += 1
            
            # Dibujar detección con estilo moderno
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 3)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (240, 240, 240), 1)
            
            # Etiqueta con fondo
            cv2.rectangle(frame, (x, y - 25), (x + len(texto)*11, y), (30, 30, 40), -1)
            cv2.rectangle(frame, (x, y - 25), (x + len(texto)*11, y), color, 1)
            cv2.putText(frame, texto, (x + 5, y - 8), 
                        FUENTE_TEXTO, 0.6, (240, 240, 240), 1)
            
            # Área del objeto
            cv2.putText(frame, f"Area: {area}", (x, y + h + 20), 
                        FUENTE_TEXTO, 0.5, (200, 200, 220), 1)

        # Control de servomotores (solo si cambió el estado)
        if estado_actual and estado_actual != ULTIMO_ESTADO:
            if estado_actual == "PEQUENIO":
                mover_servos(180, 180)
            elif estado_actual == "MEDIANO":
                mover_servos(180, 90)
            elif estado_actual == "GRANDE":
                mover_servos(90, 180)
                
            ULTIMO_ESTADO = estado_actual
            print(f"Estado cambiado: {estado_actual}")

        # =====================================
        # PANEL IZQUIERDO: VISUALIZACIÓN
        # =====================================
        # Marco para video con efecto bisel
        cv2.rectangle(lienzo, (20, 90), (ANCHO_VENTANA - PANEL_ANCHO - 20, ALTO_VENTANA - 30), 
                     (70, 70, 80), 1)
        cv2.rectangle(lienzo, (20, 90), (ANCHO_VENTANA - PANEL_ANCHO - 20, ALTO_VENTANA - 30), 
                     (40, 40, 50), 2)
        
        # Redimensionar frame para caber en el panel
        frame_redim = cv2.resize(frame, (ANCHO_VENTANA - PANEL_ANCHO - 80, ALTO_VENTANA - 150))
        lienzo[110:110+frame_redim.shape[0], 50:50+frame_redim.shape[1]] = frame_redim
        
        # Título de la vista
        cv2.putText(lienzo, "VISTA DE PROCESO", (50, 100), 
                   FUENTE_TEXTO, 0.7, COLOR_DORADO, 1)
        
        # =====================================
        # PANEL DERECHO: INFORMACIÓN Y CONTROL
        # =====================================
        panel_x = ANCHO_VENTANA - PANEL_ANCHO + 20
        y_pos = 90
        
        # Panel de estado del sistema
        y_pos = dibujar_panel_datos(lienzo, panel_x, y_pos, PANEL_ANCHO - 40, 150, "ESTADO DEL SISTEMA")
        
        # LED de conexión Arduino
        cv2.putText(lienzo, "CONEXION ARDUINO:", (panel_x + 20, y_pos), 
                   FUENTE_TEXTO, 0.6, COLOR_TEXTO, 1)
        dibujar_led(lienzo, panel_x + 220, y_pos, 12, ser.is_open)
        cv2.putText(lienzo, "ON" if ser.is_open else "OFF", 
                   (panel_x + 240, y_pos + 5), FUENTE_TEXTO, 0.6, 
                   COLOR_LED_ON if ser.is_open else COLOR_LED_OFF, 1)
        y_pos += 30
        
        # LED de detección
        cv2.putText(lienzo, "DETECCION ACTIVA:", (panel_x + 20, y_pos), 
                   FUENTE_TEXTO, 0.6, COLOR_TEXTO, 1)
        dibujar_led(lienzo, panel_x + 220, y_pos, 12, limon_detectado)
        cv2.putText(lienzo, "ON" if limon_detectado else "OFF", 
                   (panel_x + 240, y_pos + 5), FUENTE_TEXTO, 0.6, 
                   COLOR_LED_ON if limon_detectado else COLOR_LED_OFF, 1)
        y_pos += 40
        
        # Indicador de tamaño actual
        cv2.putText(lienzo, "TAMAÑO ACTUAL:", (panel_x + 20, y_pos), 
                   FUENTE_TEXTO, 0.6, COLOR_TEXTO, 1)
        y_pos += 25
        
        if estado_actual == "PEQUENIO":
            color_led = COLOR_PEQUENIO
            texto_estado = "PEQUENIO"
        elif estado_actual == "MEDIANO":
            color_led = COLOR_MEDIANO
            texto_estado = "MEDIANO"
        elif estado_actual == "GRANDE":
            color_led = COLOR_GRANDE
            texto_estado = "GRANDE"
        else:
            color_led = COLOR_LED_OFF
            texto_estado = "SIN DETECCION"
        
        dibujar_led(lienzo, panel_x + 20, y_pos, 16, estado_actual is not None, color_led)
        cv2.putText(lienzo, texto_estado, (panel_x + 50, y_pos + 7), 
                   FUENTE_TEXTO, 0.7, color_led, 1)
        y_pos += 40
        
        # Panel de contadores
        y_pos += 20
        y_pos = dibujar_panel_datos(lienzo, panel_x, y_pos, PANEL_ANCHO - 40, 180, "CONTADORES")
        
        cv2.putText(lienzo, "PEQUENIOS:", (panel_x + 20, y_pos), 
                   FUENTE_TEXTO, 0.7, COLOR_PEQUENIO, 1)
        cv2.putText(lienzo, f"{contador_pequenio}", (panel_x + PANEL_ANCHO - 80, y_pos), 
                   FUENTE_MONO, 1.0, COLOR_TEXTO, 2)
        y_pos += 35
        
        cv2.putText(lienzo, "MEDIANOS:", (panel_x + 20, y_pos), 
                   FUENTE_TEXTO, 0.7, COLOR_MEDIANO, 1)
        cv2.putText(lienzo, f"{contador_mediano}", (panel_x + PANEL_ANCHO - 80, y_pos), 
                   FUENTE_MONO, 1.0, COLOR_TEXTO, 2)
        y_pos += 35
        
        cv2.putText(lienzo, "GRANDES:", (panel_x + 20, y_pos), 
                   FUENTE_TEXTO, 0.7, COLOR_GRANDE, 1)
        cv2.putText(lienzo, f"{contador_grande}", (panel_x + PANEL_ANCHO - 80, y_pos), 
                   FUENTE_MONO, 1.0, COLOR_TEXTO, 2)
        y_pos += 35
        
        cv2.putText(lienzo, "TOTAL:", (panel_x + 20, y_pos), 
                   FUENTE_TEXTO, 0.7, COLOR_TEXTO, 1)
        total = contador_pequenio + contador_mediano + contador_grande
        cv2.putText(lienzo, f"{total}", (panel_x + PANEL_ANCHO - 80, y_pos), 
                   FUENTE_MONO, 1.0, COLOR_DORADO, 2)
        y_pos += 40
        
        # Panel de control de servos
        y_pos += 10
        y_pos = dibujar_panel_datos(lienzo, panel_x, y_pos, PANEL_ANCHO - 40, 150, "CONTROL DE SERVOS")
        
        cv2.putText(lienzo, "SERVO 1:", (panel_x + 20, y_pos), 
                   FUENTE_TEXTO, 0.6, COLOR_TEXTO, 1)
        
        if estado_actual == "PEQUENIO":
            pos_servo1 = 180
        elif estado_actual == "MEDIANO":
            pos_servo1 = 180
        elif estado_actual == "GRANDE":
            pos_servo1 = 90
        else:
            pos_servo1 = 0
            
        cv2.putText(lienzo, f"{pos_servo1}°", (panel_x + 120, y_pos), 
                   FUENTE_MONO, 0.8, COLOR_DORADO, 1)
        
        # Barra de posición
        cv2.rectangle(lienzo, (panel_x + 20, y_pos + 15), 
                     (panel_x + PANEL_ANCHO - 70, y_pos + 35), (50, 50, 60), -1)
        if estado_actual:
            ancho_barra = int((pos_servo1 / 180) * (PANEL_ANCHO - 90))
            cv2.rectangle(lienzo, (panel_x + 20, y_pos + 15), 
                         (panel_x + 20 + ancho_barra, y_pos + 35), COLOR_MEDIANO, -1)
        y_pos += 45
        
        cv2.putText(lienzo, "SERVO 2:", (panel_x + 20, y_pos), 
                   FUENTE_TEXTO, 0.6, COLOR_TEXTO, 1)
        
        if estado_actual == "PEQUENIO":
            pos_servo2 = 180
        elif estado_actual == "MEDIANO":
            pos_servo2 = 90
        elif estado_actual == "GRANDE":
            pos_servo2 = 180
        else:
            pos_servo2 = 0
            
        cv2.putText(lienzo, f"{pos_servo2}°", (panel_x + 120, y_pos), 
                   FUENTE_MONO, 0.8, COLOR_DORADO, 1)
        
        # Barra de posición
        cv2.rectangle(lienzo, (panel_x + 20, y_pos + 15), 
                     (panel_x + PANEL_ANCHO - 70, y_pos + 35), (50, 50, 60), -1)
        if estado_actual:
            ancho_barra = int((pos_servo2 / 180) * (PANEL_ANCHO - 90))
            cv2.rectangle(lienzo, (panel_x + 20, y_pos + 15), 
                         (panel_x + 20 + ancho_barra, y_pos + 35), COLOR_GRANDE, -1)
        y_pos += 50
        
        # Botón de salida
        cv2.rectangle(lienzo, (panel_x + PANEL_ANCHO - 150, ALTO_VENTANA - 70), 
                     (panel_x + PANEL_ANCHO - 30, ALTO_VENTANA - 30), COLOR_ACENTO, -1)
        cv2.rectangle(lienzo, (panel_x + PANEL_ANCHO - 150, ALTO_VENTANA - 70), 
                     (panel_x + PANEL_ANCHO - 30, ALTO_VENTANA - 30), (100, 100, 120), 2)
        cv2.putText(lienzo, "SALIR (Q)", (panel_x + PANEL_ANCHO - 130, ALTO_VENTANA - 45), 
                   FUENTE_TEXTO, 0.7, (240, 240, 240), 1)
        
        # Información FPS
        cv2.putText(lienzo, f"FPS: {fps:.1f}", (30, ALTO_VENTANA - 20), 
                   FUENTE_TEXTO, 0.6, (150, 200, 220), 1)
        
        # Mostrar resultados
        cv2.imshow('Sistema de Clasificacion Arduino', lienzo)
        
        # Salir con 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except Exception as e:
    print(f"Error inesperado: {e}")

finally:
    # Liberar recursos
    cap.release()
    cv2.destroyAllWindows()
    if ser.is_open:
        ser.close()
    print("Programa terminado")
