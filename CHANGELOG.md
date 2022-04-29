# Changelog


## Unreleased
- Allow specifying metrics (custom_measurements) for Azure custom events
([#1117](https://github.com/census-instrumentation/opencensus-python/pull/1117))

# 0.9.0
Released 2022-04-20
- Make sure handler.flush() doesn't deadlock. 
([#1112](https://github.com/census-instrumentation/opencensus-python/pull/1112))

# 0.8.0
Released 2021-10-05

- Added integration tracking functionality, includes `django`, `flask`, `http-lib`, `logging`, `mysql`, `postgresql`, `pymongo`, `pymysql`, `pyramid`, `requests`, `sqlalchemy` modules
([#1065](https://github.com/census-instrumentation/opencensus-python/pull/1065))
- Support Python 3.8, 3.9
([#1048](https://github.com/census-instrumentation/opencensus-python/pull/1048))

# 0.7.13
Released 2021-05-13

- Updated `azure`, `django`, `flask`, `requests` modules

# 0.7.12
Released 2021-01-14

- Updated `azure`, `django`, `flask`, `grpc`, `httplib`, `pyramid`, `requests` modules

# 0.7.11
Released 2020-10-13

- Updated `azure`, `stackdriver` modules

## 0.7.10
Released 2020-06-29

- Updated `azure` module
([#903](https://github.com/census-instrumentation/opencensus-python/pull/903),
 [#925](https://github.com/census-instrumentation/opencensus-python/pull/925))

- Updated `stackdriver` module
([#919](https://github.com/census-instrumentation/opencensus-python/pull/919))

## 0.7.9
Released 2020-06-17

- Hotfix for breaking change
  ([#915](https://github.com/census-instrumentation/opencensus-python/pull/915))

## 0.7.8
Released 2020-06-17

- Updated `azure` module
  ([#903](https://github.com/census-instrumentation/opencensus-python/pull/903),
   [#902](https://github.com/census-instrumentation/opencensus-python/pull/902))

## 0.7.7
Released 2020-02-03

- Updated `azure` module
([#837](https://github.com/census-instrumentation/opencensus-python/pull/837),
 [#845](https://github.com/census-instrumentation/opencensus-python/pull/845),
 [#848](https://github.com/census-instrumentation/opencensus-python/pull/848),
 [#851](https://github.com/census-instrumentation/opencensus-python/pull/851))

## 0.7.6
Released 2019-11-26

- Initial release for `datadog` module
  ([#793](https://github.com/census-instrumentation/opencensus-python/pull/793))
- Updated `azure` module
  ([#789](https://github.com/census-instrumentation/opencensus-python/pull/789),
   [#822](https://github.com/census-instrumentation/opencensus-python/pull/822))

## 0.7.5
Released 2019-10-01

- Updated `flask` module
  ([#781](https://github.com/census-instrumentation/opencensus-python/pull/781))

## 0.7.4
Released 2019-09-30

- Updated `azure` module
  ([#773](https://github.com/census-instrumentation/opencensus-python/pull/773),
   [#767](https://github.com/census-instrumentation/opencensus-python/pull/767))

- Updated `django` module
  ([#775](https://github.com/census-instrumentation/opencensus-python/pull/775))

## 0.7.3
Released 2019-08-26

- Added `http code` to `grpc code` status code mapping on `utils`
  ([#746](https://github.com/census-instrumentation/opencensus-python/pull/746))
- Updated `django`, `flask`, `httplib`, `requests` and `pyramid` modules
  ([#755](https://github.com/census-instrumentation/opencensus-python/pull/755))
- Updated `requests` module
  ([#771](https://github.com/census-instrumentation/opencensus-python/pull/771))

## 0.7.2
Released 2019-08-16

- Fix GCP resource loading for certain environments
  ([#761](https://github.com/census-instrumentation/opencensus-python/pull/761))

## 0.7.1
Released 2019-08-05

- Added `set_status` to `span`
  ([#738](https://github.com/census-instrumentation/opencensus-python/pull/738))
- Update released stackdriver exporter version

## 0.7.0
Released 2019-07-31

- Fix exporting int-valued stats with sum and lastvalue aggregations
  ([#696](https://github.com/census-instrumentation/opencensus-python/pull/696))
- Fix cloud format propagator to use decimal span_id encoding instead of hex
  ([#719](https://github.com/census-instrumentation/opencensus-python/pull/719))

## 0.6.0
Released 2019-05-31

- Refactored PeriodicTask
  ([#632](https://github.com/census-instrumentation/opencensus-python/pull/632))
- Make ProbabilitySampler default, change default sampling rate
- Pass span context to samplers, allow samplers to override parent sampling
  decision

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
