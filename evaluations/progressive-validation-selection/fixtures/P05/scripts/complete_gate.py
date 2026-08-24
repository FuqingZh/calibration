from check_event import run


def check() -> None:
    import schema_contract
    import consumer_a
    import consumer_b


run("complete_gate", "repository-complete-gate", check)
