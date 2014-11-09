FROM dockerfile/haproxy

# Install virtualenv
# RUN apt-get install python-pip -y
# RUN apt-get install python-setuptools && easy_install pip
RUN curl https://bootstrap.pypa.io/get-pip.py | python3

# Add the 
ADD haproxy-config-generator-app/requirements.txt /tmp/haproxy-config-generator-app/requirements.txt

RUN cd /tmp/haproxy-config-generator-app/ && \
    pip install -r requirements.txt

# Add the application code
ADD haproxy-config-generator-app /usr/local/bin/haproxy-config-generator-app

VOLUME ["/data/haproxy/config"]

ADD init.sh /init.sh

EXPOSE 42081

# Define default command.
CMD ["bash", "/init.sh"]
