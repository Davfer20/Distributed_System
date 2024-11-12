import multiprocessing
from flask import Flask, request, jsonify
from Node import Node
import os
import time


def initialize_node(node_id, pipe):
    # This function initializes the Node instance
    node = Node(node_id, pipe)  # Create an instance of Node with the given ID

    # Example loop to keep checking for messages from the master process
    while True:
        if pipe.poll():  # Check if there’s any data sent from the parent
            message = pipe.recv()
            if message == "STOP":
                break  # Exit the loop if stop signal received
            # Here you could process messages and perhaps send a response
            response = f"Node {node_id} processed message: {message}"
            pipe.send(response)


class Master:
    def __init__(self, nodeQuantity):
        self.nodeProcesses = {}  # NodeID: Process
        self.nodeLoads = {}  # NodeID: list of requests
        self.nodePipes = {}  # NodeID: Pipe
        self.resources = {}
        self.standby = False
        print(f"Master process ID: {os.getpid()}")

        for i in range(nodeQuantity):
            # Create each process to initialize a Node instance in that process
            parent_pipe, child_pipe = multiprocessing.Pipe()
            process = multiprocessing.Process(
                target=initialize_node, args=(i, child_pipe)
            )
            self.nodeProcesses[i] = process
            self.nodePipes[i] = parent_pipe
            self.nodeLoads[i] = []
            process.start()

        # Initialize Flask app for HTTP handling
        self.app = Flask(__name__)

        # Define Flask route for sending messages to nodes
        @self.app.route("/send/<int:node_id>", methods=["POST"])
        def send_message(node_id):
            if node_id not in self.nodePipes:
                return jsonify({"error": "Node ID not found"}), 404
            message = request.json.get("message")
            if not message:
                return jsonify({"error": "Message content is missing"}), 400

            # Send message to the specified node
            self.nodePipes[node_id].send(message)
            # Wait for the node to respond (can add timeout if necessary)
            if self.nodePipes[node_id].poll(timeout=5):  # Timeout in seconds
                response = self.nodePipes[node_id].recv()
                return jsonify({"node_id": node_id, "response": response})
            else:
                return jsonify({"error": "No response from node"}), 504

        # Define Flask route for stopping nodes
        @self.app.route("/stop/<int:node_id>", methods=["POST"])
        def stop_node(node_id):
            if node_id not in self.nodePipes:
                return jsonify({"error": "Node ID not found"}), 404
            # Send stop signal to the node
            self.nodePipes[node_id].send("STOP")
            self.nodeProcesses[node_id].join()  # Wait for process to exit
            return jsonify({"message": f"Node {node_id} stopped successfully"})

    def run(self):
        # Run Flask app
        self.app.run(port=5000, debug=True)


# Example usage
if __name__ == "__main__":
    master = Master(nodeQuantity=5)
    master.run()
