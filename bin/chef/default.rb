#
# Cookbook Name:: leptoid
# Recipe:: default
#
# Author: Alejandro Companioni
# Copyright 2012, Knewton, Inc. 
#
# Installing Leptoid's internal (Knewton-authored) and external dependencies.

RVERSION = "2.15.1"
DEPLOYNAME = "leptoid@knewton.com"
DEPLOYPW = "leptoid"

DEPLOYURL = "https://status.knewton.net/remote/deployment/"
AUTHURL = "https://my.knewton.com/remote/api/authentication/"

#####
# Installing packages via pkg manager.
#####
cookbook_file "/tmp/install_test_dependencies.sh" do
	source "install_test_dependencies.sh"
	mode "0644"
	backup false
end

# Python libraries.
bash "python-installs" do
	user "root"
	cwd "/tmp"
	code <<-EOF
	bash install_test_dependencies.sh
	EOF
end

# Installing R and rpy2, along with R package dependencies.
cookbook_file "/tmp/rpy2-setup.sh" do
	source "rpy2-setup.sh"
	mode "0644"
	backup false
end

cookbook_file "/tmp/requirements.R" do
	source "requirements.R"
	mode "0644"
	backup false
end

# Must build with shared libraries for rpy2. 
bash "R-install" do
	user "root"
	cwd "/tmp"
	code <<-EOF
	bash rpy2-setup.sh #{RVERSION}
	EOF
end

#####
# Deployment API credentials. Will change once Leptoid has a Knewdle account.
#####
bash "create-config-directory" do
	user "root"
	cwd "/etc"
	code <<-EOF
	mkdir -p ./knewton/applications
	mkdir -p ./knewton/services
	EOF
end

%w[/etc/knewton/applications/deployment.yml
/etc/knewton/applications/deployment_cmdline.yml].each do |fname|
	file fname do
		owner "root"
		group "root"
		mode "0755"
		content <<-EOF
		application:
			username: #{DEPLOYNAME}
			password: #{DEPLOYPW}
		EOF
		action :create
	end
end

file "/etc/knewton/services/deployment.yml" do
	owner "root"
	group "root"
	mode "0755"
	content <<-EOF
	service:
		url: #{DEPLOYURL}
	EOF
	action :create
end

file "/etc/knewton/services/authentication.yml" do
	owner "root"
	group "root"
	mode "0755"
	content <<-EOF
	service:
		url: #{AUTHURL}
	EOF
	action :create
end

#####
# Installing KBS.
#####
cookbook_file "/tmp/KnewtonBuildSystem-0.0.1.tar.gz" do
	source "KnewtonBuildSystem-0.0.1.tar.gz"
	mode "0644"
	backup false
end

bash "KBS-install" do
	user "root"
	cwd "/tmp"
	code <<-EOF
	pip install -i https://pypi.knewton.net/simple KCT
	tar zxvf KnewtonBuildSystem-0.0.1.tar.gz
	cd KnewtonBuildSystem-0.0.1
	python setup.py install
	EOF
end

