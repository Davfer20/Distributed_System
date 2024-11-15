from master import Master
import multiprocessing
import requests
import yaml
import time


def parseYaml(parsed_data):
    if "system" not in parsed_data:
        print("Error: La clave 'system' no está presente en los datos.")
        return None, None

    system_data = parsed_data["system"]

    node_quantity = system_data.get("node_quantity", 0)
    print("Node Quantity:", node_quantity)

    node_capacities = system_data.get("node_capacities", [])
    print("Node Capacities:")
    for capacity in node_capacities:
        print(f"  - {capacity}")

    shared_resources = system_data.get("shared_resources", [])
    print("Shared Resources:")
    for resource in shared_resources:
        name = resource.get("name", "N/A")
        resource_type = resource.get("type", "N/A")
        values = resource.get("values", {})

        print(f"  Name: {name}")
        print(f"  Type: {resource_type}")
        print(f"  Values:")
        for key, value in values.items():
            print(f"    {key}: {value}")

    print("Requests:")
    requests = system_data.get("requests", [])
    for request in requests:
        endpoint = request.get("endpoint", "N/A")
        method = request.get("method", "N/A")
        sleep = request.get("sleep", "N/A")
        body = request.get("body", {})
        body_type = body.get("type", "N/A")
        command = body.get("command", "N/A")

        print(f"  - Endpoint: {endpoint}")
        print(f"    Method: {method}")
        print(f"    Sleep: {sleep}")
        print(f"    Body Type: {body_type}")
        print(f"    Command:\n{command}")

    return node_quantity, node_capacities


def executeRequests(parsed_data):
    requests_list = parsed_data["system"].get("requests", [])
    for request in requests_list:
        endpoint = request.get("endpoint", "N/A")
        method = request.get("method", "N/A")
        sleep = request.get("sleep", "N/A")
        body = request.get("body", {})
        body_type = body.get("type", "N/A")
        command = body.get("command", "N/A")

        data = None
        headers = {}
        if body_type == "json":
            data = command  # Enviar como JSON
            headers = {"Content-Type": "application/json"}
        elif body_type == "form":
            data = command  # Enviar como datos de formulario

        # Ejecutar la solicitud HTTP
        try:
            if method == "GET":
                response = requests.get(endpoint)
            elif method == "POST":
                response = requests.post(
                    endpoint,
                    json=data if body_type == "json" else None,
                    data=data if body_type == "form" else None,
                    headers=headers,
                )
            elif method == "PUT":
                response = requests.put(
                    endpoint,
                    json=data if body_type == "json" else None,
                    data=data if body_type == "form" else None,
                    headers=headers,
                )
            elif method == "DELETE":
                response = requests.delete(endpoint)
            else:
                print(f"  - Método {method} no soportado.")
                continue

            # Imprimir el resultado de la solicitud
            print(f"  - Código de respuesta: {response.status_code}")
            print(f"  - Respuesta: {response.text}")

        except requests.RequestException as e:
            print(f"Error al ejecutar la solicitud: {e}")

        # Pausar antes de ejecutar la próxima solicitud
        time.sleep(sleep)


def inicializeMaster(node_quantity, node_capacities):
    master = Master(node_quantity, node_capacities)
    master.run()


if __name__ == "__main__":
    try:
        with open("config.yml", "r") as file:
            parsed_data = yaml.safe_load(file)
    except FileNotFoundError:
        print("El archivo config.yml no se encuentra.")
        exit(1)
    except yaml.YAMLError as e:
        print(f"Error al leer el archivo YAML: {e}")
        exit(1)

    # node_quantity, node_capacities = parseYaml(parsed_data)

    if parsed_data["system"]["requests"] != []:
        executeRequests(parsed_data)

    # process = multiprocessing.Process(
    #     target=inicializeMaster,
    #     args=(node_quantity, node_capacities),
    # )
    # process.start()

    # time.sleep(8)
    # print("Master is running")
