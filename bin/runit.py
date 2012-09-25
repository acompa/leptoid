""" Temporary run script for Leptoid.

TODO: How should this run script REALLY look?
"""

from time import sleep
import logging
logging.basicConfig(
		filename='/var/leptoid/log/leptoid.log', level=logging.INFO,
		format="%(asctime)s %(levelname)s:%(name)s %(message)s")
LOG = logging.getLogger('runit')

import sys
sys.path.insert(0, "")

from leptoid.targets import TARGETS
from leptoid.scaler import LeptoidScaler
import leptoid.forecasting as forecasting

scaler = LeptoidScaler(TARGETS)

while True:
	LOG.info("\n*****\nBeginning scaling evaluation pass...\n*****")
	# Query Graphite for utilization data.
	service_queues = scaler.query_graphite_targets()

	for queue in service_queues:
		# Generate utilization forecasts for every queue in the scaler.
		insample_forecast, util_estimate = forecasting.forecast(queue)

		# Scale instances up or down with KBS, based on the utilization forecast.
		# Skip instances with insufficient sample data.
		if (insample_forecast, util_estimate) != (None, None):
			scaler.evaluate_instance(queue, util_estimate)
	LOG.info(
			"\n*****\nCompleted scaling evaluation pass. Sleeping...\n*****")
	sleep(60)

