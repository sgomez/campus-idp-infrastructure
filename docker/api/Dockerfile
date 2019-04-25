FROM node:8

RUN mkdir -p /opt/idpapi
WORKDIR /opt/idpapi
ADD APICampusIdP /opt/idpapi
ADD certs /opt/idpapi/etc/certs

RUN npm install

RUN apt-get update && apt-get install -y gettext-base && apt-get clean

RUN mkdir -p /opt/templates
ADD development.json /opt/templates

ENV JWT_PASS 1234

ADD docker-entrypoint.sh /
ENTRYPOINT [ "/docker-entrypoint.sh" ]
CMD [ "/usr/local/bin/node", "/opt/idpapi/bin/www" ]
