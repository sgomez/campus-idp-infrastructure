#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import utils
import os
import subprocess
from jinja2 import Environment, FileSystemLoader
import yaml
import logging
import argparse
import requests

# MAIN Python script file used by RabbitMQ


def createIdPshib(apitoken, qtoken, src=None, statusurl=None):
    headers = {
        'x-api-token': apitoken,
    }

    response = requests.get(src, headers=headers)
    responseDict = yaml.load(response.text, Loader=yaml.FullLoader)

    # Remove LOG file before start
    os.system("cat /dev/null > logs/createIdPshib.log")

    # Create a new LOG file
    logging.basicConfig(filename='logs/createIdPshib.log', format='%(asctime)s - %(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S', level=logging.DEBUG)

    # CONSTANTS STARTS
    ANS_SHIB = "/opt/ansible-shibboleth"
    ANS_VAULT_FILE = "/opt/ansible-shibboleth/.vault_pass"
    ANS_SHIB_INV = ANS_SHIB + "/inventories"
    ANS_SHIB_INV_FILES = ANS_SHIB_INV + "/files"
    ANS_SHIB_INV_PROD = ANS_SHIB_INV + "/production"

    IDP_PROD_HOST_VARS = ANS_SHIB_INV_PROD + "/host_vars"
    IDP_YML = IDP_PROD_HOST_VARS + '/' + responseDict['fqdn'] + '.yml'

    IDP_FILES_DIR = ANS_SHIB_INV_FILES+'/' + responseDict['fqdn']
    IDP_SAMPLE_FILES_DIR = ANS_SHIB_INV_FILES+'/sample-FQDN-dir'
    IDP_PLA_FILES_DIR = IDP_FILES_DIR + '/phpldapadmin'
    IDP_SSL_DIR = IDP_FILES_DIR + '/common/ssl'
    IDP_CRED_DIR = IDP_FILES_DIR + '/idp/credentials'
    IDP_STYLES_DIR = IDP_FILES_DIR + '/idp/styles'
    IDP_STYLES_DIR_SAMPLE = IDP_SAMPLE_FILES_DIR + '/idp/styles'

    IDP_FQDN = responseDict['fqdn']
    # CONSTANTS END

    # 1 - Create VM and SSL Credentials

    # We leave this part out for now. It will be done later.
    #logging.debug("Creating SSL CSR and KEY for '%s' ..." % (args.fqdn))
#  utils.generate_csr(args.fqdn, IDP_SSL_DIR)
    #logging.debug("...SSL CSR and KEY created.")

    # 2 - Prepare IdP environment

    # A - Retrieve all needed stuff for Ansible recipes
    logging.debug(
        "Retrieve all needed files for %s IDP needed by Ansible..." % IDP_FQDN)

    result = utils.store_images(responseDict, ANS_SHIB_INV_FILES)

    logging.debug("...all needed files are retrieved.")

    # 3 - Prepare Dynamic Inventory Script for the IDP
    logging.debug(
        "Creating Dynamic Inventory Script for instance %s IDP by Ansible..." % IDP_FQDN)

    idpDict = utils.get_idp_values(
        responseDict, None, ANS_SHIB_INV_FILES, True)

    logging.debug("Creating Dynamic Inventory Script...")

    utils.create_dyn_inv(responseDict, idpDict, ANS_SHIB_INV)

    logging.debug("...Dynamic Inventory Script created.")

    # 4 - Run Ansible Code with Dynamic Inventory
    logging.debug(
        "Run Ansible with the Dynamic Inventory Script created for instance %s IDP by Ansible..." % IDP_FQDN)

    result = subprocess.run(["ansible-playbook", "/opt/ansible-shibboleth/site.yml",
                             "-i", "/opt/ansible-shibboleth/inventories/dyn-inv.py"])

    logging.debug(
        "...Ansible has terminated his execution and the IdP has been created.")

    return result.returncode


if __name__ == "__main__":

    #result = createIdPshib(apitoken,qtoken,src=None,statusurl=None)
    result = createIdPshib()

    logging.debug("RESULT: %s" % result)
