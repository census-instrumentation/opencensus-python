from opencensus.common.runtime_context import RuntimeContext

RuntimeContext.register_slot('current_span', None)

class Span(object):
    def __init__(self, name):
        self.name = name
        self.parent = RuntimeContext.current_span

    def __repr__(self):
        return ('{}({})'.format(type(self).__name__, self.name))

    def __enter__(self):
        RuntimeContext.current_span = self

    def __exit__(self, type, value, traceback):
        RuntimeContext.current_span = self.parent

if __name__ == '__main__':
    print(RuntimeContext)
    with Span('foo'):
        print(RuntimeContext)
        with Span('bar'):
            print(RuntimeContext)
        print(RuntimeContext)
    print(RuntimeContext)
