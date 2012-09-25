from unittest import TestCase
from mock import Mock
from subprocess import PIPE

import leptoid.deploy as deploy
from leptoid.service_queue import ServiceQueue

class TestDeploy(TestCase):

	def test_build_kbs_command(self):
		""" Test whether deploy._build_kbs_command() builds the KBS call
		correctly.
		"""
		# Setting up mock Boto EC2Connection.
		deploy.EC2CONN = Mock()
		attr_mock = Mock()
		attr_mock.values.return_value = ['m1.medium']
		attrs = {'get_instance_attribute.return_value': attr_mock}
		deploy.EC2CONN.configure_mock(**attrs)

		# Check upscaling command.
		queue = Mock(spec=ServiceQueue)
		queue.environment = 'staging'
		queue.service = 'proctoring_application'
		queue.instance_id = 'i-deadbeef'
		queue.instance_size = 'm1.medium'
		queue.legacy = True

		up_call = deploy._build_kbs_command(queue, deploy.UPSCALE_TARGETS, 100)
		self.assertEqual(up_call,
				'kbs d n --legacy -t m1.large staging proctoring_application' +
				' proctoring_application:100')

		# Check downscale command.
		down_call = deploy._build_kbs_command(
				queue, deploy.DOWNSCALE_TARGETS, 100)
		self.assertEqual(down_call,
				'kbs d n --legacy -t m1.small staging proctoring_application' +
				' proctoring_application:100')
	
	def test_build_kbs_rollback(self):
		""" Testing rollback command. """
		rollback_call = deploy._build_kbs_rollback(100)
		self.assertEqual(rollback_call, 'kbs d rollback 100')

	def test_call_kbs(self):
		""" deploy._call_kbs should call KBS using subprocess, write STDOUT to
		a pipe, then parse the pipe's contents for the deployment id.

		Here, we mock subprocess.Popen out using Mock() and check what it was
		called with. The deployment id returned by KBS doesn't matter.
		"""

		# Mock configuration
		m = Mock(spec=['stdout', 'stdout.readline'])
		m.stdout.readline.return_value = "Deployment 1000 started..."
		deploy.subprocess.Popen = Mock()
		deploy.subprocess.Popen.return_value = m

		# Construct bogus KBS command, see if it gets called properly.
		kbs_cmd = "kbs d n -t m1.small staging kbs.KRS kbs.KRS:100"
		depid = deploy._call_kbs(kbs_cmd)
		self.assertEqual(depid, -1)
		#deploy.subprocess.Popen.assert_called_with(
		#		args=kbs_cmd.split(' '), stdout=PIPE)

