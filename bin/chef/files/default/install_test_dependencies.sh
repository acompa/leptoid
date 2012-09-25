sudo apt-get install -y python-setuptools
sudo easy_install pip
sudo pip install pytest
sudo pip install coverage
sudo pip install pytest_cov
sudo pip install beaker

#####
# Python's scientific computing tools.
#####
sudo apt-get install --yes automake autoconf libtool gfortran liblapack-dev g++ gcc python2.7-dev libreadline-dev xorg-dev gs subversion
sudo pip install numpy
sudo pip install scipy
sudo pip install pandas

#####
# Internal dependencies.
#####
#sudo pip install -i https://pypi.knewton.net/simple k.json k.urllib2 k.services

#####
# KBS for legacy boxes
#####
#git clone ssh://git.knewton.net/tools/KnewtonBuildSystem
#cd KnewtonBuildSystem
#sudo python setup.py install
#cd ..
#rm -rf KnewtonBuildSystem
