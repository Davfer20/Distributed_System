import multiprocessing
import threading
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


class Master:
    def __initialize_server(self):
        # Initialize Flask app for HTTP handling
        self.app = Flask(__name__)

        # Define Flask route for sending messages to nodes
        @self.app.route("/send/<int:node_id>", methods=["POST"])
        def receive_instruction_for_node(node_id):
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

        # Define Flask route for sending messages to the master
        @self.app.route("/send", methods=["POST"])
        def receive_instruction():
            type = request.json.get("type")
            command = request.json.get("command")
            if not command or not type:
                return jsonify({"error": "Message content is missing"}), 400
            instruction = Instruction(type, command)
            self.master_queue.append(instruction)

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

    def __requeue_tasks(self, node_id):
        # Requeue tasks from the specified node
        queue = self.node_queues[node_id]
        while queue:
            instruction = queue.pop()
            self.master_queue.appendleft(instruction)

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
                    self.__requeue_tasks(node_id)
                    # Restart the node
                    self.__create_node(node_id)
            time.sleep(1)

    def select_next_node(self):
        # Select the next node to send a task to
        # Implement a simple round-robin scheduling algorithm
        count = 0
        while True:
            self.current_node = self.current_node + 1 % len(self.node_processes)
            count += 1
            if (
                len(self.node_queues[self.current_node])
                < self.node_queues[self.current_node].maxlen
            ):
                break
            if count == len(self.node_processes):
                time.sleep(2)
                count = 0

    def add_task_to_node(self):
        self.select_next_node()
        instruction = self.master_queue.popleft()
        # Send message to the specified node
        self.node_queues[self.current_node].append(instruction)

    def __distribute_tasks(self):
        while True:
            if self.master_queue:
                self.add_task_to_node()
            else:
                time.sleep(1)

    def __assign_tasks(self):
        while True:
            for node_id, idle in self.node_idleness.items():
                if idle.is_set():  # If node is idle
                    queue = self.node_queues[node_id]
                    if self.node_pipes[
                        node_id
                    ].poll():  # Check if there’s any data sent from the worker
                        # Print the response from the node
                        response = self.node_pipes[node_id].recv()
                        print(response)
                        queue.popleft()
                    if queue:
                        instruction = queue[0]
                        self.node_pipes[node_id].send(instruction)
                    else:
                        # Steal work from other queues
                        for other_queue in self.node_queues.values():
                            if len(other_queue) > 1:
                                instruction = other_queue.pop()
                                queue.append(instruction)
                                self.node_pipes[node_id].send(instruction)
            time.sleep(1)

    def __init__(self, node_quantity, node_capacities):
        self.node_processes = {}  # NodeID: Process
        self.node_pipes = {}  # NodeID: Pipe for heartbeat
        self.resources = {}
        self.standby = False
        self.node_tasks = {}  # Dict for current task.
        self.node_idleness = {}  # Dict for node idleness
        self.node_queues = {}  # Dict for node queues
        self.node_heartbeats = {}  # Dict for node heartbeats
        self.current_node = None
        print(f"Master process ID: {os.getpid()}")
        self.master_queue = deque()
        for node_id in range(node_quantity):
            self.__create_node(node_id, node_capacities[node_id])
            self.current_node = node_id

        # Start a thread to check the status of the nodes
        check_thread = threading.Thread(target=self.__check_nodes_status)
        check_thread.daemon = True
        check_thread.start()

        # Start a thread to distribute tasks to nodes
        distribute_thread = threading.Thread(target=self.__distribute_tasks)
        distribute_thread.daemon = True
        distribute_thread.start()

        # Start a thread to assign tasks to nodes
        assign_thread = threading.Thread(target=self.__assign_tasks)
        assign_thread.daemon = True
        assign_thread.start()

        # Initialize the Flask server
        self.__initialize_server()

    def run(self):
        if self.app:
            # Run Flask app
            self.app.run(port=5000)


# Example usage
if __name__ == "__main__":
    master = Master(node_quantity=5)
    master.run()
