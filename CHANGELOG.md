# Changelog

## Unreleased

- Fix bugs in Prometheus exporter. Use ordered list for histogram buckets.
  Use `UnknownMetricFamily` for `SumData` instead of `UntypedMetricFamily`.
  Check if label keys and values match before exporting.
- Remove min and max from Distribution.
- Fix a bug that caused root spans from the same tracer to share a trace ID
  ([#505](https://github.com/census-instrumentation/opencensus-python/pull/505)

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
