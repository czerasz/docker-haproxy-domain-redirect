#!/bin/bash

# Generate the configuration file
cd /usr/local/bin/haproxy-config-generator-app/
source vendor/bin/activate
python3 app.py production
deactivate

bash /haproxy-start
