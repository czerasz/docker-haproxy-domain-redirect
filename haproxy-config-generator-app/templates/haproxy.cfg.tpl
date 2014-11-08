global
    # log 127.0.0.1 local0
    # log 127.0.0.1 local1 notice
    log /dev/log local0 info
    log /dev/log local0 notice
    maxconn 4096
    chroot /var/lib/haproxy
    user haproxy
    group haproxy
    # daemon

defaults
    log global
    mode http
    option httplog
    option dontlognull
    contimeout 5000
    clitimeout 50000
    srvtimeout 50000
    errorfile 400 /etc/haproxy/errors/400.http
    errorfile 403 /etc/haproxy/errors/403.http
    errorfile 408 /etc/haproxy/errors/408.http
    errorfile 500 /etc/haproxy/errors/500.http
    errorfile 502 /etc/haproxy/errors/502.http
    errorfile 503 /etc/haproxy/errors/503.http
    errorfile 504 /etc/haproxy/errors/504.http

# Check what the options below do
#     option forwardfor
#     option http-server-close

{% if stats is defined %}
{% if stats.enabled %}
listen stats 0.0.0.0:{{ stats.port }}       #Listen on all IP's on port 9000
    stats enable

    mode http
    balance
    timeout client 5000
    timeout connect 4000
    timeout server 30000

    # This is the virtual URL to access the stats page
    stats uri {{ stats.uri }}

    # Authentication realm. This can be set to anything. Escape space characters with a backslash.
    stats realm HAProxy\ Statistics

    # The user/pass you want to use. Change this password!
    stats auth {{ stats.user }}:{{ stats.password }}

    # This allows you to take down and bring up back end servers.
    # This will produce an error on older versions of HAProxy.
    stats admin if TRUE
{% endif %}
{% endif %}

# Define fontends

{% if (domains is defined) or (redirects is defined) %}
frontend http
    bind 0.0.0.0:80

    {% for redirect in redirects %}
    # Redirect all traffic from {{ redirect.from }} to {{ redirect.to }}
    redirect prefix http://{{ redirect.to }} code {{ redirect.type }} if { hdr(host) -i {{ redirect.from }} }
    {% endfor %}

    # Define hosts
    {% for domain in domains %}
    acl host_{{ domain.name|replace(".", "_") }} hdr(host) -i {{ domain.name }}
    {% endfor %}

    # Match domains with backends
    {% for domain in domains %}
    use_backend {{ domain.name|replace(".", "_") }}_backend if host_{{ domain.name|replace(".", "_") }}
    {% endfor %}
{% endif %}

# Define backends

{% for domain in domains %}
{# TODO: use replace only once - find an elegant solution #}
backend {{ domain.name|replace(".", "_") }}_backend
#     balance roundrobin

    # "{{ domain.ip }}" taken from ${% filter upper %}{{ domain.container_link_alias }}{% endfilter %}_PORT_80_TCP_ADDR environment variable
    server {{ domain.name|replace(".", "_") }}_container1 {{ domain.ip }}:80 check
{% endfor %}