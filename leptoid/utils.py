""" Various utility functions for Leptoid. """

import yaml
import numpy as np
from collections import namedtuple
from boto.ec2.connection import EC2Connection

import logging
LOG = logging.getLogger('utils')

from leptoid.namespaces import GRAPHITE_TO_KBS_MAP
from leptoid.settings import (AWS_ACCESS_KEY_ID_PROD,
		AWS_SECRET_ACCESS_KEY_PROD, AWS_ACCESS_KEY_ID_STAG,
		AWS_SECRET_ACCESS_KEY_STAG)

# Tuple for storing rollback information.
RollbackDetails = namedtuple('RollbackDetails', 'time build_id')

# Tuple for storing service names, SVN and/or Jenkins ids.
ServiceRevisionIds = namedtuple('ServiceRevisionIds', 'name date svn jenkins')

# Hash with EC2 connections for production & staging.
EC2CONN = {
		'production': EC2Connection(
			AWS_ACCESS_KEY_ID_PROD, AWS_SECRET_ACCESS_KEY_PROD),
		'staging': EC2Connection(
			AWS_ACCESS_KEY_ID_STAG, AWS_SECRET_ACCESS_KEY_STAG)}

def fetch_yaml(filename):
	""" Retrieve YAML contents. """

	with open(filename, 'r') as infile:
		payload = yaml.load(infile)
	return payload

def get_forecast_attribute(forecast_output, attr, model_attr=None):
	"""
	Returns a Numpy ndarray containing a forecast output attribute.

	Note that R model objects have their own attributes! Thus, users can also
	specify an optional model attribute.
	"""

	# Raising exceptions for invalid attributes or no target model attribute.
	valid_attrs = set(['model', 'mean', 'level', 'x', 'upper', 'lower',
		'fitted', 'method', 'residuals'])
	if attr not in valid_attrs:
		raise Exception("Invalid attribute from forecast.forecast() output.")
	elif attr == 'model' and model_attr is None:
		raise Exception("Must specify desired model attribute.")

	# Handling optional model attribute retrieval.
	if attr == 'model':
		attribute = get_forecast_model_attribute(
				forecast_output.rx2(attr), model_attr)
		LOG.debug("Extracted %s from rpy2 model object:" % model_attr)
	elif attr == 'method':
		attribute = forecast_output.rx2(attr)
		LOG.debug("Extracted %s from rpy2 object as string:" % attr)
	else:
		attribute = np.asarray(forecast_output.rx2(attr))
		LOG.debug("Extracted %s from rpy2 object:" % attr)

	LOG.debug(attribute)
	return attribute

def get_forecast_model_attribute(model, model_attr):
	"""
	Returns a Numpy ndarray containing a specific attribute from the model
	produced by R.
	"""

	valid_model_attrs = set(['states', 'par', 'fit', 'fitted', 'amse',
			'initstate', 'm', 'bic', 'aicc', 'loglik', 'residuals',
			'components', 'x', 'call', 'mse', 'method', 'aic',
			'sigma2'])
	if model_attr not in valid_model_attrs:
		raise Exception("Invalid model attribute for forecast.forecast()"+
				".model.")

	return np.asarray(model.rx2(model_attr))

def parse_namespace_contents(namespace):
	""" Extracts instance and service information from a Graphite namespace.
	Assumes all instances begin with 'i-'.

	Parameters
	----------
	namespace
		str for namespace of data stored in Graphite

	Returns: tuple with service name and instance name.
	"""

	contents = namespace.split('.')
	for item in contents:
		if item.find("Application") != -1 or item.find("Webservice") != -1:
			service = GRAPHITE_TO_KBS_MAP[item]
		elif item.find("i-") != -1:
			instance = item
		elif item == "Production" or item == "Staging" or item == "Utility":
			env = item.lower()

	try:
		LOG.debug("Identified instance %s for service %s" % (instance, service))
		return env, service, instance
	except NameError:
		LOG.error("Service or instance name not identified for %s" % namespace)
		raise Exception("Service or instance name not identified for %s" %
				namespace)

def get_instance_size(env, instance_id):
	""" Wrapper for Boto call to obtain instance information from $env.

	Parameters
	----------
	env
		string representing environment (staging or production)
	instance_id
		string

	Returns size of the instance, if it exists. Raises boto.EC2ConnectionError
	if instance does not exist in the environment.
	"""
	return EC2CONN[env].get_instance_attribute(
				instance_id, 'instanceType')['instanceType']
