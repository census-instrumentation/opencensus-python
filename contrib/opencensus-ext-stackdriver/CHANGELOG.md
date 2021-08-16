# Changelog

## Unreleased

- Drop python <3.6 in opencensus-ext-stackdriver
  [#1056](https://github.com/census-instrumentation/opencensus-python/pull/1056)

## 0.7.4
Released 2020-10-14

- Change default transporter in stackdriver exporter
([#929](https://github.com/census-instrumentation/opencensus-python/pull/929))

## 0.7.3
Released 2020-06-29

- Add mean property for distribution values
([#919](https://github.com/census-instrumentation/opencensus-python/pull/919))

## 0.7.2
Released 2019-08-26

- Delete SD integ test metric descriptors
([#770](https://github.com/census-instrumentation/opencensus-python/pull/770))
- Updated `http.status_code` attribute to be an int.
([#755](https://github.com/census-instrumentation/opencensus-python/pull/755))

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
