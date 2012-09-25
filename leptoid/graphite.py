""" Defining class responsible for retrieving data from Graphite. """

import pandas
import pickle

from time import ctime
from urllib2 import urlopen
from string import join
from collections import defaultdict

import logging
LOG = logging.getLogger('graphite')

from leptoid.utils import parse_namespace_contents

SERIES_WINDOW_SIZE = 5

def build_graphite_call(targets, api_params):
	""" Construct /render API call to Graphite. API params retrieved
	from YAML in a dict. Details on parameters at:
	http://graphite.readthedocs.org/en/0.9.10/render_api.html

	Parameters
	----------
	targets
		list of strs, queries for Graphite. Can accept either a single
		namespace or a list of namespaces.
	
	Returns: pickled object sent by Graphite with namespace data.
	"""

	# Convert single namespace to a list.
	if not isinstance(targets, list):
		targets = list(targets)
	target_list = ["&target=%s" % target for target in targets]
	LOG.log(logging.DEBUG, "Building Graphite /render API call.")
	call = "https://graphite.knewton.net/render/?"
	for config in api_params.iteritems():
		call += '&%s' % '='.join(config)
	call += join(target_list, "")

	return call

def call_graphite(targets, api_params):
	"""
	Construct /render API call and retrieves pickled response from Graphite.
	API params retrieved from YAML in as a dict. Details at:
	http://graphite.readthedocs.org/en/0.9.10/render_api.html

	Parameters
	----------
	targets
		list of strs, target namespaces for Graphite query
		Can accept either a single namespace or a list of namespaces.
	
	Returns: pickled object sent by Graphite with namespace data.
	"""
	call = build_graphite_call(targets, api_params)
	LOG.log(logging.INFO, "Calling Graphite with %s" % call)
	response = urlopen(call)
	return pickle.load(response)

def extract_time_series(graphite_data):
	"""
	Parses raw Graphite data into time series grouped by instance. All time
	series are moving averages, with window size defined above.

	Parameters
	----------
	graphite_data
		pickled obj returned from Graphite's /render API.

	Returns: dict with key=metric name, val=pandas.TimeSeries.
	"""

	namespace_data = dict([(env, defaultdict(dict))
			for env in 'production', 'staging'])
	for rawdata in graphite_data:

		# Must convert epoch seconds to datetime string.
		starttime = ctime(rawdata['start'])

		# seriesidx provides timestamps for pandas.TimeSeries
		seriesidx = pandas.PeriodIndex(
				start=starttime, periods=len(rawdata['values']))
		tser = pandas.TimeSeries(data=rawdata['values'], index=seriesidx)
		tser = pandas.rolling_mean(tser, SERIES_WINDOW_SIZE, SERIES_WINDOW_SIZE)
		tser = tser.fillna(0)		# handle all nans

		# Populate dict with pandas.TimeSeries for each service's instances.
		# Finding instance in metric name by identifying substring with 'i-'.
		env, service, instance_name = parse_namespace_contents(rawdata['name'])
		namespace_data[env][service][instance_name] = tser
	
	return namespace_data

