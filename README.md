# UDP File Transfer

## Descripción :book:

Trabajo Práctico número 2 de la materia **Introducción a los Sistemas Distribuidos** (75.43), dictada en la Facultad de Ingeniería de la Universidad de Buenos Aires.

## Integrantes :busts_in_silhouette:

| Nombre | Apellido    | Padrón | Mail                   |
| ------ | ----------- | ------ | ---------------------- |
| Mauro  | Parafati    | 102749 | mparafati@fi.uba.ar    |
| Taiel  | Colavecchia | 102510 | tcolavecchia@fi.uba.ar |
| Yuhong | Huang       | 102146 | yhuang@fi.uba.ar       |

## Requisitos :ballot_box_with_check:

Se listan a continuación los requisitos necesarios para poder correr el proyecto:

-   [Python3](https://www.python.org/downloads/)

## Uso :computer: <MIGHT BE OUTDATED, FROM TP1>

Se detalla a continuación una breve explicación para correr el programa:

### Servidor

El servidor consta de un sólo comando `start-server`, que permite iniciar el servidor. Para ejecutarlo, o bien se puede optar por:

```python
./start-server [-h] [-v | -q] [-H ADDR] [-p PORT] [-s DIRPATH]
```

Para lo cual podría ser necesario darle permisos de ejecución al script (`chmod +x ./start-server`), o bien por la segunda opción:

```python
python3 start-server [-h] [-v | -q] [-H ADDR] [-p PORT] [-s DIRPATH]
```

Pueden utilizarse distintos flags:

-   [`-h` o `--help`] permite mostrar el mensaje de ayuda y detalle de los distintos flags.
-   [`-v` o `--verbose` | `-q` o `--quiet`] maneja el nivel de profundidad del logging.
-   [`-H` o `--host`] permite indicar el host donde se quiere levantar el servidor.
-   [`-p` o `--port`] permite indicar el puerto donde se quiere levantar el servidor.
-   [`-s` o `--storage`] permite indicar el directorio donde se quieren bajar los archivos.

### Cliente

El cliente cuenta con tres comandos distintos:

-   `list-files`: permite descargar la lista de archivos disponibles en el servidor.
-   `upload-file`: permite subir un archivo al servidor.
-   `download-file`: permite descargar un archivo del servidor.

Los tres comandos pueden correrse con los siguientes flags:

-   [`-h` o `--help`] permite mostrar el mensaje de ayuda y detalle de los distintos flags.
-   [`-v` o `--verbose` | `-q` o `--quiet`] maneja el nivel de profundidad del logging.
-   [`-H` o `--host`] permite indicar el host del servidor al que se quiere enviar el comando.
-   [`-p` o `--port`] permite indicar el puerto del servidor al que se quiere enviar el comando.

Además de ciertos flags adicionales según cada comando.

#### upload-file

Este comando puede correrse de las siguientes dos formas:

```python
$ ./upload-file [-h] [-v | -q] [-H ADDR] [-p PORT] -s FILEPATH -n FILENAME
```

```python
$ python3 upload-file [-h] [-v | -q] [-H ADDR] [-p PORT] -s FILEPATH -n FILENAME
```

Donde vemos que tenemos dos parámetros adicionales **obligatorios**:

-   `-s` o `--src` para indicar la ruta al archivo que queremos subir.
-   `-n` o `--name` para indicar el nombre con el que queremos guardar el archivo en el servidor.

#### download-file

Este comando puede correrse de las siguientes dos formas:

```python
$ ./download-file [-h] [-v | -q] [-H ADDR] [-p PORT] -d FILEPATH -n FILENAME
```

```python
$ python3 download-file [-h] [-v | -q] [-H ADDR] [-p PORT] -d FILEPATH -n FILENAME
```

Donde vemos que, al igual que con `upload-file`, tambén tenemos dos parámetros adicionales **obligatorios**:

-   `-d` o `--dest` para indicar la ruta donde queremos almacenar el archivo descargado del servidor.
-   `-n` o `--name` para indicar el nombre del archivo en el servidor que queremos descargar.

#### list-files

Este último comando puede correrse de las siguientes dos formas:

```python
$ ./list-files [-h] [-v | -q] [-H ADDR] [-p PORT] [-n | -s | -d] [-a]
```

```python
$ python3 list-files [-h] [-v | -q] [-H ADDR] [-p PORT] [-n | -s | -d] [-a]
```

Donde vemos que tenemos dos parámetros adicionales **opcionales**:

-   [`-n` o `--by-name` | `-s` o `--by-size` | `-d` o `--by-date`] para indicar el criterio con el que se quiere ordenar los resultados.
-   [`-a` o `--ascending`] para indicar que queremos ordenar de forma ascendente.
