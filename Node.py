# Node.py
import threading
import os
import time
import logging
import sys
import traceback

HEARTBEAT = True

# Configure the logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class Node:
    def __init__(self, nodeId, pipe, heartbeat, idle, resource_pipe):
        self.escuchando = False  # Controla el bucle de escucha
        self.nodeId = nodeId
        self.pipe = pipe
        self.heartbeat = heartbeat
        self.idle = idle
        self.idle.set()
        self.resource_pipe = resource_pipe
        self.logger = logging.getLogger(f"Node {self.nodeId}-{os.getpid()}")

        self.logger.info(f"Node created: {os.getpid()}")

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
                        sys.exit()  # Exit the loop if stop signal received
                    response = ""
                    if instruction.type == "python":
                        try:
                            print(instruction.command)
                            exec_locals = {
                                "request_read_resource": self.request_read_resource,
                                "release_read_resource": self.release_read_resource,
                                "request_write_resource": self.request_write_resource,
                                "release_write_resource": self.release_write_resource,
                            }
                            exec(instruction.command, {}, exec_locals)
                            response = exec_locals.get(
                                "response", "No result retruned."
                            )
                        except Exception as e:
                            error_details = traceback.format_exc()
                            response = f"Node {self.nodeId}: The code executed produced an error. {error_details}"

                    elif instruction.type == "shell":
                        try:
                            response = os.system(instruction.command)
                        except Exception as e:
                            response = f"Node {self.nodeId}: The shell command produced an error. {e}"
                    else:
                        response = f"Node {self.nodeId}: Unknown instruction received."
                    # Here you could process messages and perhaps send a response
                    self.logger.info(response)
                    self.pipe.send(response)
                    self.idle.set()
        except BrokenPipeError:
            print(f"Node {self.nodeId}: Pipe was closed unexpectedly.")

    def send_heartbeat(self):
        while True:
            # Send a heartbeat message to the master process
            self.heartbeat.value = time.time()
            self.logger.debug("Heartbeat sent")
            time.sleep(5)

    def request_read_resource(self, resource):
        self.resource_pipe.send({"type": "request_read", "resource": resource})
        response = self.resource_pipe.recv()
        if response["status"] != "error":
            return response["resource"]
        return None

    def release_read_resource(self, resource):
        self.resource_pipe.send({"type": "release_read", "resource": resource})

    def request_write_resource(self, resource):
        self.resource_pipe.send({"type": "request_write", "resource": resource})
        response = self.resource_pipe.recv()
        if response["status"] != "error":
            return response["resource"]
        return None

    def release_write_resource(self, resource):
        self.resource_pipe.send({"type": "release_write", "resource": resource})
