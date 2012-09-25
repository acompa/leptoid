""" Unit testing interface with R. """

from mock import Mock, MagicMock
from unittest import TestCase
from pandas import TimeSeries, PeriodIndex
from time import ctime

import leptoid.forecasting as fore

class TestForecasting(TestCase):
	""" forecasting.py Test Case """

	def setUp(self):
		""" Building test case scaffolding. """
		fore.forecast = Mock()
		fore.graphics = Mock()
		self.config_file = Mock()
		seriesidx = PeriodIndex(start=ctime(10000), periods=10)
		self.tseries = TimeSeries(data=range(10), index=seriesidx)

	def test_forecast_utilization(self):
		""" Test whether forecast methods are called. """
		_ = fore._forecast_utilization(self.tseries)
		fore.forecast.ets.assert_called_with(self.tseries, model='ZZZ')

	def test_get_forecast_attr(self):
		""" Check whether attributes are retrieved properly. """
		self.assertRaises(Exception,
				fore.get_forecast_attribute, None, 'foo')
		self.assertRaises(Exception,
				fore.get_forecast_attribute, None, 'model', 'foo')

