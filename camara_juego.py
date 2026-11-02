import os
import time
import urllib.request

import socket
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

# ==================== AJUSTES DE LA X ====================
CAMARA = 0
FRAMES_NECESARIOS = 60     # Frames seguidos que debe verse la X para activar
ANCHO_CM = 7
ALTO_CM = 7
PIXELES_POR_CM = 6
TOLERANCIA = 0.25

COLORES = {
    "azul":     [((100, 120, 50), (130, 255, 255))],
    "rojo":     [((0, 120, 70), (10, 255, 255)), ((170, 120, 70), (179, 255, 255))],
    "verde":    [((40, 80, 50), (85, 255, 255))],
    "naranja":  [((10, 120, 100), (22, 255, 255))],
    "amarillo": [((22, 120, 100), (35, 255, 255))],
    "negro":    [((0, 0, 0), (179, 255, 50))],
    "blanco":   [((255, 255, 255), (179, 255, 50))],
}

# ==================== AJUSTES DE LOS PIES ====================
UMBRAL_SALTO = 0.05         # subida mínima de los pies (fracción del alto de imagen)
ZONA_IZQ = 0.40             # x por debajo de esto = izquierda
ZONA_DER = 0.60             # x por encima de esto = derecha
ESPERA_SALTO = 0.7          # segundos mínimos entre saltos
SEGUNDOS_PREPARACION = 3    # tiempo para colocarte tras detectar la X
SEGUNDOS_CALIBRACION = 3
DEBUG = False               # True = imprime x e y de los pies continuamente

# ==================== CONEXIÓN CON UNITY ====================
UNITY_IP = "127.0.0.1"      # 127.0.0.1 = este mismo PC
UNITY_PUERTO = 5005         # el mismo que en Unity
# =============================================================

# ---------- Modelo de MediaPipe ----------
MODELO = "pose_landmarker_lite.task"
URL_MODELO = ("https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
              "pose_landmarker_lite/float16/latest/pose_landmarker_lite.task")

if not os.path.exists(MODELO):
    print("Descargando modelo (solo la primera vez)...")
    urllib.request.urlretrieve(URL_MODELO, MODELO)
    print("Modelo descargado.")

opciones = vision.PoseLandmarkerOptions(
    base_options=mp_python.BaseOptions(model_asset_path=MODELO),
    running_mode=vision.RunningMode.VIDEO,
    num_poses=1,
    min_pose_detection_confidence=0.3,
    min_pose_presence_confidence=0.3,
    min_tracking_confidence=0.3,
)
detector = vision.PoseLandmarker.create_from_options(opciones)

# Tobillos (27, 28), talones (29, 30), puntas (31, 32)
PUNTOS_PIES = [27, 28, 29, 30, 31, 32]

# ---------- Cámara ----------
camara = cv2.VideoCapture(CAMARA, cv2.CAP_DSHOW)
camara.set(cv2.CAP_PROP_FRAME_WIDTH, 900)
camara.set(cv2.CAP_PROP_FRAME_HEIGHT, 500)

if not camara.isOpened():
    print("No se pudo abrir la cámara. Cierra otras apps que la usen o cambia CAMARA.")
    exit()

ancho_esperado = ANCHO_CM * PIXELES_POR_CM
alto_esperado = ALTO_CM * PIXELES_POR_CM
kernel = np.ones((3, 3), np.uint8)
ultimo_hsv = None
t0 = time.monotonic()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def enviar(mensaje):
    """Manda un mensaje de texto a Unity."""
    sock.sendto(mensaje.encode("utf-8"), (UNITY_IP, UNITY_PUERTO))


# ---------- Funciones de la X ----------
def cerca(valor, esperado):
    return abs(valor - esperado) <= esperado * TOLERANCIA


def al_hacer_clic(evento, x, y, flags, param):
    if evento == cv2.EVENT_LBUTTONDOWN and ultimo_hsv is not None:
        zona = ultimo_hsv[max(y - 2, 0):y + 3, max(x - 2, 0):x + 3]
        h, s, v = [int(n) for n in zona.reshape(-1, 3).mean(axis=0)]
        minimo = (max(h - 10, 0), max(s - 70, 30), max(v - 70, 30))
        maximo = (min(h + 10, 179), 255, 255)
        COLORES["clic"] = [(minimo, maximo)]
        print(f"Color aprendido con clic: H={h} S={s} V={v}")


def buscar_x(hsv):
    for nombre, rangos in COLORES.items():
        mascara = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for minimo, maximo in rangos:
            mascara |= cv2.inRange(hsv, np.array(minimo), np.array(maximo))

        mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, kernel)
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, kernel)

        contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contornos:
            x, y, w, h = cv2.boundingRect(c)
            if cerca(w, ancho_esperado) and cerca(h, alto_esperado):
                relleno = cv2.contourArea(c) / (w * h)
                if 0.15 < relleno < 0.65:
                    return nombre, x, y, w, h
    return None


# ---------- Función de los pies ----------
def detectar_pies(frame):
    """Devuelve (x, y) medios de los pies (valores de 0 a 1) o None."""
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    imagen_mp = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    marca_tiempo = int((time.monotonic() - t0) * 1000)
    resultado = detector.detect_for_video(imagen_mp, marca_tiempo)

    if not resultado.pose_landmarks:
        return None

    lm = resultado.pose_landmarks[0]
    puntos = [lm[i] for i in PUNTOS_PIES if lm[i].visibility > 0.4]

    for p in puntos:
        cv2.circle(frame, (int(p.x * w), int(p.y * h)), 6, (0, 0, 255), -1)

    if len(puntos) < 3:
        return None

    x_pies = sum(p.x for p in puntos) / len(puntos)
    y_pies = sum(p.y for p in puntos) / len(puntos)
    return x_pies, y_pies


# ---------- Programa principal ----------
estado = "ESPERANDO_X"
inicio_estado = time.time()
frames_seguidos = 0
color_actual = None
muestras = []
altura_normal = None
carril_actual = None
ultimo_salto = 0

cv2.namedWindow("Camara Brio")
cv2.setMouseCallback("Camara Brio", al_hacer_clic)

print("Cámara lista. Enseña la X para empezar.")
print("Clic sobre la X = aprender su color | R = volver a empezar | C = recalibrar | Q = salir")

while True:
    ok, frame = camara.read()
    if not ok:
        print("Error leyendo la cámara.")
        break

    frame = cv2.flip(frame, 1)   # espejo
    h, w = frame.shape[:2]
    ultimo_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    texto = ""

    # ===== FASE 1: esperar la X =====
    if estado == "ESPERANDO_X":
        resultado = buscar_x(ultimo_hsv)
        if resultado is not None:
            nombre, x, y, bw, bh = resultado
            cv2.rectangle(frame, (x, y), (x + bw, y + bh), (0, 255, 0), 2)
            cv2.putText(frame, nombre, (x, y - 8), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 255, 0), 2)
            if nombre == color_actual:
                frames_seguidos += 1
            else:
                color_actual = nombre
                frames_seguidos = 1
        else:
            frames_seguidos = 0
            color_actual = None

        texto = f"Esperando la X... {frames_seguidos}/{FRAMES_NECESARIOS}"

        if frames_seguidos >= FRAMES_NECESARIOS:
            print(f"Activado (X {color_actual})")
            print(f"Colócate en el centro. Calibración en {SEGUNDOS_PREPARACION} segundos...")
            estado = "PREPARANDO"
            inicio_estado = time.time()

    # ===== FASE 2: tiempo para colocarte =====
    elif estado == "PREPARANDO":
        detectar_pies(frame)   # solo para ver los puntos rojos mientras te colocas
        restante = SEGUNDOS_PREPARACION - (time.time() - inicio_estado)
        texto = f"Colocate en el centro... {max(restante, 0):.0f}"
        if restante <= 0:
            muestras = []
            estado = "CALIBRANDO"
            inicio_estado = time.time()

    # ===== FASE 3: calibrar =====
    elif estado == "CALIBRANDO":
        pies = detectar_pies(frame)
        if pies is None:
            # Si pierde los pies, reinicia la cuenta
            muestras = []
            inicio_estado = time.time()
            texto = "No veo los pies"
        else:
            muestras.append(pies[1])
            restante = SEGUNDOS_CALIBRACION - (time.time() - inicio_estado)
            texto = f"Calibrando... quieto {max(restante, 0):.1f}s"
            if restante <= 0:
                altura_normal = sum(muestras) / len(muestras)
                carril_actual = None
                estado = "JUGANDO"
                print("Calibrado. Ya puedes moverte.")
                enviar("inicio")

    # ===== FASE 4: seguir los pies =====
    elif estado == "JUGANDO":
        pies = detectar_pies(frame)
        if pies is None:
            texto = "No veo los pies"
        else:
            x_pies, y_pies = pies

            if DEBUG:
                print(f"x={x_pies:.2f}  y={y_pies:.2f}")

            if x_pies < ZONA_IZQ:
                carril = "IZQUIERDA"
            elif x_pies > ZONA_DER:
                carril = "DERECHA"
            else:
                carril = "CENTRO"

            if carril != carril_actual:
                carril_actual = carril
                print(carril)
                enviar(carril)

            subida = altura_normal - y_pies
            ahora = time.time()
            if subida > UMBRAL_SALTO and ahora - ultimo_salto > ESPERA_SALTO:
                ultimo_salto = ahora
                print("SALTO")
                enviar("SALTO")

            texto = f"Carril: {carril_actual}"

    # ---------- Dibujo en pantalla ----------
    if estado in ("PREPARANDO", "CALIBRANDO", "JUGANDO"):
        cv2.line(frame, (int(w * ZONA_IZQ), 0), (int(w * ZONA_IZQ), h), (255, 255, 0), 2)
        cv2.line(frame, (int(w * ZONA_DER), 0), (int(w * ZONA_DER), h), (255, 255, 0), 2)

    cv2.putText(frame, texto, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    cv2.imshow("Camara Brio", frame)

    # ---------- Teclas ----------
    tecla = cv2.waitKey(1) & 0xFF
    if tecla == ord('q'):
        break
    elif tecla == ord('r'):          # volver a esperar la X
        estado = "ESPERANDO_X"
        frames_seguidos = 0
        color_actual = None
        carril_actual = None
        enviar("parar")
        print("Reiniciado. Enseña la X para empezar.")
    elif tecla == ord('c'):          # recalibrar sin volver a enseñar la X
        estado = "PREPARANDO"
        inicio_estado = time.time()
        print(f"Recalibrando. Colócate en el centro ({SEGUNDOS_PREPARACION} s)...")

camara.release()
cv2.destroyAllWindows()
detector.close()