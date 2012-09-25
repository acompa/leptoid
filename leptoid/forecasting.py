"""
Leptoid interface to R for forecasting. Notes on rpy2:
	
(1)		rpy2 maintains a namespace of vars--look for notes on its current
		state
(2)		R's forecast library lets one specify error, seasonality, and trend
		type from {none, additive, multiplicative}
(3)		for starters, specify additive trend, multiplicative seasonality

Uses R's forecast package to generate forecasts. See the paper for more details:
	http://www.jstatsoft.org/v27/i03/paper
"""

import datetime
import numpy as np
import logging
LOG = logging.getLogger('forecasting')

# Importing rpy2 and working with Numpy objects.
import rpy2.robjects as robjects
import rpy2.robjects.numpy2ri
rpy2.robjects.numpy2ri.activate()

# Importing plotting functions from R.
RBMP = robjects.r['bitmap']
RPLOT = robjects.r['plot']
RDEVOFF = robjects.r['dev.off']

# Importing packages from R.
from rpy2.robjects.packages import importr
forecast = importr('forecast')
graphics = importr('graphics')

from leptoid.utils import get_forecast_attribute

RECENT_DATA_WINDOW = 120
PLOT_DIRECTORY = '/var/leptoid/img/'
PLOT_SIGNIFICANCE_THRESHOLD = 1E-5

def add_new_series(nseries, seriesname='nseries'):
	"""Adds time series to R's global environment as ts object. """
	freq = len(nseries)
	robjects.globalenv['raw_vector'] = nseries
	robjects.r('%s <- ts(raw_vector, frequency=%i)' % (seriesname, freq))

def _forecast_utilization(series, model_config=None):
	"""
	Generate a forecast using R functions.
	
	Parameters
	----------
	series
		np.array containing sample data
	model_config
		dict with values for 'model_type' and 'horizon'
	
	Returns an R object with these attributes:
	model: a list with model information,
	mean: forecasted values for nseries,
	level: confidence values for prediction,
	x: the original values in nseries,
	upper: upper limit for confidence interval
	lower: lower limit  "     " "        " "
	fitted: fitted values (aka one-step ahead forecasts)
	method: forecasting method used (as str)
	residuals: errors from fitted models (ie. x - fitted)

	Returns None if no sample data is available for the last
	${recent_data_window} observations in the sample.
	"""

	# Defining default settings.
	if model_config is None:
		model_type = "ZZZ"
		horizon = int(0.1 * len(series))
	else:
		model_type = model_config['model_type']
		horizon = model_config['horizon']

	# Handling case where recent samples are missing or not available.
	if (series[-1 * RECENT_DATA_WINDOW:] == 0).all():
		forecast_output = None
	else:
		etsout = forecast.ets(series, model=model_type)
		forecast_output = forecast.forecast(etsout, h=horizon)

	return forecast_output

def forecast(queue):
	"""
	Forecasting values using R's forecast package. Series reporting empty data
	over the last ${recent_data_window} minutes will return None.

	Parameters
	----------
	queue
		pandas.TimeSeries with utilization data. Data is extracted from the
		underlying buffer using np.frombuffer.
	service, instance_id
		information for instance, used when plotting

	TODO: Currently Leptoid uses R via rpy2. This will change since rpy2 is
	poorly maintained.
	"""

	LOG.info("Generating forecast for %s:%s" %
			(queue.service, queue.instance_id))

	# Retrieving forecast from rpy2, then extracting the attributes
	# (forecasted utilization, one-step ahead forecast) we want.
	model_output = _forecast_utilization(np.frombuffer(queue.utilization.data))

	# Handling case where output == None, indicating a dormant instance.
	if model_output == None:
		in_sample_forecast = None
		util_estimate = None
	else:
		in_sample_forecast = get_forecast_attribute(model_output, "fitted")
		util_estimate = get_forecast_attribute(model_output, "mean")

		# Let's avoid empty plots
		if np.max(util_estimate) > PLOT_SIGNIFICANCE_THRESHOLD:
			plot_forecast(model_output, queue)

	return (in_sample_forecast, util_estimate)

def plot_forecast(model_output, queue):
	"""
	Plots output from R forecast. Uses R functions extracted via rpy2
	(see global vars above).

	Parameters
	----------
	model_output
		R object returned by leptoid.forecasting._forecast_utilization(). Contains
		forecast information (confidence intervals, etc.).
	queue
		leptoid.ServiceQueue with information about the service
	
	Returns nothing, but saves a plot to disk with a timestamp.
	"""
	forecast_method = get_forecast_attribute(model_output, attr='method')
	n = datetime.datetime.now()

	RBMP('%s%s-%s-%i-%i-%i-%i:%i.jpg' %
			(PLOT_DIRECTORY, queue.service, queue.instance_id, n.year,
				n.month, n.day, n.hour, n.minute),
			width=1400, height=800, units='px', type='jpeg')
	RPLOT(model_output, main="Util forecast for %s:%s (using %s)" %
			(queue.service, queue.instance_id, forecast_method),
			xlab="Minutes elapsed since %s" % queue.get_first_timestamp())
	RDEVOFF()

