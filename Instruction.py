class Instruction:
    def __init__(self, type, command):
        self.type = type  # The type of instruction can be python, shell, or STOP to kill the Node.
        self.command = command  # The command to execute in the Node.
