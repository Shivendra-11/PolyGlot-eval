"""HTTP-style handlers for the fixture repo."""

from __future__ import annotations

from app.store import TaskStore

_store = TaskStore()


def create_task(title: str) -> dict:
    if title is None or not isinstance(title, str):
        raise TypeError("title must be a string")
    task = _store.add(title)
    return {"id": task.id, "title": task.title, "done": task.done}


def list_tasks() -> list[dict]:
    return [{"id": t.id, "title": t.title, "done": t.done} for t in _store.list_all()]


def stats() -> dict:
    return {"count": len(_store.list_all()), "avg_title_len": _store.average_title_length()}
