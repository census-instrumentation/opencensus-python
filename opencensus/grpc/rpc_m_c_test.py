import unittest
from opencensus.grpc import rpc_measure_constants


class RPCMCTest(unittest.TestCase):
    """
    RPCMTest tests the rpc_measure_constants module
    """

    def setUp(self):
        """
        sets up a test rpc_measure_constant instance
        """
        self.rpc_measure = rpc_measure_constants.RPCMeasureConstants()

    def test_client_measures(self):
        """
        tests the client measures
        """
        self.assertEqual(self.rpc_measure.grpc_client_sent_messages_per_rpc.unit,
                         "1",
                         "grpc_client_sent_messages_per_rpc not set correctly on init")
        self.assertEqual(self.rpc_measure.grpc_client_sent_bytes_per_rpc.description,
                         "Total bytes sent across all request messages per RPC",
                         "grpc_client_sent_bytes_per_rpc not set correctly on init")
        self.assertEqual(self.rpc_measure.grpc_client_received_messages_per_rpc.name,
                         "grpc.io/client/received_messages_per_rpc",
                         "grpc_client_received_messages_per_rpc not set correctly on init")
        self.assertEqual(self.rpc_measure.grpc_client_received_bytes_per_rpc.unit,
                         "by",
                         "grpc_client_received_bytes_per_rpc not set correctly upon init")
        self.assertEqual(self.rpc_measure.grpc_client_roundtrip_latency.name,
                         "grpc.io/client/roundtrip_latency",
                         "grpc_client_roundtrip_latency not initialized correctly")
        self.assertEqual(self.rpc_measure.grpc_client_server_latency.name,
                         "grpc.io/client/server_latency",
                         "grpc_client_server_latency not set properly")
        self.assertEqual(self.rpc_measure.grpc_client_started_rpcs.description,
                         "Number of started client RPCs.",
                         "grpc_client_started_rpcs not set properly")
        self.assertEqual(self.rpc_measure.grpc_client_sent_messages_per_method.unit,
                         "1",
                         "grpc_client_sent_messages_per_method not set properly")
        self.assertEqual(self.rpc_measure.grpc_client_received_messages_per_method.name,
                         "grpc.io/client/received_messages_per_method",
                         "grpc_client_received_messages_per_method not set properly")
        self.assertEqual(self.rpc_measure.grpc_client_sent_bytes_per_method.description,
                         "Total bytes sent per method, recorded real-time as bytes are sent.",
                         "grpc_client_sent_bytes_per_method not set properly")
        self.assertEqual(self.rpc_measure.grpc_client_received_bytes_per_method.unit,
                         "by",
                         "grpc_client_received_bytes_per_method not set properly")

    def test_server_measures(self):
        """
        tests the server measures
        """
        self.assertEqual(
            self.rpc_measure.grpc_server_received_messages_per_rpc.name,
            "grpc.io/server/received_messages_per_rpc",
            "grpc_server_received_messages_per_rpc not set properly")

        self.assertEqual(
            self.rpc_measure.grpc_server_received_bytes_per_rpc.description,
            "Total bytes received across all messages per RPC",
            "grpc_server_received_bytes_per_rpc not set properly")

        self.assertEqual(
            self.rpc_measure.grpc_server_sent_messages_per_rpc.unit,
            "1",
            "grpc_server_sent_messages_per_rpc not set properly")

        self.assertEqual(
            self.rpc_measure.grpc_server_sent_bytes_per_rpc.name,
            "grpc.io/server/sent_bytes_per_rpc",
            "grpc_server_sent_bytes_per_rpc not set properly")

        self.assertEqual(
            self.rpc_measure.grpc_server_server_latency.description,
            "Time between first byte of request received to"
            " last byte of response sent or terminal error.",
            "grpc_server_server_latency not set properly")

        self.assertEqual(
            self.rpc_measure.grpc_server_started_rpcs.unit,
            "1",
            "grpc_server_started_rpcs not set correctly")

        self.assertEqual(
            self.rpc_measure.grpc_server_sent_messages_per_method.name,
            "grpc.io/server/sent_messages_per_method",
            "grpc_server_sent_messages_per_method not set correctly")

        self.assertEqual(
            self.rpc_measure.grpc_server_received_messages_per_method.
            description,
            "Total messages received per method.",
            "grpc_server_received_messages_per_method not set correctly")

        self.assertEqual(
            self.rpc_measure.grpc_server_sent_bytes_per_method.unit,
            "by",
            "grpc_server_sent_bytes_per_method not set correctly")

        self.assertEqual(
            self.rpc_measure.grpc_server_received_bytes_per_method.name,
            "grpc.io/server/received_bytes_per_method",
            "grpc_server_received_bytes_per_method not set correctly")


if __name__ == '__main__':
    unittest.main()
