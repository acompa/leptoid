"""
Module responsible for managing forecasts, retrieving Graphite data, and 
scaling instances.
"""

import numpy as np
import logging
import datetime

import leptoid.deploy as deploy
import leptoid.graphite as graphite
import leptoid.utils as utils
from leptoid.service_queue import generate_service_queues
from leptoid.deploy_api import find_instance_ids

LOG = logging.getLogger('scaler')

class LeptoidScaler(object):
	"""
	LeptoidScaler aggregates
	-- collections of instance names for scaling or reaping,
	-- parameters for scaling, including utilization limits
	into an object responsible for scaling and reaping instances.
	"""

	def __init__(self, metric_targets,
			scaling_config='leptoid/scaling_config.yml'):
		"""
		Reads configs from local YAML file. Posibility of consolidating these.
		"""
		# Scaling limits.
		config = utils.fetch_yaml(scaling_config)
		self.api_params = config['render_config']
		self.upscale_limits = config['upscale_limits']
		self.downscale_limits = config['downscale_limits']
		self.upscale_time_horizon = config['upscale_time_horizon']
		self.downscale_time_horizon = config['downscale_time_horizon']

		# Target namespaces
		self.targets = metric_targets 
		LOG.debug("Targets:")
		LOG.debug(self.targets)

		self.recent_deploys = dict()
		self.rollback_limit = {'production': 3600, 'staging': 600}

		# Configs for forecasting
		self.model_config = config['model_config']

	def query_graphite_targets(self):
		"""
		Queries arrival rate and service time data for all targets stored
		in self.targets (attached to LeptoidScaler) and extracts data from
		Graphite's response. 

		Returns: list of leptoid.ServiceQueues with utilization populated.
		"""

		# Retrieve arrival rates and service times from Graphite.
		raw_rates = graphite.call_graphite(self.targets['arrival_rates'],
				self.api_params)
		raw_times = graphite.call_graphite(self.targets['service_times'],
				self.api_params)
		arrival_rates = graphite.extract_time_series(raw_rates)
		service_times = graphite.extract_time_series(raw_times)

		return generate_service_queues(arrival_rates, service_times)

	def evaluate_instance(self, queue, estimated_util):
		"""
		Scales instance up or down depending on its utilization forecast. We
		check the forecast against that service's threshold parameters, and
		upscale or downscale if necesary.

		Parameters
		----------
		queue
			leptoid.ServiceQueue object with queue details
		estimated_util
			forecasted utilization from leptoid.forecasting

		Returns nothing, but calls KBS based on utilization estimates.
		"""

		upscale_limit = self.upscale_limits[queue.service]
		downscale_limit = self.downscale_limits[queue.service]
		max_upscale_value = np.max(estimated_util[:self.upscale_time_horizon])
		max_downscale_value = np.max(
				estimated_util[:self.downscale_time_horizon])

		# Track the deployment id of any scaling events.
		# TODO: automate build id selection proces
		if max_upscale_value > upscale_limit:
			self.upscale_instance(queue)
		elif max_downscale_value < downscale_limit:
			self.downscale_instance(queue)
		else:
			LOG.info("No action taken for %s:%s" %
					(queue.service, queue.instance_id))

	def upscale_instance(self, queue):
		""" Increases the size of the instance associated with queue. Steps:
		(1)		log
		(2)		check whether instance was recently deployed
		(3)		if so, deploy.rollback; if not, call deploy.upscale

		Parameters
		----------
		queue
			leptoid.ServiceQueue object with instance information.
		"""

		upscale_limit = self.upscale_limits[queue.service]
		LOG.info("Utilization for %s:%s exceeds %0.2f" %
				(queue.service, queue.instance_id, upscale_limit))

		# Rollback logic. We want to roll back any instances that were recently
		# downscaled and ran into utilization problems.
		rollback_details = self._find_rollback_candidates(queue)
		if rollback_details:
			deploy.rollback(queue, rollback_details.build_id)
		else:
			deploy_id = deploy.upscale(queue)
			instances = find_instance_ids(deploy_id)
			self.recent_deploys[instances] = utils.RollbackDetails(
					time=datetime.datetime.now(), build_id=deploy_id)
	
	def downscale_instance(self, queue):
		""" Decreases the size of the instance associated with queue.

		Parameters
		----------
		queue
			leptoid.ServiceQueue object with instance information.
		"""

		downscale_limit = self.downscale_limits[queue.service]
		LOG.info("Utilization for %s:%s never exceeds %0.2f" %
				(queue.service, queue.instance_id, downscale_limit))
		_ = deploy.downscale(queue)

	def _find_rollback_candidates(self, queue):
		""" Traverse recent deployments and find instances that can be rolled
		back.

		Returns the rollback details of any instance candidate if a match is
		found; otherwise returns None.
		"""
		matching_ids = self._find_matching_ids(queue)

		# If we find matching ids, check that deployment's time. Otherwise
		# return an empty list.
		if matching_ids:
			ids = matching_ids[0]
			details = self.recent_deploys[ids]
			horizon = datetime.timedelta(
					seconds=self.rollback_limit[queue.environment])
			if details.time + horizon < datetime.datetime.now(): 
				details = None			# return null if the horizon has passed
				del self.recent_deploys[ids]	# delete expired rollbacks
		else:
			details = matching_ids

		return details

	def _find_matching_ids(self, queue):
		""" Identifies all instances launched as part of a deployment id. """
		return [tuple(id_list)
				for id_list in self.recent_deploys.keys() for iid in id_list 
				if iid == queue.instance_id]
