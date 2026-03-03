# **QAPF Bot**

QAPF Bot es un sistema experto desarrollado para la identificación y
clasificación de rocas ígneas mediante dos enfoques principales: una
observación cualitativa de campo y un análisis cuantitativo de laboratorio
basado en el diagrama QAPF de Streckeisen.

El núcleo lógico del sistema está construido en **Prolog** para aprovechar
su potente motor de inferencia y reglas, permitiendo modelar el conocimiento
geológico de manera declarativa. La interfaz de usuario se expone a través de
dos plataformas: una aplicación web interactiva con **Streamlit** y un bot
conversacional en **Telegram**.

---

## Características Principales

El sistema ofrece dos modos de uso adaptados a diferentes situaciones:

### 1. 🔍 Modo Campo (Identificación Visual)

Diseñado para la observación rápida en campo donde no se cuenta con
porcentajes exactos de minerales (muestras de mano).

- Clasificación basada en: **Textura**, **Índice de Color** y
  **Minerales Visibles**.
- Utiliza una jerarquía de reglas en Prolog para determinar la roca más
  probable (ej. Cuarzo Monzonita, Granodiorita, Riolita, Basalto, etc.).
- Filtra lógicamente combinaciones inválidas (ej. presencia simultánea
  de Cuarzo y Olivino).

### 2. 🧪 Modo Laboratorio (Diagrama QAPF - Streckeisen)

Diseñado para análisis cuantitativos precisos, típicos de un estudio
petrográfico.

- Clasificación basada en porcentajes modales de:
  - **Q**: Cuarzo
  - **A**: Feldespato Alcalino
  - **P**: Plagioclasa
- Requiere especificar si la textura es plutónica (fanerítica) o
  volcánica (afanítica).
- El sistema normaliza los valores y ubica la roca en el diagrama de
  Streckeisen.

---

## Arquitectura y Tecnologías

El proyecto se divide en módulos que comparten el motor de inferencia:

- **Lógica Experta**: SWI-Prolog (`geologia.pl`)
- **Backend / Puente**: Python + `pyswip`
- **Interfaces**:
  - **Web**: Streamlit (`interfaz_streamlit/`)
  - **Bot**: Telegram Bot API (`bot_telegram/`)
- **Despliegue Serverless**: Modal (Para el webhook del bot de Telegram)

### Estructura del Repositorio

```text
.
├── bot_telegram/               # Código para el Bot de Telegram
│   ├── bot_modal.py            # Script de pruebas de Modal
│   ├── bot_webhook.py          # Configuración del Webhook usando Modal
│   ├── cerebro.py              # Clase puente Python-Prolog para el bot
│   ├── geologia.pl             # Reglas y base de conocimiento (Prolog)
│   └── interfaz_telegram.py    # Lógica de interacciones y menús del Bot
├── interfaz_streamlit/         # Código para la Interfaz Web
│   ├── cerebro.py              # Clase puente Python-Prolog para la web
│   ├── geologia.pl             # Reglas y base de conocimiento (Prolog)
│   └── interfaz_web.py         # Interfaz construida con Streamlit
├── requirements.txt            # Dependencias (Streamlit, PySwip, etc)
└── packages.txt                # Dependencias del sistema (SWI-Prolog)
```

*(Nota: Existen dos copias de `geologia.pl` y `cerebro.py` para aislar el
funcionamiento de cada interfaz durante el desarrollo).*

---

## 🚀 Instalación y Uso Local

### Prerrequisitos

Dado que el motor lógico es Prolog, **es obligatorio instalar SWI-Prolog**
en tu sistema antes de ejecutar la aplicación.

- **Ubuntu/Debian**: `sudo apt install swi-prolog`
- **Windows / macOS**: Descargar desde [swi-prolog.org](https://www.swi-prolog.org/).
  En Windows, asegúrate de que el directorio de instalación se agregue a la
  variable de entorno PATH.

### Configuración del entorno Python

1. Clona el repositorio.
2. Crea un entorno virtual (recomendado):

   ```bash
   python -m venv venv
   source venv/bin/activate  # En Linux/Mac
   venv\Scripts\activate     # En Windows
   ```

3. Instala las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

### Ejecutar la Aplicación Web (Streamlit)

Navega a la carpeta de la interfaz web y ejecuta el siguiente comando:

```bash
cd interfaz_streamlit
streamlit run interfaz_web.py
```

La aplicación se abrirá automáticamente en tu navegador por defecto
(usualmente en `http://localhost:8501`).

### Ejecutar el Bot de Telegram (Local o Webhook)

Para que el bot funcione, necesitas un token de Telegram (obtenido desde
BotFather) y configurarlo como variable de entorno `TELEGRAM_TOKEN`.

- **Despliegue Serverless con Modal (Webhook)**:
  El archivo `bot_webhook.py` está preparado para desplegarse como una
  función de Modal.

  ```bash
  cd bot_telegram
  modal deploy bot_webhook.py
  ```

  *(Nota: Requiere tener configurada la cuenta de Modal y los secrets).*

---

## Base de Conocimiento Geológico (`geologia.pl`)

El archivo de Prolog contiene reglas distribuidas en:

- **Nivel 1 al 6 (Modo Visual)**: Identifica desde rocas con los 3 minerales
  principales (Cuarzo Monzonita) hasta rocas ultramáficas (Peridotita) y
  texturas especiales (Obsidiana, Piedra Pómez).
- **Módulo QAPF**: Normaliza automáticamente el ratio de Plagioclasa vs
  (Feldespato Alcalino + Plagioclasa) y utiliza las fronteras definidas por
  la IUGS para clasificar desde Cuarzolita hasta Gabro/Basalto.

---

*Desarrollado para facilitar la clasificación petrográfica combinando IA
simbólica (Sistemas Expertos) con interfaces modernas.*
