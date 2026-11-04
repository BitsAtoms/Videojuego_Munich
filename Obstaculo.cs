using UnityEngine;

public class Obstaculo : MonoBehaviour
{
    // Velocidad compartida por TODOS los obstáculos.
    // Más adelante la iremos subiendo con el tiempo.
    public static float velocidad = 8f;

    // Cuando el obstáculo pasa por detrás del jugador hasta aquí, se borra
    public float zDestruccion = -10f;

    void Update()
    {
        // Mover hacia el jugador (hacia Z negativas)
        transform.position += Vector3.back * velocidad * Time.deltaTime;

        if (transform.position.z < zDestruccion)
        {
            Destroy(gameObject);
        }
    }
}