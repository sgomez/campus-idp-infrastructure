#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from operator import itemgetter
import sys
import getopt
import argparse
from subprocess import check_output, call
import subprocess
import shlex
import os
from io import StringIO
import logging
import requests

# PARAMETERS

# os.environ["JAVA_HOME"] = "/usr/lib/jvm/default-java/jre"

# END PARAMETERS

# FUNCTION NEEDED TO CREATE IDP METADATA CREDENTIALS

# Download and Store Logos and Favicons of an IdP
# dict_yaml    (YAML provided by WebGUI CampusIDP)
# dest         (/opt/ansible-shibboleth)


def store_images(dict_yaml, dest):

    for lang in dict_yaml['idp']['md']:
        logo = requests.get(dict_yaml['idp']['md'][lang]['mdui_logo'])
        favicon = requests.get(dict_yaml['idp']['md'][lang]['mdui_favicon'])
        if (lang == 'en'):
            flag = requests.get("http://flagpedia.net/data/flags/w580/gb.png")
        else:
            flag = requests.get(
                "http://flagpedia.net/data/flags/w580/%s.png" % lang)

        idp_images_dir = "%s/%s/idp/styles/%s" % (
            dest, dict_yaml['fqdn'], lang)
        pla_images_dir = "%s/%s/phpldapadmin/images" % (
            dest, dict_yaml['fqdn'])

        if not os.path.exists(idp_images_dir):
            os.makedirs(idp_images_dir)

        if not os.path.exists(pla_images_dir):
            os.makedirs(pla_images_dir)

        # Stores "logo.png" file for each language
        with open("%s/%s/idp/styles/%s/logo.png" % (dest, dict_yaml['fqdn'], lang), 'wb') as f:
            f.write(logo.content)

        # Stores "favicon.png" file for each language
        with open("%s/%s/idp/styles/%s/favicon.png" % (dest, dict_yaml['fqdn'], lang), 'wb') as f:
            f.write(favicon.content)

        # Stores "flag.png" file for each language
        with open("%s/%s/idp/styles/%s/%sFlag.png" % (dest, dict_yaml['fqdn'], lang, lang), 'wb') as f:
            f.write(flag.content)

        if lang == 'en':
            # Stores "logo.png" for phpLDAPadmin
            with open("%s/%s/phpldapadmin/images/logo.png" % (dest, dict_yaml['fqdn']), 'wb') as f:
                f.write(logo.content)

            # Stores "favicon.png" for phpLDAPadmin
            with open("%s/%s/phpldapadmin/images/favicon.png" % (dest, dict_yaml['fqdn']), 'wb') as f:
                f.write(favicon.content)

# Create Signing/Encryption SSO credentials for an IdP
# dict_yaml             (YAML provided by WebGUI CampusIDP)
# idp_credentials_dir   (Where the SSO credentials will be stored. Default into a 'tmp' dir)


def get_sso_credentials(dict_yaml, idp_credentials_dir='tmp'):
    for cert in dict_yaml['idp']['sso_keys']:
        if (cert['use'] == 'sign'):
            idp_signing_crt = cert["pubKey"]
            idp_signing_key = cert["privKey"]

            # Create IDP Signing CRT file
            idp_sign_crt_file = open(
                idp_credentials_dir+"/idp-signing.crt", "w")
            idp_sign_crt_file.write(idp_signing_crt)
            idp_sign_crt_file.close()

            # Create IDP Signing KEY file
            idp_sign_key_file = open(
                idp_credentials_dir+"/idp-signing.key", "w")
            idp_sign_key_file.write(idp_signing_key)
            idp_sign_key_file.close()

        if (cert['use'] == 'enc'):
            idp_encryption_crt = cert["pubKey"]
            idp_encryption_key = cert["privKey"]

            # Create IDP Encryption CRT file
            idp_enc_crt_file = open(
                idp_credentials_dir+"/idp-encryption.crt", "w")
            idp_enc_crt_file.write(idp_encryption_crt)
            idp_enc_crt_file.close()

            # Create IDP Encryption KEY file
            idp_enc_key_file = open(
                idp_credentials_dir+"/idp-encryption.key", "w")
            idp_enc_key_file.write(idp_encryption_key)
            idp_enc_key_file.close()

    logging.debug("Signing/Encryption Credentials created from GUI")

# Create/Retrieve Sealer/Keystore password for an IdP
# dict_yaml             (YAML provided by WebGUI CampusIDP)
# ans_vault_file        (Ansible Vault file contains the Vault password to encrypt KEYS and passwords". Default: None)
# dest                  (Where the SSO credentials will be stored. Default into a 'tmp' dir)
# debug                 (Set it to 'True' if you need more verbose logging. Default: False)


def get_sealer_keystore_pw(dict_yaml, ans_vault_file=None, dest='tmp', debug=False):

    idp_fqdn = dict_yaml['fqdn']

    if(dict_yaml['idp']['entityID']):
        entityID = dict_yaml['idp']['entityID']
    else:
        entityID = "https://" + idp_fqdn + "/idp/shibboleth"

    # Create a password long 27 characters
    idp_cred_pw = check_output(shlex.split(
        "openssl rand -base64 27")).strip().decode("utf-8")

    if(debug):
        logging.debug("IdP Credentials password : %s" % idp_cred_pw)

    # Create IDP Credentials DIR
    credentials_dir = "%s/%s/idp/credentials" % (dest, idp_fqdn)

    if not os.path.exists(credentials_dir):
        os.makedirs(credentials_dir)

    if(debug):
        logging.debug("IdP 'credentials' directory created in: %s" %
                      credentials_dir)

    # Find the IDP /bin directory
    idp_bin_dir = check_output(shlex.split(
        'find / -path "*shibboleth-identity-provider-*/bin"')).strip().decode("utf-8")

    if (debug):
        logging.debug("IdP 'bin' directory found in: %s" % idp_bin_dir)

    # Generate Sealer JKS and KVER

    # Check the existance of Sealer JKS and KVER
    sealer_jks = check_output(shlex.split(
        'find '+credentials_dir+' -name "sealer.jks"')).strip().decode("utf-8")
    sealer_kver = check_output(shlex.split(
        'find '+credentials_dir+' -name "sealer.kver"')).strip().decode("utf-8")

    if (not sealer_jks and not sealer_kver):
        call(["./seckeygen.sh", "--alias", "secret", "--storefile", credentials_dir + "/sealer.jks",
              "--storepass", idp_cred_pw, "--versionfile", credentials_dir + "/sealer.kver"], cwd=idp_bin_dir)

        if (ans_vault_file and os.path.isfile(ans_vault_file)):
            # Encrypt KEY with Ansible Vault
            # Needed to avoid output of 'call' commands
            FNULL = open(os.devnull, 'w')
            call(["ansible-vault", "encrypt", "sealer.jks", "--vault-password-file",
                  ans_vault_file], cwd=credentials_dir, stdout=FNULL)
            FNULL.close()
    else:
        if (debug):
            logging.debug("IdP Sealer JKS created into: %s" % sealer_jks)
            logging.debug("IdP Sealer KVER created into: %s" % sealer_kver)

    # Generate IDP Backchannel Certificate

    # Check the existance of IDP Backchannell P12 and CRT
    backchannel_p12 = check_output(shlex.split(
        'find '+credentials_dir+' -name "idp-backchannel.p12"')).strip().decode("utf-8")
    backchannel_crt = check_output(shlex.split(
        'find '+credentials_dir+' -name "idp-backchannel.crt"')).strip().decode("utf-8")

    if (not backchannel_p12 and not backchannel_crt):
        call(["./keygen.sh", "--storefile", credentials_dir + "/idp-backchannel.p12", "--storepass", idp_cred_pw, "--hostname", idp_fqdn,
              "--lifetime", "30", "--uriAltName", entityID, "--certfile", credentials_dir + "/idp-backchannel.crt"], cwd=idp_bin_dir)

        if (ans_vault_file and os.path.isfile(ans_vault_file)):
            # Encrypt KEY with Ansible Vault
            # Needed to avoid output of 'call' commands
            FNULL = open(os.devnull, 'w')
            call(["ansible-vault", "encrypt", "idp-backchannel.p12",
                  "--vault-password-file", ans_vault_file], cwd=credentials_dir, stdout=FNULL)
            FNULL.close()
    else:
        if (debug):
            logging.debug("IdP Backchannel PCKS12 created into: %s" %
                          backchannel_p12)
            logging.debug(
                "IdP Backchannel Certificate created into: %s" % backchannel_crt)

    # Generate IDP Signing Certificate and Key

    # Get IDP Signing/Encryption CRT/KEY from YAML
    get_sso_credentials(dict_yaml, credentials_dir)

    # Check the existance of Signing CRT and KEY
    signing_crt = check_output(shlex.split(
        'find '+credentials_dir+' -name "idp-signing.crt"')).strip().decode("utf-8")
    signing_key = check_output(shlex.split(
        'find '+credentials_dir+' -name "idp-signing.key"')).strip().decode("utf-8")

    if (not signing_crt and not signing_key):
        call(["./keygen.sh", "--hostname", idp_fqdn, "--lifetime", "30", "--uriAltName", entityID, "--certfile",
              credentials_dir + "/idp-signing.crt", "--keyfile", credentials_dir + "/idp-signing.key"], cwd=idp_bin_dir)

        if (ans_vault_file and os.path.isfile(ans_vault_file)):
            # Encrypt KEY with Ansible Vault
            # Needed to avoid output of 'call' commands
            FNULL = open(os.devnull, 'w')
            call(["ansible-vault", "encrypt", "idp-signing.key", "--vault-password-file",
                  ans_vault_file], cwd=credentials_dir, stdout=FNULL)
            FNULL.close()
    else:
        if (debug):
            logging.debug(
                "IdP Signing Certificate created into: %s" % signing_crt)
            logging.debug("IdP Signing Key created into: %s" % signing_key)

    # Generate IDP Encryption Certificate and Key

    # Check the existance of Encryption CRT and KEY
    encryption_crt = check_output(shlex.split(
        'find '+credentials_dir+' -name "idp-encryption.crt"')).strip().decode("utf-8")
    encryption_key = check_output(shlex.split(
        'find '+credentials_dir+' -name "idp-encryption.key"')).strip().decode("utf-8")

    if (not encryption_crt and not encryption_key):
        call(["./keygen.sh", "--hostname", idp_fqdn, "--lifetime", "30", "--uriAltName", entityID, "--certfile",
              credentials_dir + "/idp-encryption.crt", "--keyfile", credentials_dir + "/idp-encryption.key"], cwd=idp_bin_dir)

        if (ans_vault_file and os.path.isfile(ans_vault_file)):
            # Encrypt KEY with Ansible Vault
            # Needed to avoid output of 'call' commands
            FNULL = open(os.devnull, 'w')
            call(["ansible-vault", "encrypt", "idp-encryption.key",
                  "--vault-password-file", ans_vault_file], cwd=credentials_dir, stdout=FNULL)
            FNULL.close()
    else:
        if (debug):
            logging.debug(
                "IdP Encryption Certificate created into: %s" % encryption_crt)
            logging.debug("IdP Encryption Key created into: %s" %
                          encryption_key)

    # Generate a file containing the Credentials Password encrypted with Ansible Vault to be able to upload it on a private GIT

    idp_credentials_pw = "%s/%s_pw.txt" % (credentials_dir, idp_fqdn)

    if (os.path.isfile(idp_credentials_pw)):
        idp_cred_pw_file = open(credentials_dir+"/"+idp_fqdn+"_pw.txt", "r")
        idp_cred_pw = idp_cred_pw_file.read()
        idp_cred_pw_file.close()
        if "ANSIBLE_VAULT" in idp_cred_pw:
            idp_cred_pw = check_output(shlex.split('ansible-vault view --vault-password-file ' +
                                                   ans_vault_file+' ' + credentials_dir+'/'+idp_fqdn+'_pw.txt')).strip().decode("utf-8")
            return idp_cred_pw
        return idp_cred_pw
    else:
        idp_cred_pw_file = open(credentials_dir+"/"+idp_fqdn+"_pw.txt", "w")
        idp_cred_pw_file.write(idp_cred_pw)
        idp_cred_pw_file.close()

        if (ans_vault_file and os.path.isfile(ans_vault_file)):
            # Needed to avoid output of 'call' commands
            FNULL = open(os.devnull, 'w')
            call(["ansible-vault", "encrypt", credentials_dir+"/"+idp_fqdn+"_pw.txt",
                  "--vault-password-file", ans_vault_file], cwd=credentials_dir, stdout=FNULL)
            FNULL.close()
        return idp_cred_pw

# Get Apache admin emails


def get_admin_emails(dict_yaml):
    list_technical = []

    # HOWTO iterate over a Python Dictionary
    for contactType, value in dict_yaml['contacts'].items():
        # HOWTO iterate over a Python List
        if (contactType == 'technical'):
            list_technical.append({value['name']: value['email']})

    tech_emails = []
    for ctcTech in list_technical:
        for name, email in ctcTech.items():
            tech_emails.append(email)

    return ','.join(tech_emails)


def get_idp_scope(yml_file):
    list_scopes = []

    # HOWTO iterate over a Python List
    for scope in yml_file['idp']['scope']:
        list_scopes.append(scope)

    return ','.join(list_scopes)


'''
def get_idp_md_info(dict_md_info):
   org_name = dict_md_info['org_name']
   org_displayName = dict_md_info['org_displayName']
   mdui_displayName = dict_md_info['mdui_displayName']
   mdui_logo = dict_md_info['mdui_logo']

   return (org_name,org_displayName,mdui_displayName,mdui_logo)
'''

# Get IdP values and put them on a dictionary


def get_idp_values(dict_yaml, ans_vault_file, dest='tmp', debug=False):

    # Create an empty python dictionary
    idp = {}

    # Create Sealer/Keystore credentials and get their password
    idp_sealer_pw = get_sealer_keystore_pw(
        dict_yaml, ans_vault_file, dest, debug)

    idp['idp_sealer_pw'] = idp_sealer_pw
    idp['apache_admin_emails'] = get_admin_emails(dict_yaml)
    idp['scope'] = get_idp_scope(dict_yaml)

    return idp
