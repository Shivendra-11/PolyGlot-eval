"""Simple in-memory task store (fixture repo for polyglot-eval proof-of-execution)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Task:
    id: int
    title: str
    done: bool = False


@dataclass
class TaskStore:
    """In-memory task list."""

    _tasks: list[Task] = field(default_factory=list)

    def add(self, title: str) -> Task:
        if not title or not title.strip():
            raise ValueError("title must be non-empty")
        task = Task(id=len(self._tasks) + 1, title=title.strip())
        self._tasks.append(task)
        return task

    def list_all(self) -> list[Task]:
        return list(self._tasks)

    def average_title_length(self) -> float:
        """Return average title length; empty store returns 0.0."""
        if not self._tasks:
            return 0.0
        total = sum(len(t.title) for t in self._tasks)
        return total / len(self._tasks)
