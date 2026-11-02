using UnityEngine;

public class CamaraSigue : MonoBehaviour
{
    public Transform objetivo;
    public float altura = 3f;
    public float distancia = 6f;

    void LateUpdate()
    {
        transform.position = new Vector3(0f, altura, objetivo.position.z - distancia);
    }
}
