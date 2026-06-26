# Dependencias FARO v5.3

FARO v5.3 agrega revisión automática de dependencias.

## Al abrir

`ABRIR_FARO.bat` ejecuta:

```text
faro_dependency_check.py
```

Si todo está instalado, no instala nada.

Si en el futuro `requirements.txt` incluye paquetes externos, FARO instalará solo los que falten.

## Módulos base revisados

- tkinter
- sqlite3
- webbrowser
- urllib.parse
- pathlib
- json
- csv
- html
- uuid

## Log

```text
faro_data/dependency_check.log
```

## Nota

Actualmente FARO usa solamente librerías estándar de Python.
