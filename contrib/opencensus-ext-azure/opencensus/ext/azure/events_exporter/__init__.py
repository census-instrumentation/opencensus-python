from opencensus.ext.azure.common import utils
from opencensus.ext.azure.common.protocol import Data, Envelope, Event
from opencensus.ext.azure.log_exporter import AzureLogHandler


class AzureEventHandler(AzureLogHandler):
    def __init__(self, **options):
        super(AzureEventHandler, self).__init__(**options)

    def log_record_to_envelope(self, record):
        envelope = Envelope(
            iKey=self.options.instrumentation_key,
            tags=dict(utils.azure_monitor_context),
            time=utils.timestamp_to_iso_str(record.created),
        )

        envelope.name = "Microsoft.ApplicationInsights.Event"
        data = Event(
            name=record.msg,
            properties=record.args,
            measurements=None,
        )
        envelope.data = Data(baseData=data, baseType='EventData')
        return envelope
