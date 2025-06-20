
# Clasificación de Limones por Tamaño con Visión Artificial y Arduino

Este proyecto implementa un sistema automático para clasificar limones en diferentes tamaños (pequeño, mediano, grande) usando visión artificial en Python y controlando servomotores a través de Arduino. El sistema puede integrarse con una banda transportadora para automatizar el proceso en entornos agrícolas o industriales.

---

## Índice

- [¿Cómo funciona?](#cómo-funciona)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Ejecución](#ejecución)
- [Explicación del Código Principal](#explicación-del-código-principal)
- [Personalización](#personalización)
- [Conexión Hardware](#conexión-hardware)
- [Licencia](#licencia)

---

## ¿Cómo funciona?

1. **Captura de Video:** El sistema utiliza una cámara para capturar imágenes en tiempo real de limones sobre una banda transportadora.
2. **Procesamiento de Imagen:** Se utiliza OpenCV para segmentar los limones en la imagen mediante un filtro de color (HSV) y operaciones morfológicas.
3. **Clasificación:** El tamaño de cada limón se estima contando los píxeles de su área y clasificándolo en pequeño, mediano o grande según rangos definidos.
4. **Control de Banda:** Se comunica vía serial con un Arduino, que acciona servomotores para desviar los limones según su tamaño.
5. **Interfaz Visual:** Muestra en pantalla el estado, conteos y controles del sistema, con una estética inspirada en Arduino.

---

## Requisitos

- Python 3.7 o superior
- OpenCV (`opencv-python`)
- NumPy
- pyserial
- Arduino UNO/Nano (o compatible) conectado por USB
- Servomotores conectados al Arduino
- Banda transportadora (opcional, para automatización física)

Instala las dependencias de Python con:
```bash
pip install opencv-python numpy pyserial
```

---

## Instalación

1. Clona este repositorio:
    ```bash
    git clone https://github.com/Tzurudo/Clasificaci-ndeLimonesporTama-o.git
    cd Clasificaci-ndeLimonesporTama-o
    ```
2. Conecta el Arduino a tu computadora y asegúrate de tener los servos correctamente cableados.

---

## Ejecución

Ejecuta el programa principal:
```bash
python main.py
```

- El sistema buscará automáticamente el puerto del Arduino y establecerá la conexión.
- Comenzará la captura de video y la clasificación; los limones serán desviados automáticamente según su tamaño.
- Puedes salir del sistema presionando la tecla `q`.

---

## Explicación del Código Principal

A continuación, se explica el flujo y las partes más importantes del código:

### 1. **Importación de librerías**
```python
import cv2
import numpy as np
import serial
import time
import os
import sys
from datetime import datetime
```
Se usan librerías para visión artificial, manejo de arrays, comunicación serial, control de tiempo y sistema operativo.

### 2. **Comunicación con Arduino**
- **find_arduino()**: Busca automáticamente el puerto serial donde está conectado el Arduino.
- **fix_linux_permissions(port)**: Soluciona posibles permisos en Linux para acceder al puerto serial.
- **Inicialización**: Se conecta al Arduino usando pyserial y configura los parámetros de comunicación.

### 3. **Control de servomotores**
```python
def mover_servos(servo1, servo2):
    """Envía comandos a los servomotores a través de Arduino"""
    comando = f"{servo1},{servo2}\n"
    ser.write(comando.encode('ascii'))
    ser.flush()
    time.sleep(0.1)
```
Envía la posición deseada de los servos vía serial para que el Arduino los mueva.

### 4. **Procesamiento de imagen y clasificación**
- Se define el rango de color HSV para detectar limones.
- Se captura el video de la cámara.
- Se procesa cada frame:
  - Se convierte a HSV y se aplica una máscara para encontrar objetos del color esperado (limones).
  - Se realizan operaciones morfológicas para limpiar la imagen.
  - Se buscan contornos en la máscara.
  - Se calcula el área de cada contorno y se clasifica:
    - **Pequeño**: área entre 10,000 y 75,000 píxeles.
    - **Mediano**: área entre 75,000 y 110,000 píxeles.
    - **Grande**: área mayor a 110,000 píxeles.
  - Según la clasificación, se envía el comando correspondiente al Arduino para desviar el limón.

### 5. **Interfaz gráfica**
- Se dibuja una interfaz visual usando OpenCV:
  - Paneles con información de estado, conexión, detección, conteos y posiciones de servos.
  - Visualización en tiempo real del video procesado y la clasificación.
  - Estética inspirada en la marca Arduino.

### 6. **Control de flujo y recursos**
- El sistema se mantiene en bucle hasta que se presiona la tecla `q`.
- Al finalizar, se liberan los recursos (cámara, ventana, puerto serial).

### 7. **Seguridad y robustez**
- El código maneja errores de conexión, permisos, y captura de video para evitar caídas inesperadas.

---

## Personalización

- **Umbrales de tamaño:** Puedes modificar los valores de área en el código para adaptarlo a diferentes cámaras o tamaños de limón.
- **Rango de color:** Ajusta `verde_bajo` y `verde_alto` para detectar diferentes tonos de verde o incluso otras frutas.
- **Lógica de servos:** Cambia los valores enviados a los servos para modificar las posiciones de desvío.

---

## Conexión Hardware

- **Arduino:** Se espera que el Arduino reciba comandos seriales del tipo `"angulo1,angulo2\n"` y mueva los servos conectados.
- **Servos:** Conecta los servos a los pines PWM del Arduino y alimenta adecuadamente.
- **Banda transportadora:** El sistema puede controlar compuertas o brazos que desvían los limones según su tamaño.

> Si necesitas el código para el Arduino, agrégalo como `arduino.ino` en el repositorio y documenta los pines usados.

---

## Licencia

MIT

---

Desarrollado por [Tzurudo](https://github.com/Tzurudo)

---

### ¿Dudas o mejoras?

¡Abre un issue o pull request! Las contribuciones son bienvenidas.
