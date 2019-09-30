# Changelog

## Unreleased

## 0.7.3
Released 2019-09-30

- Check that url_rule is not None before dereferencing property
  ([#781](https://github.com/census-instrumentation/opencensus-python/pull/781))

## 0.7.2
Released 2019-08-26

- Updated `http.status_code` attribute to be an int.
  ([#755](https://github.com/census-instrumentation/opencensus-python/pull/755))
- Fixes value for `http.route` in Flask middleware
  ([#759](https://github.com/census-instrumentation/opencensus-python/pull/759))

## 0.7.1
Released 2019-08-05

- Update for core library changes

## 0.7.0
Released 2019-07-31

- Make ProbabilitySampler default
- Updated span attributes to include some missing attributes listed
  [here](https://github.com/census-instrumentation/opencensus-specs/blob/master/trace/HTTP.md#attributes)
  ([#735](https://github.com/census-instrumentation/opencensus-python/pull/735))

## 0.3.0
Released 2019-04-24

- Decoupled exporter specific logic from configuration

## 0.2.0
Released 2019-04-08

- Update for package changes in core library

## 0.1.0
Released 2019-03-19

- Initial version
