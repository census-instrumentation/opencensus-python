from opencensus.stats.measure import MeasureFloat, MeasureInt
from opencensus.tags import tag_key

"""
Defines constants for collecting rpc stats
"""


class RPCMeasureConstants:
    """
    Define constants used to define Measures below
    see specs in documentation for opencensus-python
    """
    byte = "by"
    count = "1"
    millisecond = "ms"

    def __init__(self):
        """
        Define client and server tags
        """
        # Client Tags
        # gRPC server status code received,
        # e.g. OK, CANCELLED, DEADLINE_EXCEEDED
        self.grpc_client_status = tag_key.TagKey("grpc_client_status")

        # Full gRPC method name, including package, service and method,
        # e.g. google.bigtable.v2.Bigtable/CheckAndMutateRow
        self.grpc_client_method = tag_key.TagKey("grpc_client_method")

        # Server Tags
        # gRPC server status code returned,
        # e.g. OK, CANCELLED, DEADLINE_EXCEEDED
        self.grpc_server_status = tag_key.TagKey("grpc_server_status")

        # Full gRPC method name, including package, service and method,
        # e.g. com.exampleapi.v4.BookshelfService/Checkout
        self.grpc_server_method = tag_key.TagKey("grpc_server_method")

        """
        Client Measures
        """
        # Number of messages sent in the RPC
        # (always 1 for non-streaming RPCs)
        self.grpc_client_sent_messages_per_rpc = MeasureInt(
            name="grpc.io/client/sent_messages_per_rpc",
            description="Number of messages sent in the RPC",
            unit=self.count)

        # Total bytes sent across all request messages per RPC
        self.grpc_client_sent_bytes_per_rpc = MeasureFloat(
            name="grpc.io/client/sent_bytes_per_rpc",
            description="Total bytes sent across all"
                        " request messages per RPC",
            unit=self.byte)

        # Number of response messages received
        # per RPC (always 1 for non-streaming RPCs)
        self.grpc_client_received_messages_per_rpc = MeasureInt(
            name="grpc.io/client/received_messages_per_rpc",
            description="Number of response messages received per RPC",
            unit=self.count)

        # Total bytes received across all
        # response messages per RPC
        self.grpc_client_received_bytes_per_rpc = MeasureFloat(
            name="grpc.io/client/received_bytes_per_rpc",
            description="Total bytes received across all"
                        " response messages per RPC",
            unit=self.byte)

        # Time between first byte of request sent to last
        # byte of response received, or terminal error
        self.grpc_client_roundtrip_latency = MeasureFloat(
            name="grpc.io/client/roundtrip_latency",
            description="Time between first byte of request sent to"
                        " last byte of response received or terminal error.",
            unit=self.millisecond)

        # Propagated from the server and should
        # have the same value as "grpc.io/server/latency"
        self.grpc_client_server_latency = MeasureFloat(
            name="grpc.io/client/server_latency",
            description="Server latency in msecs",
            unit=self.millisecond)

        # The total number of client RPCs ever opened,
        # including those that have not completed
        self.grpc_client_started_rpcs = MeasureInt(
            name="grpc.io/client/started_rpcs",
            description="Number of started client RPCs.",
            unit=self.count)

        # Total messages sent per method
        self.grpc_client_sent_messages_per_method = MeasureInt(
            name="grpc.io/client/sent_messages_per_method",
            description="Total messages sent per method.",
            unit=self.count)

        # Total messages received per method
        self.grpc_client_received_messages_per_method = MeasureInt(
            name="grpc.io/client/received_messages_per_method",
            description="Total messages received per method.",
            unit=self.count)

        # Total bytes sent per method,
        # recorded real-time as bytes are sent
        self.grpc_client_sent_bytes_per_method = MeasureFloat(
            name="grpc.io/client/sent_bytes_per_method",
            description="Total bytes sent per method, recorded"
                        " real-time as bytes are sent.",
            unit=self.byte)

        # Total bytes received per method, recorded real-time
        # as bytes are received
        self.grpc_client_received_bytes_per_method = MeasureFloat(
            name="grpc.io/client/received_bytes_per_method",
            description="Total bytes received per method,"
                        " recorded real-time as bytes are received.",
            unit=self.byte)

        """
        Server Measures
        """
        # Number of messages received in each RPC.
        # Has value 1 for non-streaming RPCs
        self.grpc_server_received_messages_per_rpc = MeasureInt(
            name="grpc.io/server/received_messages_per_rpc",
            description="Number of messages received in each RPC",
            unit=self.count)

        # Total bytes received across all messages per RPC
        self.grpc_server_received_bytes_per_rpc = MeasureFloat(
            name="grpc.io/server/received_bytes_per_rpc",
            description="Total bytes received across all"
                        " messages per RPC",
            unit=self.byte)

        # Number of messages sent in each RPC.
        # Has value 1 for non-streaming RPCs
        self.grpc_server_sent_messages_per_rpc = MeasureInt(
            name="grpc.io/server/sent_messages_per_rpc",
            description="Number of messages sent in each RPC",
            unit=self.count)

        # Total bytes sent in across all response messages per RPC
        self.grpc_server_sent_bytes_per_rpc = MeasureFloat(
            name="grpc.io/server/sent_bytes_per_rpc",
            description="Total bytes sent across all response"
                        " messages per RPC",
            unit=self.byte)

        # Time between first byte of request received to last byte of
        # response sent, or terminal error
        self.grpc_server_server_latency = MeasureFloat(
            name="grpc.io/server/server_latency",
            description="Time between first byte of request received"
                        " to last byte of response sent or terminal error.",
            unit=self.millisecond)

        # The total number of server RPCs ever opened,
        # including those that have not completed
        self.grpc_server_started_rpcs = MeasureInt(
            name="grpc.io/server/started_rpcs",
            description="Number of started server RPCs.",
            unit=self.count)

        # Total messages sent per method
        self.grpc_server_sent_messages_per_method = MeasureInt(
            name="grpc.io/server/sent_messages_per_method",
            description="Total messages sent per method.",
            unit=self.count)

        # Total messages received per method
        self.grpc_server_received_messages_per_method = MeasureInt(
            name="grpc.io/server/received_messages_per_method",
            description="Total messages received per method.",
            unit=self.count)

        # Total bytes sent per method, recorded real-time as bytes are sent
        self.grpc_server_sent_bytes_per_method = MeasureFloat(
            name="grpc.io/server/sent_bytes_per_method",
            description="Total bytes sent per method, recorded"
                        " real-time as bytes are sent.",
            unit=self.byte)

        # Total bytes received per method, recorded real-time as
        # bytes are received
        self.grpc_server_received_bytes_per_method = MeasureFloat(
            name="grpc.io/server/received_bytes_per_method",
            description="Total bytes received per method, recorded"
                        " real-time as bytes are received.",
            unit=self.byte)
