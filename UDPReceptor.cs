using System;
using System.Collections.Concurrent;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;

public class UDPReceptor : MonoBehaviour
{
    public int puerto = 5005;
    public JugadorControl jugador;

    UdpClient cliente;
    Thread hilo;
    volatile bool escuchando;
    ConcurrentQueue<string> mensajes = new ConcurrentQueue<string>();

    void Start()
    {
        Application.runInBackground = true;

        cliente = new UdpClient(puerto);
        escuchando = true;
        hilo = new Thread(Escuchar);
        hilo.IsBackground = true;
        hilo.Start();
        Debug.Log("Escuchando UDP en el puerto " + puerto);
    }

    // Se ejecuta en un hilo aparte para no bloquear el juego
    void Escuchar()
    {
        IPEndPoint origen = new IPEndPoint(IPAddress.Any, 0);
        while (escuchando)
        {
            try
            {
                byte[] datos = cliente.Receive(ref origen);
                mensajes.Enqueue(Encoding.UTF8.GetString(datos).Trim());
            }
            catch (SocketException) { }
            catch (ObjectDisposedException) { }
        }
    }

    // Unity solo permite tocar objetos desde el hilo principal,
    // así que procesamos los mensajes aquí
    void Update()
    {
        while (mensajes.TryDequeue(out string msg))
        {
            Debug.Log("Mensaje recibido: " + msg);
            switch (msg.ToLower())
            {
                case "inicio":    jugador.Iniciar();      break;
                case "parar":     jugador.Parar();        break;
                case "izquierda": jugador.IrACarril(0);   break;
                case "centro":    jugador.IrACarril(1);   break;
                case "derecha":   jugador.IrACarril(2);   break;
                case "salto":     jugador.Saltar();       break;
            }
        }
    }

    void OnDestroy()
    {
        escuchando = false;
        if (cliente != null) cliente.Close();
    }
}