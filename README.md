# jira-data

Sistema para descarga de información de Jira.  
Descarga la **dedicación de horas** (worklogs) registrada en las tareas junto con los **datos del proyecto** asociado y los exporta a archivos CSV.

---

## Requisitos

- Python 3.9+
- Acceso a una instancia de Jira (Cloud o Server) con una API token

## Instalación

```bash
pip install -r requirements.txt
```

## Configuración

Copia el archivo de ejemplo y rellena tus credenciales:

```bash
cp .env.example .env
```

Variables disponibles en `.env`:

| Variable        | Descripción                                                          | Obligatorio |
|-----------------|----------------------------------------------------------------------|-------------|
| `JIRA_URL`      | URL de tu instancia de Jira, p. ej. `https://xxx.atlassian.net`     | Sí          |
| `JIRA_USER`     | Email del usuario de Jira                                            | Sí          |
| `JIRA_TOKEN`    | API token de Jira ([obtener aquí](https://id.atlassian.com/manage-profile/security/api-tokens)) | Sí |
| `JIRA_PROJECTS` | Claves de proyecto separadas por coma (vacío = todos los proyectos) | No          |
| `OUTPUT_DIR`    | Directorio de salida (por defecto: `output`)                         | No          |

## Uso

```bash
python main.py
```

Al finalizar se generan dos archivos CSV en el directorio de salida:

### `output/worklogs.csv`

Un registro por cada entrada de tiempo (worklog):

| Columna               | Descripción                              |
|-----------------------|------------------------------------------|
| `project_key`         | Clave del proyecto                       |
| `project_name`        | Nombre del proyecto                      |
| `issue_key`           | Clave de la tarea (p. ej. `PROJ-42`)     |
| `issue_summary`       | Título de la tarea                       |
| `issue_type`          | Tipo de tarea (Bug, Story, Task…)        |
| `issue_status`        | Estado actual de la tarea                |
| `assignee`            | Asignado a la tarea                      |
| `worklog_id`          | ID interno del worklog                   |
| `author`              | Persona que registró el tiempo           |
| `started`             | Fecha/hora de inicio del registro        |
| `time_spent_seconds`  | Tiempo registrado en segundos            |
| `time_spent_hours`    | Tiempo registrado en horas               |
| `comment`             | Comentario del worklog                   |

### `output/projects.csv`

Un registro por proyecto:

| Columna                  | Descripción                                 |
|--------------------------|---------------------------------------------|
| `project_key`            | Clave del proyecto                          |
| `project_name`           | Nombre del proyecto                         |
| `lead`                   | Responsable del proyecto                    |
| `issue_count`            | Número total de tareas en el proyecto       |
| `total_worklog_entries`  | Número total de entradas de worklog         |

## Estructura del proyecto

```
jira-data/
├── main.py              # Punto de entrada
├── requirements.txt
├── .env.example
├── src/
│   ├── jira_client.py   # Cliente autenticado de Jira
│   ├── downloader.py    # Lógica de descarga de datos
│   └── exporter.py      # Exportación a CSV
└── tests/
    ├── test_downloader.py
    └── test_exporter.py
```

## Tests

```bash
pip install pytest
pytest tests/ -v
```