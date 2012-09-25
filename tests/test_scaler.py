""" Testing LeptoidScaler. """
from unittest import TestCase
from mock import Mock
import numpy as np
import datetime

import leptoid.scaler as scaler
from leptoid.namespaces import NAMESPACES

class TestLeptoidScaler(TestCase):

	def setUp(self):
		self.scaler = scaler.LeptoidScaler(NAMESPACES)

	def test_update_instances(self):
		""" Testing threshold checks. """

		# Mocking out scaler's scaling calls.
		scaler.deploy.upscale = Mock()
		scaler.deploy.downscale = Mock()
		queue = Mock(service='knewmena', instance_id='i-deadbeef')

		# Changing to shorter time horizons.
		self.scaler.upscale_time_horizon = 2
		self.scaler.downscale_time_horizon = 4

		# Upscale call. Mocking out deployment API call too.
		estimated_util = np.array([0.8] * 4)
		scaler.find_instance_ids = Mock()
		scaler.find_instance_ids.return_value = ('i-deadbeef')
		self.scaler.evaluate_instance(queue, estimated_util)
		scaler.deploy.upscale.assert_called_with(queue)

		# Downscale call.
		estimated_util = np.array([0.01] * 4)
		self.scaler.evaluate_instance(queue, estimated_util)
		scaler.deploy.downscale.assert_called_with(queue)

	def test_rollback_candidate_check(self):
		""" Testing scaler._find_rollback_candidates. """
		mocktime = Mock(time=datetime.datetime.now())
		old_mocktime = Mock(time=datetime.datetime(1900, 1, 1))
		self.scaler.recent_deploys = {
				('i-deadbeef', 'i-beefdead'): mocktime,
				('i-00000000'): old_mocktime}
		# Testing positive & negative searches.
		self.assertTrue(self.scaler._find_rollback_candidates(
			Mock(instance_id = 'i-deadbeef', environment='production')))
		self.assertFalse(self.scaler._find_rollback_candidates(
			Mock(instance_id = 'i-01234567', environment='production')))
		# Testing positive (but expired) rollback candidates.
		self.assertFalse(self.scaler._find_rollback_candidates(
			Mock(instance_id = 'i-00000000', environment='production')))
