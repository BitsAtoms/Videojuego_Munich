# ------------------------------------------------------------
# Detector de la X de una zapatilla (7cm x 7cm) con Logitech Brio
# Funciona con X de distintos colores.
# Si la X aparece durante N frames seguidos -> imprime "Activado"
# ------------------------------------------------------------

import cv2
import numpy as np

# ==================== VARIABLES QUE PUEDES CAMBIAR ====================

CAMARA = 0
FRAMES_NECESARIOS = 10     # Frames seguidos que debe verse la X para activar

ANCHO_CM = 7               # Medida real de la X
ALTO_CM = 7
PIXELES_POR_CM = 6         # CALIBRACIÓN: píxeles que ocupa 1 cm en la imagen
TOLERANCIA = 0.25          # Margen de error en el tamaño (35 %)

# Colores que se prueban en cada frame. Formato HSV: (Matiz, Saturación, Brillo)
# Cada color tiene una lista de rangos (el rojo necesita dos porque está en los dos extremos)
COLORES = {
    "azul":     [((100, 120, 50), (130, 255, 255))],
    "rojo":     [((0, 120, 70), (10, 255, 255)), ((170, 120, 70), (179, 255, 255))],
    "verde":    [((40, 80, 50), (85, 255, 255))],
    "naranja":  [((10, 120, 100), (22, 255, 255))],
    "amarillo": [((22, 120, 100), (35, 255, 255))],
    "negro":    [((0, 0, 0), (179, 255, 50))],
    "blanco":   [((255, 255, 255), (179, 255, 50))],
}

# =====================================================================

camara = cv2.VideoCapture(CAMARA, cv2.CAP_DSHOW)
#camara.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
#camara.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
camara.set(cv2.CAP_PROP_FRAME_WIDTH, 900)
camara.set(cv2.CAP_PROP_FRAME_HEIGHT, 500)

if not camara.isOpened():
    print("No se pudo abrir la cámara. Cierra otras apps que la usen o cambia CAMARA.")
    exit()

ancho_esperado = ANCHO_CM * PIXELES_POR_CM
alto_esperado = ALTO_CM * PIXELES_POR_CM
kernel = np.ones((3, 3), np.uint8)

# Aquí guardamos el último frame en HSV para poder leer el color donde hagas clic
ultimo_hsv = None


def cerca(valor, esperado):
    """True si 'valor' está dentro del margen de 'esperado'."""
    return abs(valor - esperado) <= esperado * TOLERANCIA


def al_hacer_clic(evento, x, y, flags, param):
    """Se ejecuta cada vez que haces clic en la ventana de la cámara.
    Lee el color del píxel y lo añade a la lista de colores a buscar."""
    if evento == cv2.EVENT_LBUTTONDOWN and ultimo_hsv is not None:
        # Cogemos un cuadradito de 5x5 píxeles y hacemos la media (más estable)
        zona = ultimo_hsv[max(y - 2, 0):y + 3, max(x - 2, 0):x + 3]
        h, s, v = [int(n) for n in zona.reshape(-1, 3).mean(axis=0)]

        # Creamos un rango alrededor de ese color
        minimo = (max(h - 10, 0), max(s - 70, 30), max(v - 70, 30))
        maximo = (min(h + 10, 179), 255, 255)
        COLORES["clic"] = [(minimo, maximo)]
        print(f"Color aprendido con clic: H={h} S={s} V={v}")


def buscar_x(hsv):
    """Prueba cada color de la lista. Si encuentra la X devuelve
    (nombre_color, x, y, w, h). Si no, devuelve None."""
    for nombre, rangos in COLORES.items():
        # Máscara: blanco donde hay ese color, negro en el resto
        mascara = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for minimo, maximo in rangos:
            mascara |= cv2.inRange(hsv, np.array(minimo), np.array(maximo))

        # Limpieza de huecos y puntitos
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, kernel)
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, kernel)

        contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contornos:
            x, y, w, h = cv2.boundingRect(c)
            # ¿Tamaño de 7x7 cm?
            if cerca(w, ancho_esperado) and cerca(h, alto_esperado):
                # Una X no llena su rectángulo (un cuadrado macizo sí)
                relleno = cv2.contourArea(c) / (w * h)
                if 0.15 < relleno < 0.65:
                    return nombre, x, y, w, h
    return None


frames_seguidos = 0
color_actual = None
ya_activado = False

cv2.namedWindow("Camara Brio")
cv2.setMouseCallback("Camara Brio", al_hacer_clic)  # Activamos el clic

print("Cámara lista. Haz clic sobre la X para enseñarle un color nuevo. Pulsa 'q' para salir.")

while True:
    ok, frame = camara.read()
    if not ok:
        print("Error leyendo la cámara.")
        break

    # Convertimos a HSV (más fácil para trabajar con colores)
    ultimo_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    resultado = buscar_x(ultimo_hsv)

    if resultado is not None:
        nombre, x, y, w, h = resultado
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(frame, nombre, (x, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Si cambia el color detectado, empezamos a contar de nuevo
        if nombre == color_actual:
            frames_seguidos += 1
        else:
            color_actual = nombre
            frames_seguidos = 1
    else:
        frames_seguidos = 0
        color_actual = None
        ya_activado = False

    # Si llegamos a los frames necesarios -> Activado
    if frames_seguidos >= FRAMES_NECESARIOS and not ya_activado:
        print(f"Activado (X {color_actual})")
        ya_activado = True

    cv2.putText(frame, f"Frames: {frames_seguidos}/{FRAMES_NECESARIOS}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("Camara Brio", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

camara.release()
cv2.destroyAllWindows()