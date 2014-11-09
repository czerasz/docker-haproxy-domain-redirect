#!/bin/bash

# Generate the configuration file
python3 /usr/local/bin/haproxy-config-generator-app/app.py production

bash /haproxy-start
