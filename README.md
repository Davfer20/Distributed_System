# Distributed_System

El proyecto es un simulador de un sistema distribuido, diseñado para gestionar recursos y procesos en un entorno simulado de nodos interconectados. Cada nodo representa una instancia básica de un sistema operativo que puede procesar tareas, comunicarse y sincronizarse con otros nodos.

Elaborado por:

- José David Fernández Salas
- Daniel Granados Retana
- Diego Granados Retana

## Documentación

La documentación principal se encuentra en el PDF titulado: **Documentación_Distributed_System**  
En este archivo, se encuentra la documentación del diseño y los resultados de las pruebas.

Para ejecutar el archivo, se ejecuta el archivo master.py.  
Asimismo, se puede ejecutar el archivo main, donde se leería la configuración de un archivo .yaml.  
Este archivo se especifica en la línea 131:

```
if __name__ == "__main__":
    try:
        with open("Prueba4.yaml", "r") as file: # Configuration file
            parsed_data = yaml.safe_load(file)
    except FileNotFoundError:
        print("El archivo config.yml no se encuentra.")
        exit(1)
    except yaml.YAMLError as e:
        print(f"Error al leer el archivo YAML: {e}")
        exit(1)

```

## Enlace a video

Se adjunta un video que explica los casos de uso solicitados y las pruebas realizadas:
https://www.youtube.com/watch?v=TC1m2JYcBTY
Capítulos:
0:00 Introducción
0:10 Arquitectura
1:40 Ejecución
1:50 Master
5:05 Node
8:23 Caso de Uso 1: Asignación
10:55 Caso de Uso 2: Recursos compartidos
14:30 Caso de Uso 3: Manejo de fallos
17:45 Prueba 1: Asignación y Balanceo
21:26 Prueba 2: Sincronización de recursos
25:00 Prueba 3: Manejo de fallos
29:40 Prueba 4: Escalabilidad
31:18 Prueba 5: Redistribución

## Enlace al repositorio

https://github.com/Diego-Granados/Sistema-de-Archivos
