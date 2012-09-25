""" Unit test for checking API calls. """

from unittest import TestCase
import leptoid.deploy_api as depapi

class TestDeploymentAPICalls(TestCase):

	def setUp(self):
		pass

	def test_extract_ids(self):
		""" Extract server instance ids from a dict. """
		server_info = [
				{'aws_instance_id': 'i-deadbeef'}, 
				{'aws_instance_id': 'i-0abacabb'}]
		
		ids = depapi.extract_ids(server_info)
		self.assertEqual(ids, ['i-deadbeef', 'i-0abacabb'])
		self.assertTrue(isinstance(ids, list))

	def test_match_deploy_id(self):
		""" Check for deployment id matches. """
		reservation = {'build_id': 100}
		self.assertTrue(depapi.match_deploy_id(100, reservation))
		self.assertFalse(depapi.match_deploy_id(999, reservation))
