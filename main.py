from Node import Node

if __name__ == "__main__":
    # Nodo servidor
    nodo_servidor = Node("127.0.0.1", 12345)
    nodo_servidor.iniciar_nodo()
    # Nodo cliente
    nodo_cliente = Node("127.0.0.1", 54321)
    nodo_cliente.enviar_mensaje("127.0.0.1", 12345, "Hola, este es un mensaje!")

    nodo_servidor.cerrar_nodo()
