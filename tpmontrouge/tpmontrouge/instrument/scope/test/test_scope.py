import unittest
import os
import tempfile

import matplotlib
matplotlib.use('Agg')
from matplotlib.pyplot import figure

from ..scope import Scope
from .simu_scope import ScopeSimulation


class GenericTest(object):
    scope = Scope(root=ScopeSimulation())
    def test_base(self):
        self.scope.autoset()
        self.assertEqual(self.scope._root._last_command.lower(), 'autoset')

    def test_channel_index(self):
        with self.assertRaises(IndexError) as context:
            self.scope.channel[6]

    def test_channel_active(self):
        self.scope.channel[1].state = True
        self.assertTrue(self.scope.channel[1].is_active())
        self.assertIn(1, [elm.key for elm in self.scope.list_of_active_channel])

    def test_channel_imp(self):
        self.scope.channel[1].impedance = 'FiftyOhm'
        self.assertEqual(str(self.scope.channel[1].impedance), 'FiftyOhm')
        self.assertEqual(str(self.scope.channel1.impedance), 'FiftyOhm')
    def test_channel_coup(self):
        self.scope.channel[1].coupling = 'AC'
        self.assertEqual(str(self.scope.channel[1].coupling), 'AC')
    def test_channel_offset(self):        
        self.scope.channel[2].offset = 0.1
        self.assertEqual(self.scope.channel[2].offset, 0.1)
    def test_channel_scale(self):                
        self.scope.channel[2].scale = 0.1
        self.assertEqual(self.scope.channel[2].scale, 0.1)

    def test_trigger(self):
        self.scope.trigger.source = 1
#        print(self.scope.trigger.source)
        self.assertEqual(self.scope.trigger.source, 1)


        self.scope.trigger.slope = 'positiveedge'
        self.assertEqual(self.scope.trigger.slope, 'PositiveEdge')

        self.scope.trigger.level = .1
        self.assertEqual(self.scope.trigger.level, .1)

    def test_horizontal(self):
        self.scope.horizontal.scale = 0.01
        self.assertEqual(self.scope.horizontal.scale, 0.01)


    def test_plot(self):
        # Should be moved to test_waveform
        fig = figure()
        waveform = self.scope.channel1.get_waveform()
        waveform.plot(fig=fig)
        file = os.path.join(tempfile.gettempdir(), 'scope_test.pdf')
#        print('Figure saved to ', file)
        fig.savefig(file)

class ScopeTest(GenericTest, unittest.TestCase):
    pass
