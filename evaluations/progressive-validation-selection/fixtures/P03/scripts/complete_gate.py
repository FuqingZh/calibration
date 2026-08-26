from check_event import run


def check() -> None:
    import structural_check
    import behavior_sample
    import docs_only


run("complete_gate", "repository-complete-gate", check)
