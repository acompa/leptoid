""" Unit test for service queue object. """

import numpy as np
from unittest import TestCase
from leptoid.service_queue import ServiceQueue
from numpy.testing import assert_equal

class TestServiceQueue(TestCase):

	def setUp(self):
		self.service_time = np.array([1, 2, 3])
		self.arrival_rate = np.array([5, 5, 5])
		self.service_queue = ServiceQueue(self.service_time, self.arrival_rate)

	def check_initial_metrics(self):
		""" Make sure utilization, residence time are computed correctly. """

		# utilization
		util = np.multiply(self.service_time, self.arrival_rate)
		assert_equal(util, self.service_queue.utilization)
		# residency_time
		rtime = self.service_time / (1 - util * self.service_time)
		assert_equal(rtime, self.service_queue.residency_time)
