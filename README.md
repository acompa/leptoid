# leptoid
#### v0.0.1, released 9/25/2012

## Introduction

leptoid is a Python library that automatically increases or decreases host capacity based on that host's forecasted load. Load forecasts are based on [queuing theory](https://en.wikipedia.org/wiki/Queuing_theory), thus examining the rate at which Knewton services clear out requests from a figurative arrival queue.

### Queuing Theory
leptoid uses queuing theory's definition of [utilization](https://en.wikipedia.org/wiki/Queuing_theory#Utilization) to generate load forecasts. Instead of service rates, however, leptoid uses service times (the amount of time taken to service a request). Service times are the inverse of service rates, so we can redefine utilization as the product of arrival rate and service time.

## Installation & Usage

The preferred method for installing leptoid comes from a Chef recipe in bin/chef (which will install all dependencies, including the painful R+rpy2 setup). leptoid has not been submitted to the official cheese shop (pypi.python.org), although that will happen soon.

From there, you'll have to hunt down the leptoid/bin directory and start the run script (bin/runit.py). The Chef recipe handles all of this for you (which is why it is the preferred installation method).
* Note: if installing leptoid via the Chef recipe, the run script lives at /var/leptoid/bin, while logs and images live at /var/leptoid/log and /var/leptoid/img.


## Design
leptoid main functions have been separated into three components:

* communications with Graphite to retrieve arrival rate and service time data,
* a time series forecasting module (currently written with a Python-to-R bridge) for analyzing utilization data, and
* a deployment module responsible for scaling hosts in place (currently written using KBS and the deployment API)

These components have been designed as facades, allowing them to be swapped out with no impact on the other components. For example, one can easily swap leptoid's deployment calls and operate multiple instances of leptoid in different environments.

Further, all components are wrapped into a single LeptoidScaler object responsible for retrieving data, forecasting utilization, and making deployment decisions based on user-defined utilization limits. Each of these components is described below.

### Data Extraction and Retrieval

##### Extraction
Knewton's Readiness product uses nginx proxies to route requests to various webservices and applications. We can thus analyze proxy logs to understand how frequently requests are routed to each service/app, as well as the time each service/app takes to satisfy these requests.

We use [Logster](http://github.com/etsy/logster) to parse our nginx proxy logs. Knewton's version of Logster has a parser specifically written for this task. Thus, parsing proxy logs is as simple as:
1. setting up Logster on the proxy
2. editing the root crontab so that our parser runs every minute

##### Retrieval

leptoid makes use of Graphite's /render API to retrieve the service time and arrival rate data produced by Logster. leptoid.graphite defines methods for building the render call, calling Graphite, and extracting a time series of data from the response.

host_data is a nested dictionary with levels devoted to environment, service, and AWS instance id. leptoid parses this dictionary into a collection of convenient data structures (leptoid.ServiceQueue) with host information via a helper method (leptoid.service_queue.generate_service_queues).

In practice, you'll only need to call these methods:

    raw_rates = graphite.call_graphite(arrival_rate_targets, api_parameters)
    raw_times = graphite.call_graphite(service_time_targets, api_parameters)
    arrival_rates = graphite.extract_time_series(raw_rates)
    service_times = graphite.extract_time_series(raw_times)
    service_queues = service_queue.generate_service_queues(arrival_rates, service_times)

This could be further wrapped into fewer methods, but the above example provides some flexibility in how we model host load (we might want to move away from utilization some day).

### Forecasting

After retrieving data from Graphite, leptoid can forecast future utilization levels via the leptoid.forecasting module. Python's time-series forecasting options are lacking ([statsmodels](http://github.com/statsmodels/statsmodels) is the biggest contender), so this module currently uses [R's forecast package](http://robjhyndman.com/software/forecast/) via Python's [rpy2](http://rpy.sourceforge.net/rpy2.html) library.

The forecasting module is built to accept a leptoid.ServiceQueue and generate a forecast in one line:

    in_sample_forecast, utilization_forecast = forecasting.forecast_util(queue)

This method also plots the utilization forecast and stores the plots in a subdirectory; users can configure this via leptoid.forecasting.PLOT_DIRECTORY.

    leptoid.forecasting.PLOT_DIRECTORY = 'img/'

(this will probably change in the future).

### Deployment

leptoid will increase or decrease host capacity based on the utilization forecasts generated in leptoid.forecasting. Deployment actions are defined in leptoid.deploy, and they're as simple as

    deploy.upscale(queue)

for instances that need more capacity, and

    deploy.downscale(queue)

for instances that have too much capacity. Deployment is managed by Knewton's internal build system, which also offers deployment rollbacks:

    deploy.rollback(queue, rollback_build_id)

### The Scaler
Note that, in some places, leptoid's "facade" approach is porous. While the acts of scaling and querying Graphite are independent of the model used to forecast host load, configurations for scaling and querying Graphite both depend on the load model.

As a solution, leptoid introduces a middle piece to manage interactions. This piece -- defined in leptoid.scaler as...the LeptoidScaler -- is responsible for managing configurations for the retrieval, forecasting, and deployment pieces. On initialization it accepts a list of Graphite query targets and a YAML file with scaling and model configurations:

    scaler = LeptoidScaler(TARGETS, scaling_config)

Examples of these can be found in leptoid/targets.py and leptoid/leptoid.conf.

Further, it wraps all of the above pieces relatively nicely:

    service_queues = scaler.query_graphite_targets()
    for queue in service_queues:
        insample_forecast, util_estimate = forecasting.forecast(queue)
        if util_estimate != None:
            scaler.evaluate_instance(queue, util_estimate)

## Outstanding Issues & Roadmap

Here is a list of longer-term issues for the project:

* We currently treat each service as its own queue, without accounting for its role in the larger Readiness system. [https://en.wikipedia.org/wiki/Jackson_network Jackson networks] address this issue and look like an interesting modeling option.
* Configuration is not ideal. Some configs (leptoid.conf, targets.py) live in lib/python/leptoid, when they should live in e.g. /var/leptoid/conf. Others are hard-coded global variables in each module. These configs should either (a) pass in as command-line arguments to the run script, or (b) live in a conf directory.
* Forecasting needs to be optimized. It isn't clear that we need to generate a new set of forecasting weights on every pass (i.e. calling R's forecast.forecast() in leptoid.forecasting), and maybe R's forecast.eps(), with occasional calls to forecast.forecast(), will suffice.
* Related to the forecasting issue: forecasts for newly-deployed instances have accuracy issues, since they incorporate lots of NaN data. This missing data is cast to == 0 in leptoid.graphite (look for fillna(0)); a better approach would instead truncate all missing data at the start of a time series. I'm going to give this some thought this week.

## License

Apache License, Version 2.0
