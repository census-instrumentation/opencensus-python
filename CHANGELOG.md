# Changelog

## Unreleased

- Fix gRPC client tracer reuse bug
  ([#539](https://github.com/census-instrumentation/opencensus-python/pull/539))
- Fix bugs in Prometheus exporter. Use ordered list for histogram buckets.
  Use `UnknownMetricFamily` for `SumData` instead of `UntypedMetricFamily`.
  Check if label keys and values match before exporting.
- Remove min and max from Distribution.
- Replace stackdriver `gke_container` resources, see the [GKE migration
  notes](https://cloud.google.com/monitoring/kubernetes-engine/migration#incompatible)
  for details
- Componentize the package distribution. All [contrib
  packages](https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/)
  are now decoupled from the core library, and can be released separately.

## 0.2.0
Released 2019-01-18

- Fix multiple stackdriver and prometheus exporter bugs
- Increase size of trace batches and change transport behavior on exit
  ([#452](https://github.com/census-instrumentation/opencensus-python/pull/452))

## 0.1.11
Released 2019-01-16

- Fix a bug in the stackdriver exporter that caused spans to be exported
  individually
  ([#425](https://github.com/census-instrumentation/opencensus-python/pull/425))
- Add this changelog
