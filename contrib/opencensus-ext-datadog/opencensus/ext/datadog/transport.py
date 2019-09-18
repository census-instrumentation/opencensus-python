import platform
import requests


class DDTransport(object):
    """ DDTransport contains all the logic for sending Traces to Datadog

    :type trace_addr: str
    :param trace_addr: trace_addr specifies the host[:port] address of the
    Datadog Trace Agent.
    """
    def __init__(self, trace_addr):
        self._trace_addr = trace_addr

        self._headers = {
            "Datadog-Meta-Lang": "python",
            "Datadog-Meta-Lang-Interpreter": platform.platform(),
            # Following the example of the Golang version it is prefixed
            # OC for Opencensus.
            "Datadog-Meta-Tracer-Version": "OC/0.0.1",
            "Content-Type": "application/json",
        }

    @property
    def trace_addr(self):
        """ specifies the host[:port] address of the Datadog Trace Agent.
        """
        return self._trace_addr

    @property
    def headers(self):
        """ specifies the headers that will be attached to HTTP request sent to DD.
        """
        return self._headers

    def send_traces(self, trace):
        """ Sends traces to the Datadog Tracing Agent

        :type trace: dic
        :param trace: Trace dictionary
        """

        requests.post("http://" + self.trace_addr + "/v0.4/traces",
                      json=trace,
                      headers=self.headers)
