# FARO

**F.A.R.O. = Familia, Alerta, Resguardo y Orientación**

**FARO** es una herramienta gratuita de protección familiar contra estafas digitales.  
Fue desarrollada **únicamente por xtr4ng3**, sin fines de lucro, con una idea simple: ayudar a que una persona no tenga que enfrentar sola una llamada, un correo o un link sospechoso.

> Desarrollado por y para el pueblo.  
> **FR33 M4N.**

---

## Qué es FARO

FARO es un asistente local para prevenir estafas por:

- llamadas telefónicas;
- mensajes de WhatsApp;
- correos electrónicos falsos;
- links sospechosos;
- pedidos de dinero, claves, códigos o datos personales.

FARO no reemplaza a una denuncia, a la justicia, a la policía ni al acompañamiento familiar.  
FARO ayuda a **frenar, pensar, verificar y pedir ayuda antes de actuar**.

---

## Para quién está pensado

FARO está pensado para:

- personas mayores;
- familias;
- cuidadores;
- vecinos de confianza;
- centros de jubilados;
- espacios comunitarios;
- personas que reciben llamadas o correos dudosos;
- cualquier persona que quiera verificar antes de responder.

---

## Qué problema intenta resolver

Muchas estafas funcionan igual:

1. alguien llama o escribe;
2. dice ser familiar, banco, soporte, correo, empresa u organismo;
3. mete urgencia;
4. pide dinero, claves, códigos, transferencias o datos;
5. intenta que la persona no consulte con nadie.

FARO rompe esa cadena.

Cuando algo parece raro, FARO permite marcar lo que está pasando y preparar una alerta para contactos de confianza.

---

## Funciones principales

### Llamada en vivo

Durante una llamada sospechosa, la persona puede marcar señales simples:

- dice ser un familiar;
- cambió de número;
- pide dinero;
- pide transferencia;
- pide código, token o clave;
- pide secreto;
- amenaza con bloqueo, deuda o cierre;
- manda un link;
- pide instalar una app.

FARO calcula un nivel de riesgo y activa alertas.

---

## Umbrales de alerta

FARO no espera a que el riesgo llegue al máximo.

```text
43% o más  -> AVISAR: NECESITO ASEGURAR
70% o más  -> ALERTA URGENTE
90% o más  -> PROTECCIÓN INMEDIATA
```

### Aviso preventivo

Cuando el riesgo supera el 43%, FARO permite avisar:

```text
Me están llamando y necesito asegurar que todo esté bien antes de responder.
```

### Alerta urgente

Cuando el riesgo supera el 70%, FARO prepara una alerta más fuerte:

```text
Me están llamando y necesito ayuda urgente para verificar que no sea una estafa.
```

### Protección inmediata

Cuando el riesgo supera el 90%, FARO recomienda no avanzar, no compartir datos y pedir ayuda de inmediato.

---

## WhatsApp Web

FARO puede abrir WhatsApp Web con un mensaje preparado para contactos de confianza.

FARO **no envía mensajes ocultos**.  
FARO **no presiona enviar solo**.  
FARO abre WhatsApp con el texto cargado para que la persona revise y confirme.

Esto es importante para evitar abusos y mantener el uso transparente.

---

## Contactos de confianza

FARO permite cargar contactos de confianza extrema.

Recomendación:

- cargar pocos contactos;
- usar personas realmente cercanas;
- revisar que el número esté bien escrito;
- probar WhatsApp desde la sección de contactos.

Formato recomendado para Argentina:

```text
+549011XXXXXXX
```

Sin `+`, sin espacios, sin guiones y sin paréntesis.

---

## Analizador de correos

FARO incluye un analizador de correos sospechosos.

Puede revisar:

- remitente;
- dominio;
- entidad que dice ser;
- asunto;
- cuerpo del correo;
- pedidos de contraseña, código, pago, tarjeta o datos;
- amenazas de cierre o bloqueo;
- links sospechosos.

Incluye referencias defensivas para casos frecuentes en Argentina y servicios conocidos:

- ARCA / ex AFIP;
- ANSES;
- Banco Nación;
- Santander;
- Banco Galicia;
- Banco Macro;
- Mercado Pago;
- Correo Argentino;
- Personal / Flow / Telecom;
- Microsoft / Outlook / Hotmail;
- Google / Gmail;
- Netflix.

FARO no afirma que un correo sea delito.  
FARO alerta cuando algo no coincide o cuando el contenido parece peligroso.

---

## Scanner de links

FARO puede revisar links sin abrirlos.

Detecta señales como:

- acortadores;
- dominios raros;
- uso de HTTP;
- palabras de riesgo;
- imitación de marcas;
- enlaces largos o confusos.

También genera una versión segura del link, por ejemplo:

```text
hxxps://sitio[.]sospechoso[.]com
```

---

## Cómo usar FARO

### 1. Descargar

Descargar el ZIP y extraerlo en una carpeta.

### 2. Abrir

Ejecutar:

```text
ABRIR_FARO.bat
```

### 3. Cargar contactos

Ir a **Contactos** y cargar al menos un contacto de confianza.

### 4. Usar llamada en vivo

Ir a **Llamada en vivo**, marcar lo que está pasando y tocar **Actualizar análisis**.

### 5. Avisar

Si FARO activa un botón de aviso, tocar:

```text
AVISAR: NECESITO ASEGURAR
```

o:

```text
ALERTA URGENTE
```

FARO abrirá WhatsApp Web con el mensaje preparado.

---

## Revisión de dependencias

FARO revisa automáticamente el entorno antes de abrir.

Si ya está todo instalado, no instala nada.

Archivos importantes:

```text
ABRIR_FARO.bat
INSTALAR_DEPENDENCIAS_FARO.bat
VALIDAR_FARO.bat
requirements.txt
```

Actualmente FARO usa principalmente librerías estándar de Python.

---

## Datos y privacidad

FARO trabaja de forma local.

- No sube datos automáticamente.
- No envía información a servidores externos propios.
- No vende datos.
- No espía conversaciones.
- No abre links sospechosos automáticamente.
- No envía mensajes ocultos.

Los datos se guardan en la carpeta local del programa.

---

---

## Autoría

Proyecto desarrollado únicamente por:

```text
xtr4ng3
```

FARO fue creado como una herramienta social, libre y comunitaria.

```text
Por y para el pueblo.
FR33 M4N.
```

---

## Aviso legal

FARO es una herramienta de prevención, orientación y ayuda familiar.  
No garantiza detectar todas las estafas.  
No reemplaza una denuncia formal.  
No reemplaza asesoramiento legal, bancario o institucional.  
Ante una emergencia real, contactar a familiares, autoridades o canales oficiales.

---

## Licencia

<img width="300" height="159" alt="giphy (25)" src="https://github.com/user-attachments/assets/021720ff-3aec-4916-9a93-25d47afd7d97" />

**xtr4ng3**

MIT.
