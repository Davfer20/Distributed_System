from Master import Master
import logging

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    master = Master(node_quantity=2, node_capacities=[6, 6])
    master.run()
