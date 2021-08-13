# Changelog

## Unreleased

- Enable AAD authorization via TokenCredential
([#1021](https://github.com/census-instrumentation/opencensus-python/pull/1021))
- Implement attach rate metrics via Stastbeat
([#1053](https://github.com/census-instrumentation/opencensus-python/pull/1053))
- Implement network metrics via Statsbeat - Success count
([#1059](https://github.com/census-instrumentation/opencensus-python/pull/1059))
- Implement network metrics via Statsbeat - Others
([#1062](https://github.com/census-instrumentation/opencensus-python/pull/1062))
- Implement feature metrics via Statsbeat
([#1063](https://github.com/census-instrumentation/opencensus-python/pull/1063))

## 1.0.8
Released 2021-05-13

- Fix `logger.exception` with no exception info throwing error
([#1006](https://github.com/census-instrumentation/opencensus-python/pull/1006))
- Add `enable_local_storage` to turn on/off local storage + retry + flushing logic
([#1016](https://github.com/census-instrumentation/opencensus-python/pull/1016))

## 1.0.7
Released 2021-01-25

- Hotfix
([#1004](https://github.com/census-instrumentation/opencensus-python/pull/1004))

## 1.0.6
Released 2021-01-14

- Disable heartbeat metrics in exporters
  ([#984](https://github.com/census-instrumentation/opencensus-python/pull/984))
- Loosen instrumentation key validation to GUID
  ([#986](https://github.com/census-instrumentation/opencensus-python/pull/986))

## 1.0.5
Released 2020-10-13

- Attach rate metrics via Heartbeat for Web and Function apps
  ([#930](https://github.com/census-instrumentation/opencensus-python/pull/930))
- Attach rate metrics for VM
  ([#935](https://github.com/census-instrumentation/opencensus-python/pull/935))
- Add links in properties for trace exporter envelopes
  ([#936](https://github.com/census-instrumentation/opencensus-python/pull/936))
- Fix attach rate metrics for VM to only ping data service on retry
  ([#946](https://github.com/census-instrumentation/opencensus-python/pull/946))
- Added queue capacity configuration for exporters
  ([#949](https://github.com/census-instrumentation/opencensus-python/pull/949))

## 1.0.4
Released 2020-06-29

- Remove dependency rate from standard metrics
  ([#903](https://github.com/census-instrumentation/opencensus-python/pull/903))
- Implement customEvents using AzureEventHandler
  ([#925](https://github.com/census-instrumentation/opencensus-python/pull/925))

## 1.0.3
Released 2020-06-17

- Change default path of local storage
  ([#903](https://github.com/census-instrumentation/opencensus-python/pull/903))
- Add support to initialize azure exporters with proxies
  ([#902](https://github.com/census-instrumentation/opencensus-python/pull/902))

## 1.0.2
Released 2020-02-04

- Add local storage and retry logic for Azure Metrics Exporter
  ([#845](https://github.com/census-instrumentation/opencensus-python/pull/845))
- Add Fixed-rate sampling logic for Azure Log Exporter
  ([#848](https://github.com/census-instrumentation/opencensus-python/pull/848))
- Implement TelemetryProcessors for Azure exporters
  ([#851](https://github.com/census-instrumentation/opencensus-python/pull/851))

## 1.0.1
Released 2019-11-26

- Validate instrumentation key in Azure Exporters
  ([#789](https://github.com/census-instrumentation/opencensus-python/pull/789))
- Add optional custom properties to logging messages
  ([#822](https://github.com/census-instrumentation/opencensus-python/pull/822))

## 1.0.0
Released 2019-09-30

- Standard Metrics - Incoming requests execution time
  ([#773](https://github.com/census-instrumentation/opencensus-python/pull/773))
- Implement connection strings
  ([#767](https://github.com/census-instrumentation/opencensus-python/pull/767))

## 0.7.1
Released 2019-08-26

- Standard metrics incoming requests per second
  ([#758](https://github.com/census-instrumentation/opencensus-python/pull/758))

## 0.7.0
Released 2019-07-31

- Added standard metrics
  ([#708](https://github.com/census-instrumentation/opencensus-python/pull/708),
   [#718](https://github.com/census-instrumentation/opencensus-python/pull/718),
   [#720](https://github.com/census-instrumentation/opencensus-python/pull/720),
   [#722](https://github.com/census-instrumentation/opencensus-python/pull/722),
   [#724](https://github.com/census-instrumentation/opencensus-python/pull/724))
- Supported server performance breakdown by operation name
  ([#735](https://github.com/census-instrumentation/opencensus-python/pull/735))

## 0.3.1
Released 2019-06-30

- Added metrics exporter
  ([#678](https://github.com/census-instrumentation/opencensus-python/pull/678))

## 0.2.1
Released 2019-06-13

- Support span attributes
  ([#682](https://github.com/census-instrumentation/opencensus-python/pull/682))

## 0.2.0
Released 2019-05-31

- Added log exporter
  ([#657](https://github.com/census-instrumentation/opencensus-python/pull/657),
  [#668](https://github.com/census-instrumentation/opencensus-python/pull/668))
- Added persistent storage support
  ([#640](https://github.com/census-instrumentation/opencensus-python/pull/640))
- Changed AzureExporter constructor signature to use kwargs
  ([#632](https://github.com/census-instrumentation/opencensus-python/pull/632))

## 0.1.0
Released 2019-04-24

- Initial release
