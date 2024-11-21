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

## Enlace al repositorio

https://github.com/Diego-Granados/Sistema-de-Archivos
