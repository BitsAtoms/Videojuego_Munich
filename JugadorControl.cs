using UnityEngine;

public class JugadorControl : MonoBehaviour
{
    public float velocidadAvance = 8f;
    public float distanciaCarril = 2f;
    public float velocidadCambioCarril = 15f;
    public float fuerzaSalto = 8f;
    public float gravedad = -25f;

    int carrilActual = 1;          // 0 = izquierda, 1 = centro, 2 = derecha
    float velocidadVertical = 0f;
    float alturaSuelo = 0.5f;
    bool enSuelo = true;

    void Update()
    {
        // ---- Teclas de prueba ----
        if (Input.GetKeyDown(KeyCode.LeftArrow))  CambiarCarril(-1);
        if (Input.GetKeyDown(KeyCode.RightArrow)) CambiarCarril(1);
        if (Input.GetKeyDown(KeyCode.UpArrow))    Saltar();

        // ---- Movimiento ----
        Vector3 pos = transform.position;

        // Avanzar siempre hacia delante
        pos.z += velocidadAvance * Time.deltaTime;

        // Moverse suavemente hacia el carril elegido
        float xObjetivo = (carrilActual - 1) * distanciaCarril;
        pos.x = Mathf.MoveTowards(pos.x, xObjetivo, velocidadCambioCarril * Time.deltaTime);

        // Gravedad y salto
        velocidadVertical += gravedad * Time.deltaTime;
        pos.y += velocidadVertical * Time.deltaTime;

        if (pos.y <= alturaSuelo)
        {
            pos.y = alturaSuelo;
            velocidadVertical = 0f;
            enSuelo = true;
        }
        else
        {
            enSuelo = false;
        }

        transform.position = pos;
    }

    // Son públicas para poder llamarlas luego desde la cámara de Python
    public void CambiarCarril(int direccion)
    {
        carrilActual = Mathf.Clamp(carrilActual + direccion, 0, 2);
    }

    public void Saltar()
    {
        if (enSuelo)
        {
            velocidadVertical = fuerzaSalto;
            enSuelo = false;
        }
    }
}
