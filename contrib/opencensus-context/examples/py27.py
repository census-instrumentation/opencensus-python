from opencensus.common.runtime_context import RuntimeContext

RuntimeContext.register_slot('correlation_context', lambda: {})

def hello(name):
    correlation_context = RuntimeContext.correlation_context.copy()
    correlation_context['name'] = name
    RuntimeContext.correlation_context = correlation_context

    print(RuntimeContext)

if __name__ == '__main__':
    print(RuntimeContext)
    RuntimeContext.correlation_context['test'] = True
    print(RuntimeContext)
    hello('hello')
    RuntimeContext.clear()
    print(RuntimeContext)
