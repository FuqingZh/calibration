# Compatibility Record

## Use When

Use this type for verified constraints, deviations, failure signatures, or safe
adaptations at an external or third-party boundary.

## Method Reference

Use compatibility-policy examples such as the [Kubernetes version skew
policy](https://kubernetes.io/releases/version-skew-policy/) and [MDN
compatibility tables](https://developer.mozilla.org/en-US/docs/MDN/Writing_guidelines/Page_structures/Compatibility_tables)
for explicit versions, scope, and supported combinations.

## Local Requirements

- Place it in project `docs/compatibility/` when the project uses the shared
  compatibility location.
- Identify the external boundary, version, environment, and expected contract.
- Separate observed behavior from inference or recommendation.
- Record reproducible evidence, failure signatures, safe adaptations, and
  affected callers or artifacts.
- State scope, expiry or review conditions, and the owner of follow-up.
- Promote only repeatedly verified reusable rules; keep raw trial-and-error in
  `.traces/`.

## Complete When

An independent contributor can tell what behavior is supported, reproduce the
relevant observation, apply the documented adaptation, and recognize when the
record no longer applies.
