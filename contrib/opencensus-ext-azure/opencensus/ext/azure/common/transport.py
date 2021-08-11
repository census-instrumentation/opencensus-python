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
import threading

import requests
from azure.core.exceptions import ClientAuthenticationError
from azure.identity._exceptions import CredentialUnavailableError

logger = logging.getLogger(__name__)
_MONITOR_OAUTH_SCOPE = "https://monitor.azure.com//.default"
_requests_lock = threading.Lock()
_requests_map = {}


class TransportMixin(object):
    def _check_stats_collection(self):
        return self.options.enable_stats_metrics and \
            (not hasattr(self, '_is_stats') or not self._is_stats)

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
        try:
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json; charset=utf-8',
            }
            endpoint = self.options.endpoint
            if self.options.credential:
                token = self.options.credential.get_token(_MONITOR_OAUTH_SCOPE)
                headers["Authorization"] = "Bearer {}".format(token.token)
                # Use new api for aad scenario
                endpoint += '/v2.1/track'
            else:
                endpoint += '/v2/track'
            response = requests.post(
                url=endpoint,
                data=json.dumps(envelopes),
                headers=headers,
                timeout=self.options.timeout,
                proxies=json.loads(self.options.proxies),
            )
        except requests.Timeout:
            logger.warning(
                'Request time out. Ingestion may be backed up. Retrying.')
            return self.options.minimum_retry_interval
        except requests.RequestException as ex:
            logger.warning(
                'Retrying due to transient client side error %s.', ex)
            # client side error (retryable)
            return self.options.minimum_retry_interval
        except CredentialUnavailableError as ex:
            logger.warning('Credential error. %s. Dropping telemetry.', ex)
            return -1
        except ClientAuthenticationError as ex:
            logger.warning('Authentication error %s', ex)
            return self.options.minimum_retry_interval
        except Exception as ex:
            logger.warning(
                'Error when sending request %s. Dropping telemetry.', ex)
            # Extraneous error (non-retryable)
            return -1

        text = 'N/A'
        data = None
        try:
            text = response.text
        except Exception as ex:
            logger.warning('Error while reading response body %s.', ex)
        else:
            try:
                data = json.loads(text)
            except Exception:
                pass
        if response.status_code == 200:
            if self._check_stats_collection():
                with _requests_lock:
                    _requests_map['success'] = _requests_map.get('success', 0) + 1  # noqa: E501
            return 0
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
                        self.storage.put(resend_envelopes)
                except Exception as ex:
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
            logger.warning(
                'Transient server side error %s: %s.',
                response.status_code,
                text,
            )
            # server side error (retryable)
            return self.options.minimum_retry_interval
        # Authentication error
        if response.status_code == 401:
            logger.warning(
                'Authentication error %s: %s.',
                response.status_code,
                text,
            )
            return self.options.minimum_retry_interval
        # Forbidden error
        # Can occur when v2 endpoint is used while AI resource is configured
        # with disableLocalAuth
        if response.status_code == 403:
            logger.warning(
                'Forbidden error %s: %s.',
                response.status_code,
                text,
            )
            return self.options.minimum_retry_interval
        logger.error(
            'Non-retryable server side error %s: %s.',
            response.status_code,
            text,
        )
        # server side error (non-retryable)
        return -response.status_code
