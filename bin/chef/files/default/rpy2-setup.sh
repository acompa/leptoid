#!/bin/bash

# $1 == version of R to install
# currently = 2.15.1

#####
# Install R
#####
wget http://cran.r-project.org/src/base/R-2/R-$1.tar.gz
tar zxvf R-$1.tar.gz
cd R-$1/
./configure --enable-R-shlib --with-x=no		# mandatory for rpy2
make
make check
sudo make install
cd ..
sudo rm -rf R-$1/ build/
rm R-$1.tar.gz

#####
# rpy2 on Ubuntu is easy--just make sure Python can find the shared libs
#####
sudo pip install rpy2
export PATH=$PATH:/usr/local/lib

#####
# rpy2 for Mac is...different.
#####
#wget http://pypi.python.org/packages/source/r/rpy2/rpy2-2.2.6.tar.gz
#tar zxvf rpy2-2.2.6.tar.gz
#cd rpy2-2.2.6/
#python setup.py build --r-home /usr/local/bin/R --r-home-lib /usr/local/bin/R/lib
#sudo python setup.py install
#cd ..
#rm -rf rpy2-2.2.6/
#
## Linking libraries to /usr/local/lib.
#sudo ln -s /usr/local/lib/R/lib/libR.so /usr/local/lib/
#sudo ln -s /usr/local/lib/R/lib/libRlapack.so /usr/local/lib/
#sudo ln -s /usr/local/lib/R/lib/libRblas.so /usr/local/lib/
#sudo ldconfig
#
## Confirm successful installation.
## python -m 'rpy2.tests'

#####
# Install R package dependencies.
#####
sudo R CMD BATCH config/requirements.R
