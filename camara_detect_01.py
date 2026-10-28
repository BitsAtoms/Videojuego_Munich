# ------------------------------------------------------------
# Detector de una "X" de 5cm x 10cm con una cámara Logitech Brio
# Si la X aparece durante N frames seguidos -> imprime "Activado"
# ------------------------------------------------------------

import cv2  # OpenCV: la librería que lee la cámara y analiza imágenes

# ==================== VARIABLES QUE PUEDES CAMBIAR ====================

CAMARA = 0                 # 0 = primera cámara del PC. Si no abre la Brio, prueba 1 o 2
FRAMES_NECESARIOS = 15     # Cuántos frames seguidos debe verse la X para activar (la variable "X frames")

ANCHO_CM = 10               # Medida real de la X (lado corto), en cm
ALTO_CM = 10               # Medida real de la X (lado largo), en cm

PIXELES_POR_CM = 20        # CALIBRACIÓN: cuántos píxeles ocupa 1 cm en la imagen
                           # (depende de la distancia a la cámara, mira las notas abajo)
TOLERANCIA = 0.25          # Margen de error permitido en el tamaño (0.25 = 25 %)

# =====================================================================

# Abrimos la cámara. CAP_DSHOW ayuda a que la Brio abra rápido en Windows
camara = cv2.VideoCapture(CAMARA, cv2.CAP_DSHOW)

# Pedimos resolución 1280x720 (la Brio soporta más, pero así va fluido)
camara.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
camara.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# Si no se pudo abrir, avisamos y salimos
if not camara.isOpened():
    print("No se pudo abrir la cámara. Cierra otras apps que la usen o cambia CAMARA.")
    exit()

# Tamaño esperado de la X en píxeles (cm x píxeles por cm)
corto_esperado = ANCHO_CM * PIXELES_POR_CM
largo_esperado = ALTO_CM * PIXELES_POR_CM


def cerca(valor, esperado):
    """Devuelve True si 'valor' está dentro del margen de 'esperado'."""
    return abs(valor - esperado) <= esperado * TOLERANCIA


frames_seguidos = 0     # Contador de frames consecutivos con la X detectada
ya_activado = False     # Para imprimir "Activado" solo una vez, no en cada frame

print("Cámara lista. Pulsa 'q' en la ventana para salir.")

while True:
    # Leemos un frame (una foto) de la cámara
    ok, frame = camara.read()
    if not ok:
        print("Error leyendo la cámara.")
        break

    # 1) Pasamos a escala de grises y suavizamos para quitar ruido
    gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gris = cv2.GaussianBlur(gris, (5, 5), 0)

    # 2) Umbral: lo oscuro se vuelve blanco y lo claro negro (la X negra será "blanca")
    #    Otsu elige el umbral automáticamente según la luz
    _, binaria = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 3) Buscamos las formas (contornos) que hay en la imagen
    contornos, _ = cv2.findContours(binaria, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    x_detectada = False  # En este frame todavía no hemos visto la X

    for c in contornos:
        # Rectángulo que envuelve la forma: posición (x, y), ancho (w) y alto (h)
        x, y, w, h = cv2.boundingRect(c)

        # Ordenamos para no depender de si la X está en vertical u horizontal
        lado_corto = min(w, h)
        lado_largo = max(w, h)

        # 4) ¿El tamaño coincide con 5cm x 10cm?
        if cerca(lado_corto, corto_esperado) and cerca(lado_largo, largo_esperado):

            # 5) Comprobación extra de forma: una X no rellena todo su rectángulo
            #    (un cuadrado negro rellenaría ~100 %, una X ronda el 20-60 %)
            relleno = cv2.contourArea(c) / (w * h)
            if 0.15 < relleno < 0.65:
                x_detectada = True
                # Dibujamos un recuadro verde para ver qué ha detectado
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                break  # Ya la encontramos, no hace falta seguir buscando

    # 6) Contamos frames seguidos
    if x_detectada:
        frames_seguidos += 1
    else:
        frames_seguidos = 0      # Si se pierde la X, el contador vuelve a cero
        ya_activado = False      # y permitimos que se active otra vez

    # 7) Si llegamos al número de frames necesario -> Activado
    if frames_seguidos >= FRAMES_NECESARIOS and not ya_activado:
        print("Activado")
        ya_activado = True

    # Mostramos información en la ventana (útil para calibrar)
    cv2.putText(frame, f"Frames: {frames_seguidos}/{FRAMES_NECESARIOS}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("Camara Brio", frame)

    # Salimos al pulsar la tecla 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Liberamos la cámara y cerramos ventanas
camara.release()
cv2.destroyAllWindows()