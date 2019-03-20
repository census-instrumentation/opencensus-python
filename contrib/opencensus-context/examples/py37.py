import asyncio

from opencensus.common.runtime_context import RuntimeContext

RuntimeContext.register_slot('correlation_context', lambda: dict())


async def hello(name):
    correlation_context = RuntimeContext.correlation_context.copy()
    correlation_context['name'] = name
    RuntimeContext.correlation_context = correlation_context

    for i in range(3):
        print('Hello {} {} {}'.format(
            name,
            i,
            RuntimeContext,
        ))
        await asyncio.sleep(0.1)


async def main():
    print(RuntimeContext)
    RuntimeContext.correlation_context['test'] = True
    print(RuntimeContext)
    await asyncio.gather(
        hello('foo'),
        hello('bar'),
        hello('baz'),
    )
    print(RuntimeContext)
    RuntimeContext.clear()
    print(RuntimeContext)


if __name__ == '__main__':
    asyncio.run(main())
