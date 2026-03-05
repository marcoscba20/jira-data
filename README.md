# jira-data

Sistema para descarga de información de Jira.  
Descarga la **dedicación de horas** (worklogs) registrada en las tareas junto con los **datos del proyecto** asociado.  
Los worklogs se almacenan en **Azure Table Storage** y los datos de proyectos se exportan a un archivo CSV.

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

| Variable                           | Descripción                                                          | Obligatorio |
|------------------------------------|----------------------------------------------------------------------|-------------|
| `JIRA_URL`                         | URL de tu instancia de Jira, p. ej. `https://xxx.atlassian.net`     | Sí          |
| `JIRA_USER`                        | Email del usuario de Jira                                            | Sí          |
| `JIRA_TOKEN`                       | API token de Jira ([obtener aquí](https://id.atlassian.com/manage-profile/security/api-tokens)) | Sí |
| `JIRA_PROJECTS`                    | Claves de proyecto separadas por coma (vacío = todos los proyectos) | No          |
| `OUTPUT_DIR`                       | Directorio de salida para el CSV de proyectos (por defecto: `output`) | No        |
| `AZURE_STORAGE_CONNECTION_STRING`  | Cadena de conexión completa de Azure Storage (opción 1)             | Sí\*        |
| `AZURE_STORAGE_ACCOUNT_NAME`       | Nombre de la cuenta de Azure Storage (opción 2)                     | Sí\*        |
| `AZURE_STORAGE_ACCOUNT_KEY`        | Clave de la cuenta de Azure Storage (opción 2)                      | Sí\*        |
| `AZURE_TABLE_NAME`                 | Nombre de la tabla en Azure Table Storage (por defecto: `worklogs`) | No          |

> \* Para Azure Storage se puede usar `AZURE_STORAGE_CONNECTION_STRING` **o** el par `AZURE_STORAGE_ACCOUNT_NAME` + `AZURE_STORAGE_ACCOUNT_KEY`. Al menos una de las opciones es obligatoria.

## Uso

```bash
python main.py
```

Al finalizar se generan los siguientes resultados:

- Los **worklogs** se almacenan en Azure Table Storage en la tabla configurada (`AZURE_TABLE_NAME`).
- Se genera un archivo CSV con el resumen de **proyectos** en el directorio de salida.

### Azure Table Storage: worklogs

Cada worklog se almacena como una entidad en la tabla configurada.

| Campo                 | Descripción                              |
|-----------------------|------------------------------------------|
| `PartitionKey`        | Clave del proyecto (`project_key`)       |
| `RowKey`              | ID interno del worklog (`worklog_id`)    |
| `project_name`        | Nombre del proyecto                      |
| `issue_key`           | Clave de la tarea (p. ej. `PROJ-42`)     |
| `issue_summary`       | Título de la tarea                       |
| `issue_type`          | Tipo de tarea (Bug, Story, Task…)        |
| `issue_status`        | Estado actual de la tarea                |
| `assignee`            | Asignado a la tarea                      |
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
│   ├── jira_client.py         # Cliente autenticado de Jira
│   ├── downloader.py          # Lógica de descarga de datos
│   ├── exporter.py            # Exportación de proyectos a CSV
│   └── azure_table_exporter.py  # Exportación de worklogs a Azure Table Storage
└── tests/
    ├── test_downloader.py
    ├── test_exporter.py
    └── test_azure_table_exporter.py
```

## Tests

```bash
pip install pytest
pytest tests/ -v
```