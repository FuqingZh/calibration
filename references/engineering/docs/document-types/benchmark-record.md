# Benchmark Record

## Use When

Use this type for a reproducible performance, numerical consistency, capacity,
or scale measurement and the claim supported by its result.

## Method Reference

Follow the project measurement and reproducibility rules. Treat the benchmark
as an evidence record, not as a standalone headline number.

## Local Requirements

- Place it in project `docs/benchmarks/` when the project maintains benchmark
  records there.
- State the question, workload, inputs, environment, versions, and baseline.
- Define metrics, protocol, repetitions, random seed where relevant, and
  comparison method.
- Preserve the output path or artifact needed to inspect the result.
- Report results with uncertainty, limitations, and any failed or skipped
  checks.
- State the conditions under which the result remains comparable or should be
  rerun.

## Complete When

An independent contributor can reproduce the measurement, inspect its output,
and understand exactly what the result does and does not establish.
