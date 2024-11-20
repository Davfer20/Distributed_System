import multiprocessing
import threading
from flask import Flask, request, jsonify
from Node import Node
import os
import time
from collections import deque
from Instruction import Instruction
import logging
from ReadWriteLock import ReadWriteLock

HEARTBEAT = True

# Configure the logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S.%f",
)


def initialize_node(node_id, pipe, heartbeat, idle, resource_pipe, max_capacity):
    # This function initializes the Node instance
    node = Node(
        node_id, pipe, heartbeat, idle, resource_pipe, max_capacity
    )  # Create an instance of Node with the given ID


class Master:
    def __initialize_server(self):
        # Initialize Flask app for HTTP handling
        self.app = Flask(__name__)

        # Flask route for sending messages to nodes
        @self.app.route("/send/<int:node_id>", methods=["POST"])
        def receive_instruction_for_node(node_id):
            if node_id not in self.node_pipes:  # If the node does not exist.
                return jsonify({"error": "Node ID not found"}), 404
            type = request.json.get("type")  # Type of the instruction
            command = request.json.get("command")  # Instruction that needs to be run
            if not command or not type:
                return jsonify({"error": "Message content is missing"}), 400
            instruction = Instruction(type, command)  # Create an instruction object
            while (
                True
            ):  # If the queue is full, an instruction cannot be added, so the server waits until the queue is not full.
                if len(self.node_queues[node_id]) < self.node_queues[node_id].maxlen:
                    break
                time.sleep(1)
            self.node_queues[node_id].append(
                instruction
            )  # Add the instruction to the queue
            self.logger.info(
                f"Node {node_id}'s queue length: {len(self.node_queues[node_id])}"
            )
            return jsonify({"message": f"Instruction received for node {node_id}"})

        # Flask route for sending messages to the master
        @self.app.route("/send", methods=["POST"])
        def receive_instruction():
            type = request.json.get("type")  # Type of the instruction
            command = request.json.get("command")  # Instruction that needs to be run
            if not command or not type:
                return jsonify({"error": "Message content is missing"}), 400
            instruction = Instruction(type, command)  # Create an instruction object
            self.master_queue.append(
                instruction
            )  # Add the instruction to the master queue
            return jsonify({"message": "Instruction received"})

        # Flask route for stopping nodes
        @self.app.route("/stop/<int:node_id>", methods=["POST"])
        def stop_node(node_id):
            if node_id not in self.node_pipes:  # If the node does not exist.
                return jsonify({"error": "Node ID not found"}), 404
            # Send stop signal to the node
            self.node_processes[node_id].terminate()  # Terminate the process
            return jsonify({"message": f"Node {node_id} stopped successfully"})

        # Create resource
        @self.app.route("/resource", methods=["POST"])
        def create_resource():
            # The resource request will have
            # Type: File/String/Integer/Float/Boolean/List/Dictionary/Tuple
            # Name:
            # Value:
            resource_name = request.json.get("name")  # Name of the resource
            resource_type = request.json.get("type")  # Type of the resource
            values = request.json.get("values", {})  # Values of the resource
            if not resource_name or not resource_type or not values:
                return jsonify({"error": "A resource field is missing."}), 400
            self.resources[resource_name] = None  # Create the resource
            self.resource_locks[resource_name] = (
                ReadWriteLock()
            )  # Create a lock for the resource
            # Create a shared resource based on type
            if resource_type == "File":
                file_path = values.get("path", "README.md")
                resource = {
                    "type": "File",
                    "path": file_path,
                    "mode": values.get("mode", "w+"),
                }
            elif resource_type == "String":
                initial_value = values.get("initial_value", "")
                resource = self.manager.Value("s", initial_value)
            elif resource_type == "Integer":
                initial_value = values.get("initial_value", 0)
                resource = self.manager.Value("i", initial_value)
            elif resource_type == "Float":
                initial_value = values.get("initial_value", 0.0)
                resource = self.manager.Value(
                    "d", initial_value
                )  # 'd' is for double precision float
            elif resource_type == "Boolean":
                initial_value = values.get("initial_value", False)
                resource = self.manager.Value("b", initial_value)
            elif resource_type == "List":
                initial_list = values.get("initial_value", [])
                resource = self.manager.list(initial_list)
            elif resource_type == "Dictionary":
                initial_dict = values.get("initial_value", {})
                resource = self.manager.dict(initial_dict)
            elif resource_type == "Tuple":
                initial_tuple = tuple(values.get("initial_value", ()))
                resource = self.manager.list(
                    initial_tuple
                )  # Lists can emulate shared tuples
            else:
                return jsonify({"error": "Unsupported resource type"}), 400

            # Store resource in shared dictionary
            self.resources[resource_name] = {
                "type": resource_type,
                "resource": resource,
            }
            logging.info(f"Resource {resource_name} of type {resource_type} created.")
            return jsonify(
                {"message": f"Resource {resource_name} created successfully"}
            )

        # Flask route to add a node to the server
        @self.app.route("/add", methods=["POST"])
        def add_node():
            node_id = len(self.node_processes)
            max_capacity = request.json.get("max_capacity", 10)
            self.__create_node(node_id, max_capacity)
            return jsonify({"message": f"Node {node_id} added successfully"})

    def __create_node(self, node_id, max_capacity=10):
        # Create each process to initialize a Node instance in that process
        idle = multiprocessing.Event()  # Event to indicate if the node is idle
        parent_pipe, child_pipe = (
            multiprocessing.Pipe()
        )  # Pipe for communication between the master and the node
        child_heartbeat = multiprocessing.Value(
            "d", time.time()
        )  # Value to store the heartbeat time
        parent_resource_pipe, child_resource_pipe = (
            multiprocessing.Pipe()
        )  # Pipe for resource management
        process = multiprocessing.Process(
            target=initialize_node,
            args=(
                node_id,
                child_pipe,
                child_heartbeat,
                idle,
                child_resource_pipe,
                max_capacity,
            ),
        )  # Create a process for the node
        # Set all of the node's attributes and variables
        self.node_processes[node_id] = process
        self.node_pipes[node_id] = parent_pipe
        self.node_heartbeats[node_id] = child_heartbeat
        self.node_queues[node_id] = deque(maxlen=max_capacity)
        self.node_idleness[node_id] = idle
        self.active_nodes[node_id] = True
        self.logger.info(f"Node {node_id} activated.")
        self.resource_pipes[node_id] = parent_resource_pipe
        process.start()  # Start the process

    def __requeue_tasks(self, node_id):
        # Requeue tasks from the specified node
        queue = self.node_queues[node_id]  # Get the queue for the specified node
        self.logger.info(
            f"Node {node_id}'s queue length before requeueing: {len(queue)}"
        )
        while queue:  # While there are still tasks in the queue
            instruction = queue.pop()  # Remove the task from the queue
            self.master_queue.appendleft(
                instruction
            )  # Add the task to the master queue
        self.logger.info(
            f"Finished requeueing for Node {node_id}: length {len(self.node_queues[node_id])}"
        )

    def __check_nodes_status(self, timeout=10):
        # Check if nodes are still running
        while True:
            current_time = time.time()

            # Check each node's last heartbeat time
            for node_id, heartbeat in self.node_heartbeats.items():
                with heartbeat.get_lock():  # Ensure thread-safe access
                    if current_time - heartbeat.value > timeout:
                        self.logger.info(f"Node {node_id} is not responding.")
                        self.logger.info(f"Requeueing tasks from Node {node_id}")
                        self.active_nodes[node_id] = False  # Set node as inactive
                        self.__requeue_tasks(node_id)  # Requeue tasks from the node
                        # Release held resources
                        if node_id in self.resource_in_use:
                            self.logger.info(
                                f"Releasing resources held by Node {node_id}"
                            )
                            resources_held = list(
                                self.resource_in_use[node_id]
                            )  # Copy to avoid modification during iteration
                            for resource in resources_held:
                                if resource[1] == "read":
                                    self.release_read_resource(node_id, resource[0])
                                else:
                                    self.release_write_resource(node_id, resource[0])
                        # Restart the node and update the heartbeat value
                        self.__create_node(node_id, self.node_queues[node_id].maxlen)
                        self.logger.info(f"Node {node_id} restarted.")

            time.sleep(1)

    def select_next_node(self):
        # Select the next node to send a task to
        # Implement a simple round-robin scheduling algorithm
        count = 0
        while True:  # Loop until a node is found
            if (
                self.active_nodes[self.current_node]
                and len(self.node_queues[self.current_node])
                < self.node_queues[self.current_node].maxlen
            ):  # If the node is active and has space in its queue
                break
            self.current_node = (self.current_node + 1) % len(
                self.node_processes
            )  # Move to the next node
            count += 1
            if count == len(self.node_processes):
                time.sleep(5)
                self.logger.info(
                    f"All nodes are busy. Waiting for a node to become idle. Master queue length: {len(self.master_queue)}"
                )
                count = 0

    def add_task_to_node(self):
        self.select_next_node()  # Select the next node to send a task to
        instruction = (
            self.master_queue.popleft()
        )  # Get the instruction from the master queue
        self.node_queues[self.current_node].append(
            instruction
        )  # Add the instruction to the node's queue
        # Send message to the specified node
        self.logger.info(f"Queueing instruction to Node {self.current_node}")

        self.logger.info(
            f"Node {self.current_node}'s queue length: {len(self.node_queues[self.current_node])}"
        )
        self.current_node = (self.current_node + 1) % len(self.node_processes)

    # This function is run in a separate thread to distribute tasks to nodes
    def __distribute_tasks(self):
        while True:
            if self.master_queue:
                self.add_task_to_node()
            else:
                time.sleep(1)

    # This function is run in a separate thread to assign tasks to nodes
    def __assign_tasks(self):
        while True:  # Loop indefinitely
            for node_id, idle in self.node_idleness.items():  # Iterate over each node
                if (
                    idle.is_set()
                    and self.node_processes[
                        node_id
                    ].is_alive()  # If node is idle and unalive, node is not on the queue
                ):  # If node is idle
                    queue = self.node_queues[node_id]
                    if self.node_pipes[
                        node_id
                    ].poll():  # Check if there’s any data sent from the worker
                        # Print the response from the node
                        response = self.node_pipes[node_id].recv()
                        self.logger.info(f"Node {node_id} response: {response}")
                        queue.popleft()  # Remove the task from the queue

                    if queue:
                        instruction = queue[0]
                        self.logger.info(f"Sending instruction to node {node_id}")
                        self.node_pipes[node_id].send(instruction)
                    else:
                        # Steal work from other queues
                        for other_node, other_queue in self.node_queues.items():
                            if other_node != node_id and len(other_queue) > 1:
                                self.logger.critical(
                                    f"Node {node_id} is stealing work from Node {other_node}!"
                                )
                                instruction = other_queue.pop()
                                self.logger.info(
                                    f"Node {other_node}'s queue length: {len(other_queue)}"
                                )
                                queue.append(instruction)
                                break
                                # self.node_pipes[node_id].send(instruction)
            time.sleep(1)

    def __init__(self, node_quantity, node_capacities):
        if node_quantity < 1:
            raise ValueError("Node quantity must be at least 1")
        self.node_processes = {}  # NodeID: Process
        self.node_pipes = {}  # NodeID: Pipe for heartbeat

        self.node_idleness = {}  # Dict for node idleness
        self.node_queues = {}  # Dict for node queues
        self.node_heartbeats = {}  # Dict for node heartbeat pipes
        self.active_nodes = {}  # Dict for active nodes
        self.current_node = 0
        self.logger = logging.getLogger("Master")
        self.logger.info(f"Master process ID: {os.getpid()} ")
        self.master_queue = (
            deque()
        )  # Queue that the master keeps that contains the instructions it receives
        self.resource_locks = {}  # Locks for resources
        self.resource_in_use = {}  # Resources in use by nodes
        self.resource_pipes = {}  # Pipes for resource management
        self.manager = multiprocessing.Manager()  # Manager to create shared resources
        self.resources = self.manager.dict()  # Shared resources

        for node_id in range(node_quantity):  # Create the specified number of nodes
            self.__create_node(node_id, node_capacities[node_id])

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

        # Start a thread to manage resources
        resource_thread = threading.Thread(target=self.resource_manager)
        resource_thread.daemon = True
        resource_thread.start()

        # Initialize the Flask server
        self.__initialize_server()

    def request_read_resource(self, node_id, resource):
        lock: ReadWriteLock = self.resource_locks[
            resource
        ]  # Get the lock for the resource
        lock.acquire_read()  # Acquire read lock
        self.logger.info(
            f"Node {node_id} has acquired read access to resource {resource}"
        )
        # Track the resource in the node's resource set
        if (
            node_id not in self.resource_in_use
        ):  # If the node is not in the resource set
            self.resource_in_use[node_id] = set()
        self.resource_in_use[node_id].add((resource, "read"))

    def release_read_resource(self, node_id, resource):
        lock = self.resource_locks[resource]  # Get the lock for the resource
        lock.release_read()  # Release read lock
        self.logger.info(
            f"Node {node_id} has released read access to resource {resource}"
        )
        # Remove the resource from the node's resource set
        if node_id in self.resource_in_use:  # If the node is in the resource set
            self.resource_in_use[node_id].discard((resource, "read"))
            # Clean up if no more resources are held by this node
            if not self.resource_in_use[node_id]:
                del self.resource_in_use[node_id]

    def request_write_resource(self, node_id, resource):
        lock = self.resource_locks[resource]
        lock.acquire_write()  # Acquire write lock
        self.logger.info(
            f"Node {node_id} has acquired write access to resource {resource}"
        )

        # Track the resource in the node's resource set
        if (
            node_id not in self.resource_in_use
        ):  # If the node is not in the resource set
            self.resource_in_use[node_id] = set()
        self.resource_in_use[node_id].add((resource, "write"))

    def release_write_resource(self, node_id, resource):
        lock = self.resource_locks[resource]
        lock.release_write()  # Release write lock
        self.logger.info(
            f"Node {node_id} has released write access to resource {resource}"
        )

        # Remove the resource from the node's resource set
        if node_id in self.resource_in_use:  # If the node is in the resource set
            self.resource_in_use[node_id].discard(
                (resource, "write")
            )  # Remove the resource
            # Clean up if no more resources are held by this node
            if not self.resource_in_use[
                node_id
            ]:  # If the node is not holding any resources
                del self.resource_in_use[node_id]

    def handle_read_request(self, node_id, resource, resource_pipe):
        self.request_read_resource(node_id, resource)  # Request read resource
        # If node died during wait, release the resource
        if (
            self.active_nodes[node_id] and self.node_processes[node_id].is_alive()
        ):  # If the node is active and alive
            shared_resource = self.resources.get(resource)[
                "resource"
            ]  # Get the shared resource
            resource_pipe.send(
                {"status": "granted_read", "resource": shared_resource}
            )  # Send the resource
        else:
            self.release_read_resource(node_id, resource)

    def handle_write_request(self, node_id, resource, resource_pipe):
        self.request_write_resource(node_id, resource)
        # If node died during wait, release the resource
        if (
            self.active_nodes[node_id] and self.node_processes[node_id].is_alive()
        ):  # If the node is active and alive
            shared_resource = self.resources.get(resource)[
                "resource"
            ]  # Get the shared resource
            resource_pipe.send(
                {"status": "granted_write", "resource": shared_resource}
            )  # Send the resource
        else:
            self.release_write_resource(node_id, resource)

    def resource_manager(self):
        while True:
            for node_id, resource_pipe in self.resource_pipes.items():
                if (
                    self.node_processes[node_id].is_alive()
                    and self.active_nodes[node_id]
                    and resource_pipe.poll()
                ):  # If the node is active and alive
                    message = resource_pipe.recv()  # Receive the message
                    type = message.get("type")  # Get the type of the message
                    resource = message.get("resource")  # Get the resource
                    if not self.resources.get(
                        resource
                    ):  # If the resource does not exist
                        resource_pipe.send(
                            {"status": "error", "message": "Resource not found"}
                        )
                        continue
                    if type == "request_read":  # If the message is a request to read
                        threading.Thread(
                            target=self.handle_read_request,
                            args=(node_id, resource, resource_pipe),
                        ).start()

                    elif (
                        type == "release_read"
                    ):  # If the message is a request to release read
                        self.release_read_resource(node_id, resource)
                        resource_pipe.send({"status": "released_read"})
                    elif (
                        type == "request_write"
                    ):  # If the message is a request to write
                        threading.Thread(
                            target=self.handle_write_request,
                            args=(node_id, resource, resource_pipe),
                        ).start()
                    elif (
                        type == "release_write"
                    ):  # If the message is a request to release write
                        self.release_write_resource(node_id, resource)
                        resource_pipe.send({"status": "released_write"})
            time.sleep(1)

    def run(self):
        if self.app:
            # Run Flask app
            self.app.run(port=5000)


# Example usage
if __name__ == "__main__":
    master = Master(node_quantity=5)
    master.run()
