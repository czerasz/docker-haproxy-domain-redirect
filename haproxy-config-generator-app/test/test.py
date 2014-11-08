# from nose import *
from nose.tools import *
import os
import re

import app

def setup_func():
    "set up test fixtures"

def teardown_func():
    "tear down test fixtures"

# @with_setup(setup_func, teardown_func)
# def test():
#     assert False

@raises(TypeError)
def test_stats_validation():
    app.validate_stats_section()

@raises(Exception)
def test_stats_validation_argument():
    ''' user and password fields are required '''

    stats = {}
    app.validate_stats_section(stats)

    stats = {"user": "test"}
    app.validate_stats_section(stats)

    stats = {"password": "test"}
    app.validate_stats_section(stats)

def test_stats_validation_defaults():
    ''' Test default values '''

    stats_base = {"user": "test", "password": "test"}
    stats = {}
    stats.update(stats_base)
    stats = app.validate_stats_section(stats)

    eq_(stats["uri"], "/haproxy-stats")
    eq_(stats["port"], 9000)
    eq_(stats["enabled"], True)


    stats = { "uri": "/haproxy-stats-test" }
    stats.update(stats_base)
    stats = app.validate_stats_section(stats)

    eq_(stats["uri"], "/haproxy-stats-test")
    eq_(stats["port"], 9000)
    eq_(stats["enabled"], True)


    stats = { "port": 1 }
    stats.update(stats_base)
    stats = app.validate_stats_section(stats)

    eq_(stats["uri"], "/haproxy-stats")
    eq_(stats["port"], 1)
    eq_(stats["enabled"], True)

def test_update_domains_section():
    ''' Test update_domains_section function '''

    domains = [
        {
            "name": "www.example.com",
            "container_link_alias": "example_app"
        }
    ]   
    app.update_domains_section(domains, "test")

    assert "ip" in domains[0]
    eq_(domains[0]["ip"], "localhost")

def test_render_configuration():
    ''' '''

    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    project_directory = os.path.abspath(os.path.join(current_file_directory, ".."))
    template_file_path = os.path.join(project_directory, "templates", "haproxy.cfg.tpl")


    # Test with empty configuration
    configuration = {}
    configuration_file_content = app.render_configuration(configuration, template_file_path)

    assert "listen stats" not in configuration_file_content
    assert "frontend http" not in configuration_file_content

    if re.match(r'^backend\S.*_backend$', configuration_file_content):
        assert False


    # Test only with stats configuration - without domain configuration
    stats_base = {"user": "test", "password": "test"}
    configuration = {
        "stats": app.validate_stats_section(stats_base)
    }
    configuration_file_content = app.render_configuration(configuration, template_file_path)

    assert "stats enable" in configuration_file_content
    assert "listen stats 0.0.0.0:{port}".format(port=configuration["stats"]["port"])  in configuration_file_content
    assert "stats uri {uri}".format(uri=configuration["stats"]["uri"]) in configuration_file_content
    assert "stats auth {user}:{password}".format(user=configuration["stats"]["user"], password=configuration["stats"]["password"]) in configuration_file_content


    # Test if one domain is set
    configuration.update({
        "domains": [
            {
                "name": "www.example.com",
                "container_link_alias": "example_app"
            }
        ]   
    })
    app.update_domains_section(configuration["domains"], "test")
    configuration_file_content = app.render_configuration(configuration, template_file_path)
    
    underscored_domain = configuration["domains"][0]["name"].replace(".", "_")

    assert "frontend http" in configuration_file_content
    assert ("acl host_"+ underscored_domain +" hdr(host) -i "+ configuration["domains"][0]["name"]) in configuration_file_content
    assert ("use_backend "+ underscored_domain +"_backend if host_"+ underscored_domain) in configuration_file_content
    assert ("backend "+ underscored_domain +"_backend") in configuration_file_content
    assert ("server "+ underscored_domain +"_container1 "+ configuration["domains"][0]["ip"] +":80 check") in configuration_file_content
    assert "redirect prefix" not in configuration_file_content

    # Test if one redirect is set
    configuration.update({
        "redirects": [
            {
                "from": "example.com",
                "to": "www.example.com",
                "type": 301
            }
        ]
    })
    configuration_file_content = app.render_configuration(configuration, template_file_path)
    redirect = configuration["redirects"][0]
    assert ("redirect prefix http://"+ redirect["to"] +" code "+ str(redirect["type"]) +" if { hdr(host) -i "+ redirect["from"] +" }") in configuration_file_content

    print configuration_file_content

    # assert False
