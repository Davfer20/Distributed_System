# Node.py
import socket
import threading
import os


class Node:
    def __init__(self, nodeId, pipe, heartbeat, idle):
        self.escuchando = False  # Controla el bucle de escucha
        self.nodeId = nodeId
        self.pipe = pipe
        self.idle = idle
        self.idle.set()
        print(os.getpid())

    def iniciar_nodo(self):
        self.escuchando = True
        self.socket.bind((self.host, self.port))
        self.socket.listen()
        print(f"Nodo iniciado en {self.host}:{self.port}")

        # Ejecuta la escucha en un hilo separado
        threading.Thread(target=self.escuchar_mensajes).start()

    def listen(self):

        # Example loop to keep checking for messages from the master process
        try:
            while True:
                if self.pipe.poll():  # Check if there’s any data sent from the parent
                    instruction = self.pipe.recv()
                    if instruction.type == "STOP":
                        break  # Exit the loop if stop signal received
                    response = ""
                    if instruction.type == "python":
                        try:
                            response = exec(instruction.command)
                        except Exception as e:
                            response = f"Node {self.nodeId}: The code executed produced an error. {e}"

                    elif instruction.type == "shell":
                        try:
                            response = os.system(instruction.command)
                        except Exception as e:
                            response = f"Node {self.nodeId}: The shell command produced an error. {e}"
                    else:
                        response = f"Node {self.nodeId}: Unknown instruction received."
                    # Here you could process messages and perhaps send a response
                    print(response)
                    self.pipe.send(response)
        except BrokenPipeError:
            print(f"Node {self.nodeId}: Pipe was closed unexpectedly.")
        # while self.escuchando:
        #     try:
        #         conn, addr = self.socket.accept()
        #         print(f"Conexión establecida con {addr}")
        #         data = conn.recv(1024).decode()
        #         if data:
        #             print(f"Mensaje recibido: {data}")
        #             conn.sendall(b"Mensaje recibido")
        #         conn.close()
        #     except socket.error:
        #         break  # Rompe el bucle en caso de cierre del socket

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
