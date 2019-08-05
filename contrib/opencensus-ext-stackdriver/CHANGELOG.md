# Changelog

## Unreleased

## 0.7.1
Released 2019-08-05

  - Support exporter changes in `opencensus>=0.7.0`

## 0.4.0
Released 2019-05-31

- Fix stackdriver k8s label keys
  ([#656](https://github.com/census-instrumentation/opencensus-python/pull/656))

## 0.3.0
Released 2019-04-24

- Multiple changes to stats exporter API

## 0.2.1
Released 2019-04-11
- Don't require exporter options, fall back to default GCP auth
  ([#610](https://github.com/census-instrumentation/opencensus-python/pull/610))

## 0.2.0
Released 2019-04-08

- Update for package changes in core library
- Export metrics periodically from background thread instead of at record time
- Create metric descriptors lazily instead of on view registration
- Change return type of `new_stats_exporter` to include exporter task
  ([#593](https://github.com/census-instrumentation/opencensus-python/pull/593))

## 0.1.0
Released 2019-03-19

- Initial version
