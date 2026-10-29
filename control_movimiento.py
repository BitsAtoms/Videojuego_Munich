import os
import time
import urllib.request

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

# ---------- AJUSTES ----------
CAMARA = 0                  # si no abre la Brio, prueba 1 o 2
UMBRAL_SALTO = 0.05         # subida mínima de los pies (fracción del alto de imagen)
ZONA_IZQ = 0.40             # x por debajo de esto = izquierda
ZONA_DER = 0.60             # x por encima de esto = derecha
ESPERA_SALTO = 0.7          # segundos mínimos entre saltos
SEGUNDOS_CALIBRACION = 3
DEBUG = False               # True = imprime x e y de los pies continuamente
# -----------------------------

MODELO = "pose_landmarker_lite.task"
URL_MODELO = ("https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
              "pose_landmarker_lite/float16/latest/pose_landmarker_lite.task")

# Descarga el modelo si no existe
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

# Puntos del pie: tobillos (27, 28), talones (29, 30), puntas (31, 32)
PUNTOS_PIES = [27, 28, 29, 30, 31, 32]

cap = cv2.VideoCapture(CAMARA, cv2.CAP_DSHOW)   # CAP_DSHOW es para Windows
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

calibrando = False
inicio_calibracion = 0
muestras = []
altura_normal = None
carril_actual = None
ultimo_salto = 0
t0 = time.monotonic()

print("Pulsa C para calibrar (de pie, quieto, con los pies visibles).")
print("Pulsa Q para salir.")

while True:
    ok, frame = cap.read()
    if not ok:
        print("No se pudo leer la cámara. Prueba a cambiar CAMARA = 1")
        break

    frame = cv2.flip(frame, 1)   # espejo
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    imagen_mp = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    # El timestamp debe ir siempre en aumento (milisegundos)
    marca_tiempo = int((time.monotonic() - t0) * 1000)
    resultado = detector.detect_for_video(imagen_mp, marca_tiempo)

    texto = "Pulsa C para calibrar"

    if resultado.pose_landmarks:
        lm = resultado.pose_landmarks[0]

        # Dibujamos los puntos de los pies
        for i in PUNTOS_PIES:
            if lm[i].visibility > 0.4:
                cv2.circle(frame, (int(lm[i].x * w), int(lm[i].y * h)),
                           6, (0, 0, 255), -1)

        puntos = [lm[i] for i in PUNTOS_PIES if lm[i].visibility > 0.4]

        if len(puntos) >= 3:
            x_pies = sum(p.x for p in puntos) / len(puntos)
            y_pies = sum(p.y for p in puntos) / len(puntos)

            if DEBUG:
                print(f"x={x_pies:.2f}  y={y_pies:.2f}")

            # ---- CALIBRACIÓN ----
            if calibrando:
                muestras.append(y_pies)
                restante = SEGUNDOS_CALIBRACION - (time.time() - inicio_calibracion)
                texto = f"Calibrando... quieto {restante:.1f}s"
                if restante <= 0:
                    altura_normal = sum(muestras) / len(muestras)
                    calibrando = False
                    print("Calibrado. Ya puedes moverte.")

            # ---- DETECCIÓN ----
            elif altura_normal is not None:
                if x_pies < ZONA_IZQ:
                    carril = "IZQUIERDA"
                elif x_pies > ZONA_DER:
                    carril = "DERECHA"
                else:
                    carril = "CENTRO"

                if carril != carril_actual:
                    carril_actual = carril
                    print(carril)

                subida = altura_normal - y_pies
                ahora = time.time()
                if subida > UMBRAL_SALTO and ahora - ultimo_salto > ESPERA_SALTO:
                    ultimo_salto = ahora
                    print("SALTO")

                texto = f"Carril: {carril_actual}"
        else:
            texto = "Veo pocos puntos del pie"
    else:
        texto = "No detecto el cuerpo"

    cv2.putText(frame, texto, (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                1, (0, 255, 0), 2)
    cv2.line(frame, (int(w * ZONA_IZQ), 0), (int(w * ZONA_IZQ), h), (255, 255, 0), 2)
    cv2.line(frame, (int(w * ZONA_DER), 0), (int(w * ZONA_DER), h), (255, 255, 0), 2)

    cv2.imshow("Detector de pies", frame)

    tecla = cv2.waitKey(1) & 0xFF
    if tecla == ord('c'):
        calibrando = True
        inicio_calibracion = time.time()
        muestras = []
    elif tecla == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
detector.close()