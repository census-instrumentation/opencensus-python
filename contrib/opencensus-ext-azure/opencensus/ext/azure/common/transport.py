# Copyright 2019, OpenCensus Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
import os
import threading
import time

import requests
from azure.core.exceptions import ClientAuthenticationError
from azure.identity._exceptions import CredentialUnavailableError

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


logger = logging.getLogger(__name__)

_MAX_CONSECUTIVE_REDIRECTS = 10
_MONITOR_OAUTH_SCOPE = "https://monitor.azure.com//.default"
_requests_lock = threading.Lock()
_requests_map = {}


class TransportMixin(object):

    def _check_stats_collection(self):
        return not os.environ.get("APPLICATIONINSIGHTS_STATSBEAT_DISABLED_ALL") and (not hasattr(self, '_is_stats') or not self._is_stats)  # noqa: E501

    def _is_stats_exporter(self):
        return hasattr(self, '_is_stats') and self._is_stats

    def _transmit_from_storage(self):
        if self.storage:
            for blob in self.storage.gets():
                # give a few more seconds for blob lease operation
                # to reduce the chance of race (for perf consideration)
                if blob.lease(self.options.timeout + 5):
                    envelopes = blob.get()
                    result = self._transmit(envelopes)
                    if result > 0:
                        blob.lease(result)
                    else:
                        blob.delete()

    def _transmit(self, envelopes):
        """
        Transmit the data envelopes to the ingestion service.
        Return a negative value for partial success or non-retryable failure.
        Return 0 if all envelopes have been successfully ingested.
        Return the next retry time in seconds for retryable failure.
        This function should never throw exception.
        """
        if not envelopes:
            return 0
        exception = None
        try:
            start_time = time.time()
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json; charset=utf-8',
            }
            endpoint = self.options.endpoint
            if self.options.credential:
                token = self.options.credential.get_token(_MONITOR_OAUTH_SCOPE)
                headers["Authorization"] = "Bearer {}".format(token.token)
            endpoint += '/v2.1/track'
            if self._check_stats_collection():
                with _requests_lock:
                    _requests_map['count'] = _requests_map.get('count', 0) + 1  # noqa: E501
            response = requests.post(
                url=endpoint,
                data=json.dumps(envelopes),
                headers=headers,
                timeout=self.options.timeout,
                proxies=json.loads(self.options.proxies),
                allow_redirects=False,
            )
        except requests.Timeout:
            if not self._is_stats_exporter():
                logger.warning(
                    'Request time out. Ingestion may be backed up. Retrying.')
            exception = self.options.minimum_retry_interval
        except requests.RequestException as ex:
            if not self._is_stats_exporter():
                logger.warning(
                    'Retrying due to transient client side error %s.', ex)
            # client side error (retryable)
            exception = self.options.minimum_retry_interval
        except CredentialUnavailableError as ex:
            if not self._is_stats_exporter():
                logger.warning('Credential error. %s. Dropping telemetry.', ex)
            exception = -1
        except ClientAuthenticationError as ex:
            if not self._is_stats_exporter():
                logger.warning('Authentication error %s', ex)
            exception = self.options.minimum_retry_interval
        except Exception as ex:
            if not self._is_stats_exporter():
                logger.warning(
                    'Error when sending request %s. Dropping telemetry.', ex)
            # Extraneous error (non-retryable)
            exception = -1
        finally:
            end_time = time.time()
            if self._check_stats_collection():
                with _requests_lock:
                    duration = _requests_map.get('duration', 0)
                    _requests_map['duration'] = duration + (end_time - start_time)  # noqa: E501
            if exception is not None:
                if self._check_stats_collection():
                    with _requests_lock:
                        if exception >= 0:
                            _requests_map['retry'] = _requests_map.get('retry', 0) + 1  # noqa: E501
                        else:
                            _requests_map['exception'] = _requests_map.get('exception', 0) + 1  # noqa: E501

                return exception

        text = 'N/A'
        data = None
        try:
            text = response.text
        except Exception as ex:
            if not self._is_stats_exporter():
                logger.warning('Error while reading response body %s.', ex)
        else:
            try:
                data = json.loads(text)
            except Exception:
                pass
        if response.status_code == 200:
            self._consecutive_redirects = 0
            if self._check_stats_collection():
                with _requests_lock:
                    _requests_map['success'] = _requests_map.get('success', 0) + 1  # noqa: E501
            return 0
        # Status code not 200, 439 or 402 counts as failures
        if self._check_stats_collection():
            if response.status_code != 439 and response.status_code != 402:
                with _requests_lock:
                    _requests_map['failure'] = _requests_map.get('failure', 0) + 1  # noqa: E501
        if response.status_code == 206:  # Partial Content
            if data:
                try:
                    resend_envelopes = []
                    for error in data['errors']:
                        if error['statusCode'] in (
                                429,  # Too Many Requests
                                500,  # Internal Server Error
                                503,  # Service Unavailable
                        ):
                            resend_envelopes.append(envelopes[error['index']])
                        else:
                            logger.error(
                                'Data drop %s: %s %s.',
                                error['statusCode'],
                                error['message'],
                                envelopes[error['index']],
                            )
                    if resend_envelopes:
                        if self._check_stats_collection():
                            with _requests_lock:
                                _requests_map['retry'] = _requests_map.get('retry', 0) + 1  # noqa: E501
                        self.storage.put(resend_envelopes)
                except Exception as ex:
                    if not self._is_stats_exporter():
                        logger.error(
                            'Error while processing %s: %s %s.',
                            response.status_code,
                            text,
                            ex,
                        )
                return -response.status_code
            # cannot parse response body, fallback to retry
        if response.status_code in (
                206,  # Partial Content
                429,  # Too Many Requests
                500,  # Internal Server Error
                503,  # Service Unavailable
        ):
            if not self._is_stats_exporter():
                logger.warning(
                    'Transient server side error %s: %s.',
                    response.status_code,
                    text,
                )
            # server side error (retryable)
            if self._check_stats_collection():
                with _requests_lock:
                    _requests_map['retry'] = _requests_map.get('retry', 0) + 1  # noqa: E501
            return self.options.minimum_retry_interval
        # Authentication error
        if response.status_code == 401:
            if not self._is_stats_exporter():
                logger.warning(
                    'Authentication error %s: %s.',
                    response.status_code,
                    text,
                )
            if self._check_stats_collection():
                with _requests_lock:
                    _requests_map['retry'] = _requests_map.get('retry', 0) + 1  # noqa: E501
            return self.options.minimum_retry_interval
        # Forbidden error
        # Can occur when v2 endpoint is used while AI resource is configured
        # with disableLocalAuth
        if response.status_code == 403:
            if not self._is_stats_exporter():
                logger.warning(
                    'Forbidden error %s: %s.',
                    response.status_code,
                    text,
                )
            if self._check_stats_collection():
                with _requests_lock:
                    _requests_map['retry'] = _requests_map.get('retry', 0) + 1  # noqa: E501
            return self.options.minimum_retry_interval
        # Redirect
        if response.status_code in (307, 308):
            self._consecutive_redirects += 1
            if self._consecutive_redirects < _MAX_CONSECUTIVE_REDIRECTS:
                if response.headers:
                    location = response.headers.get("location")
                    if location:
                        url = urlparse(location)
                        if url.scheme and url.netloc:
                            # Change the host to the new redirected host
                            self.options.endpoint = "{}://{}".format(url.scheme, url.netloc)  # noqa: E501
                            # Attempt to export again
                            return self._transmit(envelopes)
                if not self._is_stats_exporter():
                    logger.error(
                        "Error parsing redirect information."
                    )
            else:
                if not self._is_stats_exporter():
                    logger.error(
                        "Error sending telemetry because of circular redirects."  # noqa: E501
                        " Please check the integrity of your connection string."  # noqa: E501
                    )
            # If redirect but did not return, exception occured
            if self._check_stats_collection():
                with _requests_lock:
                    _requests_map['exception'] = _requests_map.get('exception', 0) + 1  # noqa: E501
        # Other, server side error (non-retryable)
        if not self._is_stats_exporter():
            logger.error(
                'Non-retryable server side error %s: %s.',
                response.status_code,
                text,
            )
        if self._check_stats_collection():
            if response.status_code == 402 or response.status_code == 439:
                # 402: Monthly Quota Exceeded (new SDK)
                # 439: Monthly Quota Exceeded (old SDK) <- Currently OC SDK
                with _requests_lock:
                    _requests_map['throttle'] = _requests_map.get('throttle', 0) + 1  # noqa: E501
        return -response.status_code
