import multiprocessing
from flask import Flask, request, jsonify
from Node import Node
import os
import time
from collections import deque
from Instruction import Instruction

HEARTBEAT = True


def initialize_node(node_id, pipe, heartbeat, idle):
    # This function initializes the Node instance
    node = Node(
        node_id, pipe, heartbeat, idle
    )  # Create an instance of Node with the given ID
    node.listen()  # Start listening for messages from the master process


class Master:
    def __initialize_server(self):
        # Initialize Flask app for HTTP handling
        self.app = Flask(__name__)

        # Define Flask route for sending messages to nodes
        @self.app.route("/send/<int:node_id>", methods=["POST"])
        def send_instruction_to_node(node_id):
            if node_id not in self.node_pipes:
                return jsonify({"error": "Node ID not found"}), 404
            type = request.json.get("type")
            command = request.json.get("command")
            if not command or not type:
                return jsonify({"error": "Message content is missing"}), 400
            instruction = Instruction(type, command)

            # Send message to the specified node
            self.node_pipes[node_id].send(instruction)
            # Wait for the node to respond (can add timeout if necessary)
            if self.node_pipes[node_id].poll(timeout=60):  # Timeout in seconds
                response = self.node_pipes[node_id].recv()
                return jsonify({"node_id": node_id, "response": response})
            else:
                return jsonify({"error": "No response from node"}), 504

        @self.app.route("/send", methods=["POST"])
        def send_instruction():
            
            if  not in self.node_pipes:
                return jsonify({"error": "Node ID not found"}), 404
            type = request.json.get("type")
            command = request.json.get("command")
            if not command or not type:
                return jsonify({"error": "Message content is missing"}), 400
            instruction = Instruction(type, command)

            # Send message to the specified node
            self.node_pipes[node_id].send(instruction)
            # Wait for the node to respond (can add timeout if necessary)
            if self.node_pipes[node_id].poll(timeout=60):  # Timeout in seconds
                response = self.node_pipes[node_id].recv()
                return jsonify({"node_id": node_id, "response": response})
            else:
                return jsonify({"error": "No response from node"}), 504

        # Define Flask route for stopping nodes
        @self.app.route("/stop/<int:node_id>", methods=["POST"])
        def stop_node(node_id):
            if node_id not in self.node_pipes:
                return jsonify({"error": "Node ID not found"}), 404
            # Send stop signal to the node
            self.node_pipes[node_id].send("STOP")
            self.node_processes[node_id].join()  # Wait for process to exit
            return jsonify({"message": f"Node {node_id} stopped successfully"})

    def __create_node(self, node_id, max_capacity=10):
        # Create each process to initialize a Node instance in that process
        idle = multiprocessing.Event()
        parent_pipe, child_pipe = multiprocessing.Pipe()
        parent_heartbeat, child_heartbeat = multiprocessing.Pipe(False)
        process = multiprocessing.Process(
            target=initialize_node,
            args=(node_id, child_pipe, child_heartbeat, idle),
        )
        self.node_processes[node_id] = process
        self.node_pipes[node_id] = parent_pipe
        self.node_heartbeats[node_id] = parent_heartbeat
        self.node_queues[node_id] = deque(maxlen=max_capacity)
        self.node_idleness[node_id] = idle
        process.start()

    def __check_nodes_status(self, timeout=10):
        last_heartbeat = {i: time.time() for i in range(len(self.node_heartbeats))}
        # Check if nodes are still running
        while True:
            for i, pipe in enumerate(self.node_heartbeats):
                if pipe.poll():
                    message = pipe.recv()
                    if message == HEARTBEAT:
                        last_heartbeat[i] = time.time()

            current_time = time.time()
            for node_id, last_time in last_heartbeat.items():
                if current_time - last_time > timeout:
                    print(f"Node {node_id} is not responding")
                    # TODO: Reload queue
                    # Restart the node
                    self.__create_node(node_id)
            time.sleep(1)

    

    def __init__(self, node_quantity):
        self.node_processes = {}  # NodeID: Process
        self.node_pipes = {}  # NodeID: Pipe for heartbeat
        self.resources = {}
        self.standby = False
        self.node_tasks = {}  # Dict for current task.
        self.node_idleness = {}  # Dict for node idleness
        self.node_queues = {}  # Dict for node queues
        self.node_heartbeats = {}  # Dict for node heartbeats
        print(f"Master process ID: {os.getpid()}")
        self.master_queue = deque()
        for node_id in range(node_quantity):
            self.__create_node(node_id)

        self.__initialize_server()

    def run(self):
        if self.app:
            # Run Flask app
            self.app.run(port=5000)


# Example usage
if __name__ == "__main__":
    master = Master(node_quantity=5)
    master.run()
