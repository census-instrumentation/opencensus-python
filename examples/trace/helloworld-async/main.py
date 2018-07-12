# This is just here for me to test

from sanic import Sanic
from sanic.response import json
from opencensus.trace.exporters import jaeger_exporter
from opencensus.trace.ext.aiohttp.trace import trace_integration as aiohttp_integration
from opencensus.trace.ext.aioredis.trace import trace_integration as aioredis_integration
from opencensus.trace.ext.sanic.sanic_middleware import SanicMiddleware
from opencensus.trace.propagation import jaeger_format
from opencensus.trace.samplers import probability
from opencensus.trace import asyncio_context

import asyncio
import aiotask_context as context
import aiohttp
import aioredis


loop = asyncio.get_event_loop()
loop.set_task_factory(context.task_factory)

sampler = probability.ProbabilitySampler(rate=0.5)
propagator = jaeger_format.JaegerFormatPropagator()
exporter = jaeger_exporter.JaegerExporter(service_name="recs")

# These uses the tracer from the async context
aiohttp_integration(propagator=propagator)
aioredis_integration()


app = Sanic()
middleware = SanicMiddleware(
                app,
                sampler=sampler,
                exporter=exporter,
                propagator=propagator)


@app.route('/')
async def root(req):
    tracer = asyncio_context.get_opencensus_tracer()
    with tracer.span(name='span1'):
        with tracer.span(name='span2'):
            async with aiohttp.ClientSession() as session:
                async with session.get("https://slashdot.org") as response:
                    print(response)
                    conn = await aioredis.create_connection(
                               'redis://localhost', loop=loop)
                    await conn.execute('set', 'foo', 'value')
                    val = await conn.get('foo')
                    print(val)
                    conn.close()
                    await conn.wait_closed()
                    return json({"hello": "world"})


def main():
    server = app.create_server(host='0.0.0.0', port=8080)
    loop = asyncio.get_event_loop()
    loop.set_task_factory(context.task_factory)
    asyncio.ensure_future(server)
    try:
        loop.run_forever()
    except SanicException as err:
        print(err)
        loop.stop()


if __name__ == '__main__':
    main()
