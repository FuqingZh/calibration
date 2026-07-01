# Loop and Closure Binder Naming

Use these rules for loop binders, lambda parameters, closure parameters, and
anonymous-function binders.

- In Python and Rust loop binders, use an underscore-prefixed binder such as
  `_sheet` or `_name`.
- In Python `lambda` parameters and Rust closure parameters, use the same
  underscore-prefixed binder style as loops, such as `_sheet` or `_name`.
- In R loop binders, use a dot-prefixed binder such as `.sheet` or `.name`.
- In R anonymous function parameters, including `\(.x)` style binders, use the
  same dot-prefixed binder style as loops, such as `.sheet` or `.name`.
