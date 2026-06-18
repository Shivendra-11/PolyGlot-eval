from app.store import TaskStore


def test_add_task():
    store = TaskStore()
    t = store.add("hello")
    assert t.id == 1
    assert t.title == "hello"


def test_add_rejects_empty_title():
    store = TaskStore()
    try:
        store.add("")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_average_title_length():
    store = TaskStore()
    store.add("ab")
    store.add("abcd")
    assert store.average_title_length() == 3.0


def test_average_title_length_empty_store():
    store = TaskStore()
    assert store.average_title_length() == 0.0
