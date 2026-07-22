# CLI Option Naming

Follow the [GNU CLI conventions](https://www.gnu.org/prep/standards/html_node/Command_002dLine-Interfaces.html),
its [long-option table](https://www.gnu.org/prep/standards/html_node/Option-Table.html),
and the [CLI Guidelines](https://clig.dev/).

Local additions:

- Follow the parser's native spelling; absent a stronger convention, use
  lowercase kebab-case for long options.
- Use operands for unambiguous required primary inputs and options for
  configuration or output, including `-o` / `--output` when appropriate.
- Preserve published compatibility and repository-local terminology.
