""" Unit test for calls to Graphite's /render API. """

import leptoid.graphite as g
import leptoid.namespaces as ns
from leptoid.scaler import LeptoidScaler

from unittest import TestCase
from numpy import arange
from time import ctime
from pandas import TimeSeries

class TestGraphite(TestCase):
	""" Graphite Test Case """

	def setUp(self):
		self.scaler = LeptoidScaler(ns.NAMESPACES)

	def test_call_construction(self):
		""" Testing construction of Graphite calls. """
		call = g.build_graphite_call(
				self.scaler.targets['arrival_rates'], self.scaler.api_params)

		# Should have one 'target' option for each of the targets in the scaler
		self.assertTrue(
				call.count('target') ==
				len(self.scaler.targets['arrival_rates']))
		# Calls should also have format and start time options.
		self.assertTrue(call.find('format') > -1)
		self.assertTrue(call.find('from') > -1)
	
	def test_data_extraction(self):
		""" Using a Mock() to check whether data is extracted correctly. """
		fake_pickle = [{
			'start': 1000,
			'values': arange(10),
			'name': "Knewton.Staging.Webservice-KRS.i-deadbeef"}]
		namespace_data = g.extract_time_series(fake_pickle)
		tser = namespace_data['staging']['kbs.KRS']['i-deadbeef']
		# Data should be in a dict, with a pandas.TimeSeries containing
		# data.
		self.assertTrue(isinstance(namespace_data, dict))
		self.assertTrue(isinstance(tser, TimeSeries))
		self.assertTrue(len(tser) == 10)
