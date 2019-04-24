# Changelog

## Unreleased

## 0.5.0
Released 2019-04-24

- Add cumulative API
  ([#626](https://github.com/census-instrumentation/opencensus-python/pull/626))

## 0.4.1
Released 2019-04-11

 - Allow for metrics with empty label keys and values
  ([#611](https://github.com/census-instrumentation/opencensus-python/pull/611),
  [#614](https://github.com/census-instrumentation/opencensus-python/pull/614))

## 0.4.0
Released 2019-04-08

- Multiple bugfixes
- Use separate context package instead of threadlocals for execution context
  ([#573](https://github.com/census-instrumentation/opencensus-python/pull/573))

## 0.3.0
Released 2019-03-11

- Fix gRPC client tracer reuse bug
  ([#539](https://github.com/census-instrumentation/opencensus-python/pull/539))
- Update prometheus client and fix multiple bugs in the exporter
  ([#492](https://github.com/census-instrumentation/opencensus-python/pull/492))
- Remove min and max from `Distribution`
  ([#501](https://github.com/census-instrumentation/opencensus-python/pull/501))
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
