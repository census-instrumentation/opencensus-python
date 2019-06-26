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
import requests

from opencensus.trace import execution_context

logger = logging.getLogger(__name__)

class ResponseType(object):
    SUCCESS = 0
    RETRY = 1
    NON_RETRY = 2


class TransportMixin(object):
    def _transmit_from_storage(self):
        for blob in self.storage.gets():
            # give a few more seconds for blob lease operation
            # to reduce the chance of race (for perf consideration)
            if blob.lease(self.options.timeout + 5):
                envelopes = blob.get()  # TODO: handle error
                result = self._transmit(envelopes)
                if result == ResponseType.RETRY:
                    blob.lease(result)
                else:
                    blob.delete(silent=True)

    def _transmit(self, envelopes):
        """
        Transmit the data envelopes to the ingestion service.
        Returns a ResponsePayload with a type, status code and message.
        Type is a ResponseType with either success,
        retry or non-retryable failure
        This function should never throw exception.
        """
        # TODO: prevent requests being tracked
        blacklist_hostnames = execution_context.get_opencensus_attr(
            'blacklist_hostnames',
        )
        execution_context.set_opencensus_attr(
            'blacklist_hostnames',
            ['dc.services.visualstudio.com'],
        )
        try:
            response = requests.post(
                url=self.options.endpoint,
                data=json.dumps(envelopes),
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json; charset=utf-8',
                },
                timeout=self.options.timeout,
            )
        except Exception as ex:  # TODO: consider RequestException
            logger.warning('Transient client side error %s.', ex)
            # client side error (retryable)
            return ResponseType.RETRY
        finally:
            execution_context.set_opencensus_attr(
                'blacklist_hostnames',
                blacklist_hostnames,
            )
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
            logger.info('Transmission succeeded: %s.', text)
            return ResponseType.SUCCESS
        if response.status_code == 206:  # Partial Content
            # TODO: store the unsent data
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
                return ResponseType.NON_RETRY
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
            return ResponseType.RETRY
        logger.error(
            'Non-retryable server side error %s: %s.',
            response.status_code,
            text,
        )
        # server side error (non-retryable)
        return ResponseType.NON_RETRY
