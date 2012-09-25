"""Generic service queue object. Contains all instrumentation data necessary
for modeling with queuing theory.
"""
from __future__ import division
import numpy as np
import pandas
from boto.exception import EC2ResponseError

import logging
LOG = logging.getLogger('service_queue')

from leptoid.utils import fetch_yaml, get_instance_size

class ServiceQueue(object):
	"""
	Instantiated with various instrumented data (service time, transaction
	arrival rate, etc.), generates key queuing statistics automatically.
	"""

	def __init__(self, env, service, instance, service_time, arrival_rate):
		""" Constructor. All parameters must be pandas.TimeSeries. """

		if service_time.shape != arrival_rate.shape:
			raise Exception("Data must have the same shape.")

		if not isinstance(service_time, pandas.TimeSeries) or \
				not isinstance(arrival_rate, pandas.TimeSeries):
			raise Exception("Must instantiate with pandas.TimeSeries.")

		# Basic metrics.
		self.service_time = service_time
		self.arrival_rate = arrival_rate
		self.utilization = np.multiply(self.service_time, self.arrival_rate)
		self.residency_time = self.service_time / (
				1 - self.utilization * self.service_time)

		# Box information
		self.environment = env
		self.service = service
		self.instance_id = instance
		self.legacy = self.service[:4] != "kbs."
		self.add_instance_size()

	def add_util_forecast(self, util_forecast):
		"""
		Attaches utilization forecast, checks to make sure length is consistent.
		"""
		serieslen = fetch_yaml('leptoid/model_config.yml')['horizon']

		if serieslen != len(util_forecast):
			raise Exception(
					"Utilization forecast does not have correct length.")
		else:
			self.util_forecast = util_forecast

	def add_instance_size(self):
		""" Attach instance size to ServiceQueue object. Will raise a
		boto.EC2ConnectionError if the instance does not exist.
		"""
		LOG.info("\tRetrieving size for %s in %s" %
				(self.instance_id, self.environment))
		self.instance_size = get_instance_size(
				self.environment, self.instance_id)

	def get_first_timestamp(self):
		""" Returns timestamp for the first utilization value. """
		return self.utilization.index[0]

def generate_service_queues(arrival_rates, service_times):
	""" Method for converting nested dictionaries with Graphite time series
	into leptoid.ServiceQueues with host information (environment, utilization,
	instance id, etc. pre-populated.

	Parameters
	----------
	arrival_rates
		nested dict produced by leptoid.graphite.extract_time_series with
		data for target hosts
	service_times
		similar to arrival_rates
	
	Returns an iterable with leptoid.ServiceQueues for each host.
	"""
	service_queues = []

	# Extract service time and arrival rate for each service instance.
	for env in arrival_rates.keys():
		for service in arrival_rates[env].keys():
			for instance in arrival_rates[env][service].keys():
				try:
					arate = arrival_rates[env][service][instance]
					stime = service_times[env][service][instance]
					queue = ServiceQueue(env, service, instance, stime, arate)
					service_queues.append(queue)
				# Handle case where instance is not found in arrival rates or
				# service_times
				except KeyError, e:
					if instance in arrival_rates[env][service]:
						del arrival_rates[env][service][instance]
					else:
						raise KeyError(e)
				except EC2ResponseError, e:
					LOG.error(
							"\tInstance %s does not exist! Continuing..." %
							instance)
					LOG.error(e)
					continue

	return service_queues
