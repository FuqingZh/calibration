# Method Naming

Use these rules for public object method names.

Public methods should mainly express protocol, lifecycle, or object-local
configuration. Domain behavior should remain module-level functions that follow
the prefix rules in `function.md`.

Allowed common public methods:

- `close()`
- `run()`
- `render()`
- `report()`
- `build()` on `*Builder`
- `from_*()` or `make()` as classmethod factories
- `add_*`, `select_*`, `group()`, `command()`, `done()`, `end()`, `with_*`
  on builders or fluent configuration helpers

Prefer module-level functions over vague public methods such as:

- `save`, `load`, `export`, `dump`
- `execute`, `start`, `stop`, `finish`, `shutdown`, `dispose`
- `process`, `do`, `get`, `show`
