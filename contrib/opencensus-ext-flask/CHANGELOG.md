# Changelog

## in development

- Don't use full URL with query parameters for the span name and span HTTP_URL
  span attribute.

  Query params can contain sensitive values which shouldn't be logged. Now just
  the url without the query parameters is used.

  Before: ``http://example.com/path/bar?foo=bar&bar=baz``, now:
  ``http://example.com/path/bar``.

## Unreleased
- Make ProbabilitySampler default

## 0.3.0
Released 2019-04-24

- Decoupled exporter specific logic from configuration

## 0.2.0
Released 2019-04-08

- Update for package changes in core library

## 0.1.0
Released 2019-03-19

- Initial version
