#!/bin/bash
#
# This script starts MongoDB on your local machine such
# that it can be used for, for example, testing purposes.
# 
# Note for Docker users:
# Because of permissions restrictions for Docker containers,
# systemd does not work by default. Therefore, background
# services, such as MongoDB, will not start automatically.
# If your scripts / simulations rely on MongoDB, please first
# run this scripts to start the DB service.

# For MongoDB on CentOS installed via Yum:
mongod -f /etc/mongod.conf
