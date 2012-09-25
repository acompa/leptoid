""" Module for calling the deployment API and obtaining deployment info. """

import logging
LOG = logging.getLogger('deploy_api')

import os
import sys
sys.path.insert(0, os.path.abspath(
	os.path.dirname(os.path.abspath(__file__)) + "/../lib"))
import urllib2

try:
	import knewton.json as json
	import knewton.services.authentication_client as auth_client
	from knewton.config import KnewtonConfig
except ImportError:
	import k.json as json
	import k.services.authentication_client as auth_client
	from k.config import KnewtonConfig

from leptoid.utils import ServiceRevisionIds

def extract_ids(server_info):
	return [server['aws_instance_id'] for server in server_info]

def match_deploy_id(deploy_id, reservation):
	return reservation['build_id'] == int(deploy_id)

def build_auth_token():
	""" Builds Leptoid's auth token for the deployment API.

	Returns an auth token built by knewton.services.authentication_client.
	"""
	auth_url = KnewtonConfig(
			).fetch_config('services/authentication.yml')['service']['url']
	auth_items = KnewtonConfig(
			).fetch_config('applications/deployment.yml')['application']
	username = auth_items['username'].strip()
	password = auth_items['password'].strip()
	return auth_client.get_auth_token(auth_url, username, password)

def fetch_servers():
	""" Fetches info for every deploy. Also handles auth. """

	output = []
	try:
		builds = fetch_build_info()
		for build in builds:
			print build
			if 'reservation' in build and build['reservation']:
				output.append(build['reservation'])
	except urllib2.URLError, err:
		LOG.error(err.code)
		LOG.error(err.read())

	return output

def fetch_build_info():
	""" Fetches info for every build. """

	auth = build_auth_token()
	deployment_url = KnewtonConfig(
			).fetch_config('services/deployment.yml')['service']['url']
	
	# Fetching build info
	url = deployment_url + '/builds'
	contents = auth_client.fetch_url(url, None, {}, auth)
	return json.loads(contents.read())

def find_instance_ids(deploy_id):
	""" Retrives instance ids associated with a deploy.

	Parameters
	----------
	deploy_id
		int, id of deployment to be evaluated

	Returns a list of every instance id (one or more) in this deployment.
	"""

	deploys = fetch_servers()
	ids = None
	
	# Return instance ids from build info.
	for server in deploys:
		if match_deploy_id(deploy_id, server):
			ids = extract_ids(server['servers'])

	return ids

def find_service_revs(service_name):
	""" Retrieves all builds associated with a service. Connects to the
	deployment API (with auth) to accomplish this.

	Parameters
	----------
	service
		str, name of service

	Returns five most recent build ids.
	"""

	output = []
	try:
		builds = fetch_build_info()
		for build in builds:
			# If we find an applicable deployment, get its info.
			if build['application_name'] == service_name:
				name = build['application_name']
				svn_rev = int(build['services'][0]['svn_rev'])
				date = build['created_at']
				if 'manifests' in build:
					jenkins_job_id = int(build['manifests']['jenkins_job_id'])
				else:
					jenkins_job_id = None
				output.append(
						ServiceRevisionIds(name=name, date=date,
							svn=svn_rev, jenkins=jenkins_job_id))
	except urllib2.URLError, err:
		LOG.error(err.code)
		LOG.error(err.read())

	# Return the most recent build.
	return output

def find_latest_build(service_name):
	""" Takes a list of service revisions for ${service_name} produced by
	find_service_revs(), returns the latest build in that list.

	Parameters
	----------
	service_name
		str, name of service to search for in all builds
	
	Returns the Jenkins id of the most recent build; if that's not available,
	the project is legacy and thus only has a SVN id.
	"""

	build_list = find_service_revs(service_name)
	latest_build = sorted(build_list, key=lambda x: x.date, reverse=True)[0]
	if latest_build.jenkins:
		return latest_build.jenkins
	return latest_build.svn
