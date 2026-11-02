using UnityEngine;

public class JugadorControl : MonoBehaviour
{
    public float velocidadAvance = 8f;
    public float distanciaCarril = 2f;
    public float velocidadCambioCarril = 15f;
    public float fuerzaSalto = 8f;
    public float gravedad = -25f;

    public bool juegoActivo = false;   // el juego espera hasta recibir "inicio"

    int carrilActual = 1;              // 0 = izquierda, 1 = centro, 2 = derecha
    float velocidadVertical = 0f;
    float alturaSuelo = 0.5f;
    bool enSuelo = true;

    void Update()
    {
        // Tecla de prueba para arrancar sin Python
        if (Input.GetKeyDown(KeyCode.Space)) Iniciar();

        if (!juegoActivo) return;

        // ---- Teclas de prueba ----
        if (Input.GetKeyDown(KeyCode.LeftArrow))  CambiarCarril(-1);
        if (Input.GetKeyDown(KeyCode.RightArrow)) CambiarCarril(1);
        if (Input.GetKeyDown(KeyCode.UpArrow))    Saltar();

        // ---- Movimiento ----
        Vector3 pos = transform.position;

        pos.z += velocidadAvance * Time.deltaTime;

        float xObjetivo = (carrilActual - 1) * distanciaCarril;
        pos.x = Mathf.MoveTowards(pos.x, xObjetivo, velocidadCambioCarril * Time.deltaTime);

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

    public void Iniciar()
    {
        juegoActivo = true;
    }

    public void Parar()
    {
        // Vuelve al principio y espera otra vez
        juegoActivo = false;
        carrilActual = 1;
        velocidadVertical = 0f;
        transform.position = new Vector3(0f, alturaSuelo, 0f);
    }

    public void CambiarCarril(int direccion)
    {
        carrilActual = Mathf.Clamp(carrilActual + direccion, 0, 2);
    }

    public void IrACarril(int carril)
    {
        if (!juegoActivo) return;
        carrilActual = Mathf.Clamp(carril, 0, 2);   // 0 = izq, 1 = centro, 2 = der
    }

    public void Saltar()
    {
        if (!juegoActivo) return;  //no guardar el salto mientras juego esta parado
        if (enSuelo)
        {
            velocidadVertical = fuerzaSalto;
            enSuelo = false;
        }
    }
}