from opencensus.grpc import rpc_measure_constants
from opencensus.stats import bucket_boundaries, view
from opencensus.stats.aggregation import (
    CountAggregation,
    DistributionAggregation,
    SumAggregation,
)


"""
Defines constants for exporting views on rpc stats
"""


class RPCViewConstants:
    """
    Define variables used by constants below
    """
    # Buckets for distributions in default views
    # Common histogram bucket boundaries for bytes
    # received/sets Views (in bytes).
    rpc_bytes_bucket_boundaries = [0, 1024, 2048, 4096, 16384, 65536,
                                   262144, 4194304, 16777216, 67108864,
                                   268435456, 1073741824, 4294967296]

    # Common histogram bucket boundaries for latency and
    # elapsed-time Views (in milliseconds).
    rpc_millis_bucket_boundaries = [0.0, 0.01, 0.05, 0.1, 0.3, 0.6,
                                    0.8, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0,
                                    8.0, 10.0, 13.0, 16.0, 20.0, 25.0,
                                    30.0, 40.0, 50.0, 65.0, 80.0, 100.0,
                                    130.0, 160.0, 200.0, 250.0, 300.0,
                                    400.0, 500.0, 650.0, 800.0, 1000.0,
                                    2000.0, 5000.0, 10000.0, 20000.0,
                                    50000.0, 100000.0]

    # Common histogram bucket boundaries for request/response
    # count Views (no unit).
    rpc_count_bucket_boundaries = [0.0, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0,
                                   64.0, 128.0, 256.0, 512.0, 1024.0,
                                   2048.0, 4096.0, 8192.0, 16384.0,
                                   32768.0, 65536.0]

    # Record sum and count stats at the same time.
    count = CountAggregation()
    sum = SumAggregation()

    # Set up aggregation object for rpc_bytes_bucket_boundaries
    bytes_bucket_boundaries = bucket_boundaries.BucketBoundaries(
        rpc_bytes_bucket_boundaries)
    aggregation_with_bytes_histogram = DistributionAggregation(
        bytes_bucket_boundaries.boundaries)

    # Set up aggregation object for rpc_millis_bucket_boundaries
    millis_bucket_boundaries = bucket_boundaries.BucketBoundaries(
        rpc_millis_bucket_boundaries)
    aggregation_with_millis_histogram = DistributionAggregation(
        millis_bucket_boundaries.boundaries)

    # Set up aggregation object for rpc_count_bucket_boundaries
    count_bucket_boundaries = bucket_boundaries.BucketBoundaries(
        rpc_count_bucket_boundaries)
    aggregation_with_count_histogram = DistributionAggregation(
        count_bucket_boundaries.boundaries)

    # Initialize an instance of RPC Measure Constants
    rpc_m_c = rpc_measure_constants.RPCMeasureConstants()

    """
    RPC Client Cumulative Views
    """
    # Default Views
    # The following set of views are considered minimum
    #  required to monitor client-side performance
    grpc_client_sent_bytes_per_rpc_view = view.View(
        name="grpc.io/client/sent_bytes_per_rpc",
        description="Sent bytes per RPC",
        columns=[rpc_m_c.grpc_client_method],
        measure=rpc_m_c.grpc_client_sent_bytes_per_rpc,
        aggregation=aggregation_with_bytes_histogram)

    grpc_client_received_bytes_per_rpc_view = view.View(
        name="grpc.io/client/received_bytes_per_rpc",
        description="Received bytes per RPC",
        columns=[rpc_m_c.grpc_client_method],
        measure=rpc_m_c.grpc_client_received_bytes_per_rpc,
        aggregation=aggregation_with_bytes_histogram)

    grpc_client_roundtrip_latency_view = view.View(
        name="grpc.io/client/roundtrip_latency",
        description="Latency in msecs",
        columns=[rpc_m_c.grpc_client_method],
        measure=rpc_m_c.grpc_client_roundtrip_latency,
        aggregation=aggregation_with_millis_histogram)

    grpc_client_completed_rpc_view = view.View(
        name="grpc.io/client/completed_rpcs",
        description="Number of completed client RPCs",
        columns=[rpc_m_c.grpc_client_method, rpc_m_c.grpc_client_status],
        measure=rpc_m_c.grpc_client_roundtrip_latency,
        aggregation=count)

    grpc_client_started_rpc_view = view.View(
        name="grpc.io/client/started_rpcs",
        description="Number of started client RPCs",
        columns=[rpc_m_c.grpc_client_method],
        measure=rpc_m_c.grpc_client_started_rpcs,
        aggregation=count)

    # Extra Views
    # The following set of views are considered useful
    #  but not mandatory to monitor client side performance
    grpc_client_sent_messages_per_rpc_view = view.View(
        name="grpc.io/client/sent_messages_per_rpc",
        description="Number of messages sent in the RPC",
        columns=[rpc_m_c.grpc_client_method],
        measure=rpc_m_c.grpc_client_sent_messages_per_rpc,
        aggregation=aggregation_with_count_histogram)

    grpc_client_received_messages_per_rpc_view = view.View(
        name="grpc.io/client/received_messages_per_rpc",
        description="Number of response messages received per RPC",
        columns=[rpc_m_c.grpc_client_method],
        measure=rpc_m_c.grpc_client_received_messages_per_rpc,
        aggregation=aggregation_with_count_histogram)

    grpc_client_server_latency_view = view.View(
        name="grpc.io/client/server_latency",
        description="Server latency in msecs",
        columns=[rpc_m_c.grpc_client_method],
        measure=rpc_m_c.grpc_client_server_latency,
        aggregation=aggregation_with_millis_histogram)

    grpc_client_sent_messages_per_method_view = view.View(
        name="grpc.io/client/sent_messages_per_method",
        description="Number of messages sent",
        columns=[rpc_m_c.grpc_client_method],
        measure=rpc_m_c.grpc_client_sent_messages_per_method,
        aggregation=count)

    grpc_client_received_messages_per_method_view = view.View(
        name="grpc.io/client/received_messages_per_method",
        description="Number of messages received",
        columns=[rpc_m_c.grpc_client_method],
        measure=rpc_m_c.grpc_client_received_messages_per_method,
        aggregation=count)
    grpc_client_sent_bytes_per_method_view = view.View(
        name="grpc.io/client/sent_bytes_per_method",
        description="Sent bytes per method",
        columns=[rpc_m_c.grpc_client_method],
        measure=rpc_m_c.grpc_client_sent_bytes_per_method,
        aggregation=sum)

    grpc_client_received_bytes_per_method_view = view.View(
        name="grpc.io/client/received_bytes_per_method",
        description="Received bytes per method",
        columns=[rpc_m_c.grpc_client_method],
        measure=rpc_m_c.grpc_client_received_bytes_per_method,
        aggregation=sum)

    """
    RPC Server Cumulative Views
    """
    # Default Views
    # The following set of views are considered minimum
    #  required to monitor server-side performance
    grpc_server_received_bytes_per_rpc = view.View(
        name="grpc.io/server/received_bytes_per_rpc",
        description="Received bytes per RPC",
        columns=[rpc_m_c.grpc_server_method],
        measure=rpc_m_c.grpc_server_received_bytes_per_rpc,
        aggregation=sum)

    grpc_server_sent_bytes_per_rpc = view.View(
        name="grpc.io/server/sent_bytes_per_rpc",
        description="Sent bytes per RPC",
        columns=[rpc_m_c.grpc_server_method],
        measure=rpc_m_c.grpc_server_sent_bytes_per_method,
        aggregation=sum)

    grpc_server_server_latency = view.View(
        name="grpc.io/server/server_latency",
        description="Latency in msecs",
        columns=[rpc_m_c.grpc_server_method],
        measure=rpc_m_c.grpc_server_server_latency,
        aggregation=aggregation_with_millis_histogram)

    grpc_server_completed_rpcs = view.View(
        name="grpc.io/server/completed_rpcs",
        description="Number of completed server RPCs",
        columns=[rpc_m_c.grpc_server_method, rpc_m_c.grpc_server_status],
        measure=rpc_m_c.grpc_server_server_latency,
        aggregation=count)

    grpc_server_started_rpcs = view.View(
        name="grpc.io/server/started_rpcs",
        description="Number of started server RPCs",
        columns=[rpc_m_c.grpc_server_method],
        measure=rpc_m_c.grpc_server_started_rpcs,
        aggregation=count)

    # Extra Views
    # The following set of views are considered useful
    #  but not mandatory to monitor server-side performance
    grpc_server_received_messages_per_rpc = view.View(
        name="grpc.io/server/received_messages_per_rpc",
        description="Number of response messages received in each RPC",
        columns=[rpc_m_c.grpc_server_method],
        measure=rpc_m_c.grpc_server_received_messages_per_rpc,
        aggregation=aggregation_with_count_histogram)

    grpc_server_sent_messages_per_rpc = view.View(
        name="grpc.io/server/sent_messages_per_rpc",
        description="Number of messages sent in each RPC",
        columns=[rpc_m_c.grpc_server_method],
        measure=rpc_m_c.grpc_server_sent_messages_per_rpc,
        aggregation=aggregation_with_count_histogram)

    grpc_server_sent_messages_per_method = view.View(
        name="grpc.io/server/sent_messages_per_method",
        description="Number of messages sent",
        columns=[rpc_m_c.grpc_server_method],
        measure=rpc_m_c.grpc_server_sent_messages_per_method,
        aggregation=count)

    grpc_server_received_messages_per_method = view.View(
        name="grpc.io/server/received_messages_per_method",
        description="Number of messages received",
        columns=[rpc_m_c.grpc_server_method],
        measure=rpc_m_c.grpc_server_received_messages_per_method,
        aggregation=count)

    grpc_server_sent_bytes_per_method = view.View(
        name="grpc.io/server/sent_bytes_per_method",
        description="Sent bytes per method",
        columns=[rpc_m_c.grpc_server_method],
        measure=rpc_m_c.grpc_server_sent_bytes_per_method,
        aggregation=sum)

    grpc_server_received_bytes_per_method = view.View(
        name="grpc.io/server/received_bytes_per_method",
        description="Received bytes per method",
        columns=[rpc_m_c.grpc_server_method],
        measure=rpc_m_c.grpc_server_received_bytes_per_method,
        aggregation=sum)
