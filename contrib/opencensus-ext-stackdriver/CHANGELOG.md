# Changelog

## Unreleased

## 0.2.0
Released 2019-04-05

- Update for package changes in core library
- Export metrics periodically from background thread instead of at record time
- Create metric descriptors lazily instead of on view registration
- Change return type of `new_stats_exporter` to include exporter task
  ([#593](https://github.com/census-instrumentation/opencensus-python/pull/593))

## 0.1.0
Released 2019-03-19

- Initial version
