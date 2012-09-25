"""
Here, we've defined a list of services monitored by Leptoid, as well as the
corresponding metric targets in Graphite.

SERVICES lists the names of all hosted services that will be monitored, and
TARGETS lists the corresponding metric targets in Graphite. In our case, we
look at arrival rates and service times for every monitored service.

Finally, there's a difference in service names between Graphite and our
deployment system (KBS); the final hash maps from the former to the latter.
"""

SERVICES = [
		"Application-Knewmena",
		"Application-Proctoring",
		"Application-Knewdle",
		"Application-BuyFlow",
		"Webservice-Authentication",
		"Webservice-Course",
		"Webservice-KRS",
		"Webservice-Observation",
		"Webservice-Study",
		"Webservice-Schedule"
		]

# Scale arrival rates by 0.016666 so it has the same time unit as
# service times.
TARGETS = {
		'arrival_rates':[
			("scale(*.%s.%s.Instance.*.arrival_rate,0.016666)"
				% (env, service))
			for service in SERVICES for env in ("Production", "Staging")],
		'service_times': [
			("*.%s.%s.Instance.*.proxy_service_time_avg"
				% (env, service))
			for service in SERVICES for env in ("Production", "Staging")]}

# Hash between service names in Graphite and KBS.
GRAPHITE_TO_KBS_MAP = {
	"Application-Knewmena": "knewmena",
	"Application-Proctoring": "proctoring_application",
	"Application-Knewdle": "knewdle",
	"Webservice-KRS": "kbs.KRS",
	"Webservice-Observation": "kbs.Observation",
	"Webservice-Course": "kbs.Course",
	"Webservice-Authentication": "kbs.Authentication",
	"Webservice-Study": "study_service",
	"Webservice-Schedule": "schedule_service",
	"Application-BuyFlow": "buy_flow"
}
