# Node.py
import socket
import threading


class Node:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.escuchando = False  # Controla el bucle de escucha

    def iniciar_nodo(self):
        self.escuchando = True
        self.socket.bind((self.host, self.port))
        self.socket.listen()
        print(f"Nodo iniciado en {self.host}:{self.port}")

        # Ejecuta la escucha en un hilo separado
        threading.Thread(target=self.escuchar_mensajes).start()

    def escuchar_mensajes(self):
        while self.escuchando:
            try:
                conn, addr = self.socket.accept()
                print(f"Conexión establecida con {addr}")
                data = conn.recv(1024).decode()
                if data:
                    print(f"Mensaje recibido: {data}")
                    conn.sendall(b"Mensaje recibido")
                conn.close()
            except socket.error:
                break  # Rompe el bucle en caso de cierre del socket

    def enviar_mensaje(self, target_host, target_port, mensaje):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((target_host, target_port))
            s.sendall(mensaje.encode())
            response = s.recv(1024).decode()
            print(f"Respuesta recibida: {response}")

    def cerrar_nodo(self):
        """Método para cerrar el nodo y detener la escucha."""
        self.escuchando = False
        self.socket.close()
        print("Nodo cerrado.")
