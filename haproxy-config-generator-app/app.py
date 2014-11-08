#!/usr/bin/env python

# This script generates the /etc/haproxy/haproxy.cfg file based on the template () and configuration (/data/haproxy/haproxy-redirect-configuration.yml)

import os
import sys
import errno
import yaml
from jinja2 import Environment, FileSystemLoader

reload(sys)
sys.setdefaultencoding("utf-8")
# <-- UTF-8 universal workaround done

AVAILABLE_ENVIRONMENTS = ["test", "development", "staging", "production"]

# 
def init(environment="production"):
    if environment == "test":
        # For testing purposes
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        project_directory = os.path.abspath(os.path.join(current_file_directory, ".."))

        configuration_file_path = os.path.join(project_directory, "config", "haproxy-redirect-configuration.yml.example")
        template_file_path = os.path.join(current_file_directory, "templates", "haproxy.cfg.tpl")
        haproxy_configuration_path = os.path.join(current_file_directory, "test", "tmp", "haproxy.cfg")

    # Read the haproxy-redirect-configuration.yml file which contains all the required data 
    configuration_stream = open(configuration_file_path, "r")
    configuration = yaml.load(configuration_stream)

    # Validate the stats section if it's available
    if "stats" in configuration:
        configuration["stats"] = validate_stats_section(configuration["stats"])
    else:
        configuration["stats"] = { "enabled": false }

    # Get IP's from the environment
    if "domains" in configuration:
        update_domains_section(configuration["domains"], environment)

    # Render the haproxy configuration
    configuration_file_content = render_configuration(configuration, template_file_path)
    
    # Overewrite the file each time
    with open (haproxy_configuration_path, "w") as file:
        file.write (configuration_file_content)

# 
def render_configuration(configuration, template_file_path):
    # Load templates off the filesystem.
    template_loader = FileSystemLoader( searchpath="/" )
    template_environment = Environment( loader=template_loader )

    # Read the template file using the environment object.
    template = template_environment.get_template( template_file_path )

    # Process the template to produce our final text
    return template.render( configuration )

# 
def validate_stats_section(stats_configuration):
    # Check required fields: user, password
    for key in ["user", "password"]:
        if key not in stats_configuration:
            raise Exception("Key: "+  key +" is not defined")

    # Set default fields if not present
    defaults = {
        "uri": "/haproxy-stats",
        "port": 9000,
    }

    defaults.update(stats_configuration)

    # Set an enabled flag
    defaults["enabled"] = True
    
    return defaults

# Update the domain entries with their container ip addresse
def update_domains_section(domains_configuration, environment):
    for domain in domains_configuration:
        variable_name = domain["container_link_alias"].upper() + "_PORT_80_TCP_ADDR"

        if environment == "test":
            ip = os.getenv(variable_name, "localhost")
        else:
            if variable_name in os.environ:
                ip = os.environ.get(variable_name)
            else:
                print variable_name + " doesn't exist"
                # Environment variable doesn't exist - exit with error code
                sys.exit(errno.EINVAL)
        
        domain["ip"] = ip


if __name__ == "__main__":
    environment = sys.argv[1]

    # If an valid environment argument was passed proceed
    if environment in AVAILABLE_ENVIRONMENTS:
        init(environment)

        # Exit and return standard exit code
        sys.exit()
    
    # When a wrong environment is passed exit with error code
    # errno.EINVAL - Invalid argument
    sys.exit(errno.EINVAL)
