from hypothesis import given, strategies as st

@given(st.lists(st.text()))
def test_task_id_generation(tasks):
    # Ensure no collisions, valid format, etc.
    from core.orchestrator import load_all_tasks
    loaded = load_all_tasks()
    ids = [t['task_id'] for t in loaded]
    assert len(ids) == len(set(ids))  # No duplicates
    for tid in ids:
        assert tid.startswith('task_')
        assert tid[5:].isdigit()