import requests

url = "http://127.0.0.1:5000/send/0"

# Comandos a ejecutar
commands = [
    {"type": "python", "command": "('hola mundo')"},
    {"type": "python", "command": "('adios mundo')"},
]

# Envía cada comando en orden
for index, command in enumerate(commands):
    print(f"Enviando comando {index + 1}: {command['command']}")
    response = requests.post(url, json=command)

    # Imprime el estado de la respuesta y el resultado
    if response.status_code == 200:
        print(f"Respuesta exitosa para el comando {index + 1}: {response.text}")
    else:
        print(f"Error en la solicitud del comando {index + 1}: {response.status_code}")
