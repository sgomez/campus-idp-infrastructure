#!/bin/bash
set -e

mongo \
    --username ${MONGO_INITDB_ROOT_USERNAME} \
    --password ${MONGO_INITDB_ROOT_PASSWORD} \
    --eval "db.getSiblingDB(\"${MONGO_INITDB_DATABASE}\").runCommand({ createUser: \"${MONGO_IDPAPI_USERNAME}\", pwd: \"${MONDO_IDPAPI_PASSWORD}\", roles: [ \"readWrite\" ] })"
