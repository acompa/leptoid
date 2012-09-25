""" Functions wrapping Leptoid's upscaling/downscaling work. """

from re import findall

import subprocess
import logging
LOG = logging.getLogger('deploy')

from leptoid.deploy_api import find_latest_build
from leptoid.utils import fetch_yaml

# Mapping instance sizes to upscale and downscale targets.
UPSCALE_TARGETS = {
		'm1': {
			'small': 'medium', 'medium': 'large', 'large': 'xlarge',
			'xlarge':'2xlarge'},
		'm2': {
			'xlarge': '2xlarge', '2xlarge': '4xlarge'},
		'c1': {
			'medium': 'xlarge'}
		}

DOWNSCALE_TARGETS = {
		'm1': {
			'2xlarge': 'xlarge', 'xlarge': 'large', 'large': 'medium',
			'medium': 'small'},
		'm2': {
			'4xlarge': '2xlarge', '2xlarge': 'xlarge'},
		'c1': {
			'xlarge': 'medium'}
		}

NOOP_MODE = fetch_yaml('leptoid/scaling_config.yml')['noop']

def upscale(queue):
	""" Externally-facing method for upscaling a service's instance size.

	Parameters
	----------
	queue
		leptoid.ServiceQueue object with the environment, service type, and
		instance id to be scaled

	Returns: int specifying deployment id#
	"""

	# Return blank deployment id in case of an error.
	deploy_id = 0
	build_id = find_latest_build(queue.service)

	# Build KBS command and scale up.
	LOG.info("UPSCALING INSTANCE %s" % queue.instance_id.upper())
	try:
		kbs_cmd = _build_kbs_command(queue, UPSCALE_TARGETS, build_id)
		# Call KBS and parse output
		deploy_id = _call_kbs(kbs_cmd)
	except KeyError, e:
		LOG.error("Could not upscale %s from a %s. Continuing..." %
				(queue.instance_id, e))

	return deploy_id

def downscale(queue):
	""" Externally-facing method for downscaling a service's instance size.

	Parameters
	----------
	queue
		leptoid.ServiceQueue object with the environment, service type, and
		instance id to be scaled
	
	Returns: int specifying deployment id#
	"""

	# Return blank deployment id in case of an error.
	deploy_id = 0
	build_id = find_latest_build(queue.service)

	# Build KBS command and scale down.
	LOG.info("DOWNSCALING INSTANCE %s" % queue.instance_id.upper())
	try:
		kbs_cmd = _build_kbs_command(queue, DOWNSCALE_TARGETS, build_id)
		# Call KBS, parse output.
		deploy_id = _call_kbs(kbs_cmd)
	except KeyError, e:
		LOG.error("Could not downscale %s from a %s. Continuing..." %
				(queue.instance_id, e))

	return deploy_id

def rollback(queue, deploy_id):
	""" Externally-facing method for rolling back a deployment.

	Parameters
	----------
	queue
		leptoid.ServiceQueue object with the environment, service type, and
		instance id to be scaled
	deploy_id
		int, deployment id to roll back
	
	Returns nothing.
	
	Example usage:
	deployment_id = deploy.scale_down(kbs.KRS, i-deadbeef, 160)
	"""

	# Return blank deployment id in case of an error.
	deploy_id = 0

	# Build KBS command and scale down.
	LOG.info("ROLLING BACK INSTANCE %s" % queue.instance_id.upper())
	kbs_cmd = _build_kbs_rollback(deploy_id)
	deploy_id = _call_kbs(kbs_cmd)

def _build_kbs_command(queue, target_size_hash, build_id):
	""" Build the KBS command for resizing a given instance. 
	
	Parameters
	----------
	queue
		leptoid.ServiceQueue containing environment, service, instance info
	target_size_hash
		hashmap from current instance size to next size down
	build_id
		int, id to use when deploying new box
	"""
	env, service, instance_id = (queue.environment, queue.service,
			queue.instance_id)

	# Get instance size, retrieve target size, and pass it into KBS.
	[instance_prefix, instance_size] = queue.instance_size.split('.') 
	target_size = target_size_hash[instance_prefix][instance_size]
	LOG.info("\tScaling %s:%s to %s" % (service, instance_id, target_size))

	if queue.legacy:
		is_legacy = "--legacy "
	else:
		is_legacy = ""

	return 'kbs d n %s-t %s.%s %s %s %s:%i' % (
			is_legacy, instance_prefix, target_size, env, service, service,
			build_id)

def _build_kbs_rollback(deploy_id):
	""" Constructs the KBS rollback command for deploy_id. """
	LOG.info("\tRolling back deployment #%s" % str(deploy_id))
	return 'kbs d rollback %s' % str(deploy_id)

def _call_kbs(kbs_cmd):
	""" Calls KBS with build command. Returns deployment id.

	Parameters
	----------
	kbs_cmd
		str, command to issue to KBS
	
	TODO: THIS IS HACKISH. It assumes KBS only outputs a single line,
	then parses that single line for a deployment id. This will break when
	ported to KCS!!"""

	# Route STDOUT to a subprocess pipe, then parse the KBS output.
	LOG.info("\tExecuting command:")
	LOG.info("\t" + kbs_cmd)
	if not NOOP_MODE:
		p = subprocess.Popen(args=kbs_cmd.split(' '), stdout=subprocess.PIPE)
		output = p.stdout.readline()
		LOG.info(output)
		depid = findall('[0-9]{4,6}', output)[0]
	else:
		depid = -1

	# Use regex to find the only numeric string in return value and extract it.
	return int(depid)
