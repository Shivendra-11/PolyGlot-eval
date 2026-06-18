# I2 Report — fixture-repo

## entry_point

`app/main.py:1` — `create_task`

## trace_path

1. `app/main.py:1` **create_task** — Entry module app/main.py
2. `app/main.py:17` **list_tasks** — Callable list_tasks
3. `app/main.py:21` **stats** — Callable stats

## external_deps

- HTTP client: Outbound API calls if present
- File system: Config and static assets

## side_effects

- http_call: `app/main.py`

## sequence_diagram

```mermaid
sequenceDiagram
    participant Client
    participant App as fixture-repo
    participant Handler as create_task
    participant Store as Data Layer

    Client->>App: /
    App->>Handler: create_task()
    Handler->>Store: read/write
    Store-->>Handler: result
    Handler-->>App: response
    App-->>Client: 200 OK
```

## uncertainty

- Dynamic imports and runtime routing may extend this trace
