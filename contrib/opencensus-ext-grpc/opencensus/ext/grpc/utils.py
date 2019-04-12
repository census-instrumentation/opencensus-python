from datetime import datetime

from grpc.framework.foundation import future
from grpc.framework.interfaces.face import face
from opencensus.trace import execution_context
from opencensus.trace import time_event


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


class WrappedResponseIterator(future.Future, face.Call):
    """Wraps the rpc response iterator.

    The grpc.StreamStreamClientInterceptor abstract class states stream
    interceptor method should return an object that's both a call (implementing
    the response iterator) and a future.  Thus, this class is a thin wrapper
    around the rpc response to provide the opencensus extension.

    :type iterator: (future.Future, face.Call)
    :param iterator: rpc response iterator

    :type span: opencensus.trace.Span
    :param span: rpc span
    """
    def __init__(self, iterator, span):
        self._iterator = iterator
        self._span = span

        self._messages_received = 0

    def add_done_callback(self, fn):
        self._iterator.add_done_callback(lambda ignored_callback: fn(self))

    def __iter__(self):
        return self

    def __next__(self):
        try:
            message = next(self._iterator)
        except StopIteration:
            execution_context.get_opencensus_tracer().end_span()
            raise

        self._messages_received += 1
        add_message_event(
            proto_message=message,
            span=self._span,
            message_event_type=time_event.Type.RECEIVED,
            message_id=self._messages_received)
        return message

    def next(self):
        return self.__next__()

    def cancel(self):
        return self._iterator.cancel()

    def is_active(self):
        return self._iterator.is_active()

    def cancelled(self):
        raise NotImplementedError()  # pragma: NO COVER

    def running(self):
        raise NotImplementedError()  # pragma: NO COVER

    def done(self):
        raise NotImplementedError()  # pragma: NO COVER

    def result(self, timeout=None):
        raise NotImplementedError()  # pragma: NO COVER

    def exception(self, timeout=None):
        raise NotImplementedError()  # pragma: NO COVER

    def traceback(self, timeout=None):
        raise NotImplementedError()  # pragma: NO COVER

    def initial_metadata(self):
        raise NotImplementedError()  # pragma: NO COVER

    def terminal_metadata(self):
        raise NotImplementedError()  # pragma: NO COVER

    def code(self):
        raise NotImplementedError()  # pragma: NO COVER

    def details(self):
        raise NotImplementedError()  # pragma: NO COVER

    def time_remaining(self):
        raise NotImplementedError()  # pragma: NO COVER

    def add_abortion_callback(self, abortion_callback):
        raise NotImplementedError()  # pragma: NO COVER

    def protocol_context(self):
        raise NotImplementedError()  # pragma: NO COVER
