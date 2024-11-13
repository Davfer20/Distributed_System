import multiprocessing
from flask import Flask, request, jsonify
from Node import Node
import os
import time
from collections import deque


def initialize_node(node_id, pipe):
    # This function initializes the Node instance
    node = Node(node_id, pipe)  # Create an instance of Node with the given ID


class Master:
    def __initialize_server(self):
        # Initialize Flask app for HTTP handling
        self.app = Flask(__name__)

        # Define Flask route for sending messages to nodes
        @self.app.route("/send/<int:node_id>", methods=["POST"])
        def send_message(node_id):
            if node_id not in self.node_pipes:
                return jsonify({"error": "Node ID not found"}), 404
            message = request.json.get("message")
            if not message:
                return jsonify({"error": "Message content is missing"}), 400

            # Send message to the specified node
            self.node_pipes[node_id].send(message)
            # Wait for the node to respond (can add timeout if necessary)
            if self.node_pipes[node_id].poll(timeout=5):  # Timeout in seconds
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

    def __init__(self, node_quantity):
        self.node_processes = {}  # NodeID: Process
        self.node_loads = {}  # NodeID: list of requests
        self.node_pipes = {}  # NodeID: Pipe
        self.resources = {}
        self.standby = False
        print(f"Master process ID: {os.getpid()}")

        for i in range(node_quantity):
            # Create each process to initialize a Node instance in that process
            parent_pipe, child_pipe = multiprocessing.Pipe()
            process = multiprocessing.Process(
                target=initialize_node, args=(i, child_pipe)
            )
            self.node_processes[i] = process
            self.node_pipes[i] = parent_pipe
            self.node_loads[i] = deque()
            process.start()

        self.__initialize_server()

    def run(self):
        if self.app:
            # Run Flask app
            self.app.run(port=5000)


# Example usage
if __name__ == "__main__":
    master = Master(node_quantity=5)
    master.run()
