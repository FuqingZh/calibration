from check_event import run


def check() -> None:
    import focused_test
    import unrelated_suite


run("complete_gate", "repository-complete-gate", check)
