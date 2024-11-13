# Node.py
import threading
import os
import time

HEARTBEAT = True


class Node:
    def __init__(self, nodeId, pipe, heartbeat, idle):
        self.escuchando = False  # Controla el bucle de escucha
        self.nodeId = nodeId
        self.pipe = pipe
        self.heartbeat = heartbeat
        self.idle = idle
        self.idle.set()
        print(os.getpid())

        heartbeat_thread = threading.Thread(target=self.send_heartbeat)
        heartbeat_thread.daemon = True
        heartbeat_thread.start()

        self.listen()

    def listen(self):
        # Example loop to keep checking for messages from the master process
        try:
            while True:
                if self.pipe.poll():  # Check if there’s any data sent from the parent
                    instruction = self.pipe.recv()
                    self.idle.clear()
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
                    self.idle.set()
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

    def send_heartbeat(self):
        while True:
            # Send a heartbeat message to the master process
            self.heartbeat.send(HEARTBEAT)
            time.sleep(5)
