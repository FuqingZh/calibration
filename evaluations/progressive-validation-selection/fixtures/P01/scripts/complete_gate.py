from check_event import run


def check() -> None:
    import docs_check
    import runtime_test


run("complete_gate", "repository-complete-gate", check)
