# import unittest

# import mock

# from opencensus.ext.datadog.transport import DDTransport


# class TestTraces(unittest.TestCase):
#     def setUp(self):
#         pass

#     @mock.patch('requests.post', return_value=None)
#     def test_send_traces(self, mr_mock):
#         transport = DDTransport('test')
#         transport.send_traces({})
# # 