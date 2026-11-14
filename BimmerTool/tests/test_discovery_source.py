import unittest
from unittest.mock import patch
from bimmertool import transport,hsfz,doip
from bimmertool.simulator import Simulator


class DiscoverySource(unittest.TestCase):
    def test_bound_source_finds_local_simulator_over_each_protocol(self):
        for model, module in [('f',hsfz),('ix',doip)]:
            with self.subTest(model=model):
                sim=Simulator(model=model,port=0,discovery_port=0).start()
                try:
                    cars=module.discover('127.0.0.1',port=sim.discovery_port,timeout=.3,source_ip='127.0.0.1')
                    self.assertEqual(len(cars),1)
                finally:sim.stop()

    def test_one_protocol_error_does_not_hide_other_result(self):
        with patch.object(hsfz,'discover',side_effect=OSError('network route')),patch.object(doip,'discover',return_value=[{'ip':'169.254.1.2'}]) as discover:
            cars=transport.discover_all(source_ip='169.254.1.1')
        self.assertEqual(cars[0]['ip'],'169.254.1.2')
        self.assertEqual(discover.call_args.kwargs['source_ip'],'169.254.1.1')

    def test_bind_failure_is_not_reported_as_empty_success(self):
        with patch.object(hsfz,'discover',side_effect=OSError('cannot bind')),patch.object(doip,'discover',return_value=[]):
            with self.assertRaisesRegex(hsfz.HsfzError,'cannot bind'):
                transport.discover_all(source_ip='169.254.1.1')

    def test_invalid_source_never_opens_socket(self):
        with patch.object(hsfz,'discover') as discover:
            with self.assertRaises(ValueError):transport.discover_all(source_ip='not-ip')
        discover.assert_not_called()
