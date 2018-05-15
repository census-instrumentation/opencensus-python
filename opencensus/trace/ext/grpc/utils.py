from datetime import datetime

from opencensus.trace import time_event
from opencensus.trace import execution_context


def add_message_event(proto_message, span, message_event_type, message_id=1):
    """Adds a MessageEvent to the span based off of the given protobuf
    message
    """
    span.add_time_event(
        time_event=time_event.TimeEvent(
            datetime.utcnow(),
            message_event=time_event.MessageEvent(
                message_id,
                type=message_event_type,
                uncompressed_size_bytes=proto_message.ByteSize()
            )
        )
    )


def wrap_iter_with_message_events(
    request_or_response_iter,
    span,
    message_event_type
):
    """Wraps a request or response iterator to add message events to the span
    for each proto message sent or received
    """
    for message_id, message in enumerate(request_or_response_iter, start=1):
        add_message_event(
            proto_message=message,
            span=span,
            message_event_type=message_event_type,
            message_id=message_id
        )
        yield message


def wrap_iter_with_end_span(response_iter):
    """Wraps an iterator to end the current span on completion"""
    for response in response_iter:
        yield response
    execution_context.get_opencensus_tracer().end_span()
