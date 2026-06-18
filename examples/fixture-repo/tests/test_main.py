from app.main import create_task


def test_create_task_rejects_none():
    try:
        create_task(None)  # type: ignore[arg-type]
        assert False, "expected TypeError"
    except TypeError:
        pass
