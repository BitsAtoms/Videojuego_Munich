using UnityEngine;

public class JugadorControl : MonoBehaviour
{
    //public float velocidadAvance = 8f;  //quitamos velocidad avance ya que dejaremos quieto
    public float distanciaCarril = 2f;          // separación entre carriles
    public float velocidadCambioCarril = 15f;   // lo rápido que cambia de carril
    public float fuerzaSalto = 8f;              // impulso inicial del salto
    public float gravedad = -25f;               // lo rápido que cae
    public GameObject canvas_u_loose;           // pantalla de "has perdido"

    public bool juegoActivo = false;   // el juego espera hasta recibir "inicio"

    int carrilActual = 1;              // 0 = izquierda, 1 = centro, 2 = derecha
    float velocidadVertical = 0f;      // velocidad de subida/bajada en cada momento
    float alturaSuelo = -0.48f;        // altura Y a la que está el jugador en el suelo
    bool enSuelo = true;               // true si está tocando el suelo

    void Start()
    {
        // Ocultamos la pantalla de "perdiste" al empezar
        if (canvas_u_loose != null) canvas_u_loose.SetActive(false);
    }

    void Update()
    {
        // Tecla de prueba para arrancar sin Python
        if (Input.GetKeyDown(KeyCode.Space)) Iniciar();

        // Si el juego está parado, no hacemos nada más
        if (!juegoActivo) return;

        // ---- Teclas de prueba ----
        if (Input.GetKeyDown(KeyCode.LeftArrow))  CambiarCarril(-1);
        if (Input.GetKeyDown(KeyCode.RightArrow)) CambiarCarril(1);
        if (Input.GetKeyDown(KeyCode.UpArrow))    Saltar();

        // ---- Movimiento ----
        Vector3 pos = transform.position;

        //pos.z += velocidadAvance * Time.deltaTime;  //se quedara quieto

        // Moverse suavemente hacia el carril elegido
        float xObjetivo = (carrilActual - 1) * distanciaCarril;
        pos.x = Mathf.MoveTowards(pos.x, xObjetivo, velocidadCambioCarril * Time.deltaTime);

        // Gravedad y salto
        velocidadVertical += gravedad * Time.deltaTime;
        pos.y += velocidadVertical * Time.deltaTime;

        // Si llega al suelo, se queda ahí
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

        // Aplicamos la nueva posición (¡esta línea debe estar al final de Update!)
        transform.position = pos;
    }

    // Unity llama a este método cuando otro collider entra en este jugador.
    // Tiene que estar FUERA de Update, como un método más de la clase.
    void OnTriggerEnter(Collider other)
    {
        // Si lo que nos ha tocado tiene la etiqueta "Obstacle"...
        if (other.CompareTag("Obstacle"))
        {
            Debug.Log("¡Choque con un obstáculo!");
            if (canvas_u_loose != null) canvas_u_loose.SetActive(true); // mostrar "perdiste"
            Parar(); // detener el juego
        }
    }


    public void Iniciar()
    {
        juegoActivo = true;
        // Al empezar una partida nueva, ocultamos la pantalla de "perdiste"
        if (canvas_u_loose != null) canvas_u_loose.SetActive(false);
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
        if (!juegoActivo) return;  // no guardar el salto mientras el juego está parado
        if (enSuelo)
        {
            velocidadVertical = fuerzaSalto;
            enSuelo = false;
        }
    }
}