#!/bin/bash
set -e

if [ ! -e /opt/idpapi/etc/certs/jwt.key ]
then
    openssl genrsa -passout pass:${JWT_PASS} -out /opt/idpapi/etc/certs/jwt.key 1024
    openssl rsa -in /opt/idpapi/etc/certs/jwt.key -passin pass:${JWT_PASS} -pubout -out /opt/idpapi/etc/certs/jwt.crt
fi

if [ ! -e /opt/idpapi/etc/development.json ]
then
    envsubst < /opt/templates/development.json > /opt/idpapi/etc/development.json 
fi

exec "$@"
