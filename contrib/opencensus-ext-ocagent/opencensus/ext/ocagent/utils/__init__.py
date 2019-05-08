import datetime
import os
import socket

from google.protobuf.internal.well_known_types import ParseError
from google.protobuf.timestamp_pb2 import Timestamp
from opencensus.common.version import __version__ as opencensus_version
from opencensus.proto.agent.common.v1 import common_pb2

# Default agent endpoint
DEFAULT_ENDPOINT = 'localhost:55678'

# OCAgent exporter version
EXPORTER_VERSION = '0.0.1'


def get_node(service_name, host_name):
    """Generates Node message from params and system information.
    """
    return common_pb2.Node(
        identifier=common_pb2.ProcessIdentifier(
            host_name=socket.gethostname() if host_name is None
            else host_name,
            pid=os.getpid(),
            start_timestamp=proto_ts_from_datetime(
                datetime.datetime.utcnow())),
        library_info=common_pb2.LibraryInfo(
            language=common_pb2.LibraryInfo.Language.Value('PYTHON'),
            exporter_version=EXPORTER_VERSION,
            core_library_version=opencensus_version),
        service_info=common_pb2.ServiceInfo(name=service_name))


def proto_ts_from_datetime(dt):
    """Converts datetime to protobuf timestamp.

    :type dt: datetime
    :param dt: date and time

    :rtype: :class:`~google.protobuf.timestamp_pb2.Timestamp`
    :returns: protobuf timestamp
    """

    ts = Timestamp()
    if (dt is not None):
        ts.FromDatetime(dt)
    return ts


def proto_ts_from_datetime_str(dt):
    """Converts string datetime in ISO format to protobuf timestamp.
    :type dt: str
    :param dt: string with datetime in ISO format
    :rtype: :class:`~google.protobuf.timestamp_pb2.Timestamp`
    :returns: protobuf timestamp
    """

    ts = Timestamp()
    if (dt is not None):
        try:
            ts.FromJsonString(dt)
        except ParseError:
            pass
    return ts
