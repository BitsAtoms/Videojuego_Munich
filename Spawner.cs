using UnityEngine;

public class Spawner : MonoBehaviour
{
    // ---------- VARIABLES QUE PUEDES CAMBIAR EN EL INSPECTOR ----------

    // Aquí arrastrarás tus 4 prefabs de obstáculos
    public GameObject[] prefabsObstaculos;

    // Referencia al jugador (para saber si el juego está activo)
    public JugadorControl jugador;

    // A qué distancia (en Z) aparecen los obstáculos, lejos del jugador
    public float distanciaAparicion = 40f;

    // Separación entre carriles (debe ser la misma que en JugadorControl)
    public float distanciaCarril = 2f;

    // Segundos que pasan entre un obstáculo y el siguiente
    public float intervalo = 1.5f;

    // ---------- VARIABLES INTERNAS (no hace falta tocarlas) ----------

    float temporizador;        // cuenta atrás hasta el próximo obstáculo
    bool estabaActivo = false; // para detectar cuándo empieza y cuándo se para el juego

    void Start()
    {
        // Avisos en rojo en la consola si se te olvida algo en el Inspector
        if (jugador == null)
            Debug.LogError("Spawner: falta arrastrar el Jugador al campo Jugador");
        if (prefabsObstaculos == null || prefabsObstaculos.Length == 0)
            Debug.LogError("Spawner: faltan los prefabs en Prefabs Obstaculos");
    }

    void Update()
    {
        // Si falta algo, no hacemos nada (así evitamos errores en cadena)
        if (jugador == null || prefabsObstaculos.Length == 0) return;

        // ---- CASO 1: el juego NO está activo ----
        if (!jugador.juegoActivo)
        {
            // Si justo se acaba de parar, borramos los obstáculos que quedaban
            if (estabaActivo)
            {
                LimpiarObstaculos();
                estabaActivo = false;
            }
            return; // no seguimos: no hay que generar nada
        }

        // ---- CASO 2: el juego está activo ----

        // Si justo acaba de empezar, reiniciamos la cuenta atrás
        if (!estabaActivo)
        {
            estabaActivo = true;
            temporizador = intervalo;
        }

        // Restamos el tiempo que ha pasado desde el último frame
        temporizador -= Time.deltaTime;

        // Cuando llega a 0, sacamos un obstáculo y reiniciamos la cuenta
        if (temporizador <= 0f)
        {
            CrearObstaculo();
            temporizador = intervalo;
        }
    }

    void CrearObstaculo()
    {
        // 1. Elegir uno de los prefabs al azar
        //    (Random.Range con números enteros no incluye el último)
        int indicePrefab = Random.Range(0, prefabsObstaculos.Length);
        GameObject prefab = prefabsObstaculos[indicePrefab];

        // 2. Elegir un carril al azar: 0 = izquierda, 1 = centro, 2 = derecha
        int carril = Random.Range(0, 3);

        // 3. Convertir el carril en posición X: -2, 0 o 2
        float x = (carril - 1) * distanciaCarril;

        // 4. Calcular la posición final.
        //    Mantenemos la Y que tú le pusiste al prefab (para que quede apoyado en el suelo)
        Vector3 posicion = new Vector3(x, prefab.transform.position.y, distanciaAparicion);

        // 5. Crear la copia. El último parámetro (transform) la deja
        //    como "hija" del Spawner, así luego es fácil borrarlas todas
        Instantiate(prefab, posicion, prefab.transform.rotation, transform);
    }

    void LimpiarObstaculos()
    {
        // Recorremos todos los objetos hijos del Spawner (los obstáculos) y los borramos
        foreach (Transform hijo in transform)
        {
            Destroy(hijo.gameObject);
        }
    }
}