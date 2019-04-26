#!/usr/bin/env python3
# coding=utf-8

# Libraries/Modules
from OpenSSL import crypto, SSL
import os
import logging

### FUNCTIONS NEEDED TO CREATE CSR/KEY HTTPS (PYTHON 2.7)

# Generate Certificate Signing Request (CSR)
def generate_csr(fqdn, dest, req_info = 'No', sans = []):
   if not os.path.exists(dest + '/' + fqdn + '.key'):
      os.makedirs(dest)

      # These variables will be used to create the fqdn.csr and fqdn.key files.
      csrfile = dest + '/' + fqdn + '.csr'
      keyfile = dest + '/' + fqdn + '.key'

      # OpenSSL Key Type Variable, passed in later.
      TYPE_RSA = crypto.TYPE_RSA

      # Appends SAN to have 'DNS:'
      ss = []
      for i in sans:
          ss.append("DNS: %s" % i)
      ss = ", ".join(ss)

      req = crypto.X509Req()
      req.get_subject().CN = fqdn

      if(req_info == 'y' or req_info == 'Y' or req_info == 'yes' or req_info == 'Yes'):
        C, ST, L, O, OU = get_csr_subjects()

        req.get_subject().countryName = C
        req.get_subject().stateOrProvinceName = ST
        req.get_subject().localityName = L
        req.get_subject().organizationName = O
        req.get_subject().organizationalUnitName = OU

      # Add in extensions
      base_constraints = ([
          crypto.X509Extension("keyUsage", False, "Digital Signature, Non Repudiation, Key Encipherment"),
          crypto.X509Extension("basicConstraints", False, "CA:FALSE"),
      ])
      x509_extensions = base_constraints
      # If there are SAN entries, append the base_constraints to include them.
      if ss:
          san_constraint = crypto.X509Extension("subjectAltName", False, ss)
          x509_extensions.append(san_constraint)
      req.add_extensions(x509_extensions)
      # Utilizes generate_key function to kick off key generation.
      key = generate_key(TYPE_RSA, 2048)
      req.set_pubkey(key)
      req.sign(key, "sha256")

      generate_files(csrfile, req)
      generate_files(keyfile, key)

      return req
   else:
      logging.debug("CSR and KEY for %s are already created in: %s" % (fqdn,dest))
      return 0

def get_csr_subjects():
   while True:
       C  = raw_input("Enter your Country Name (2 letter code) [US]: ")
       if len(C) != 2:
         print "You must enter two letters. You entered %r" % (C)
         continue
       ST = raw_input("Enter your State or Province <full name> []:California: ")
       if len(ST) == 0:
         print "Please enter your State or Province."
         continue
       L  = raw_input("Enter your (Locality Name (eg, city) []:San Francisco: ")
       if len(L) == 0:
         print "Please enter your City."
         continue
       O  = raw_input("Enter your Organization Name (eg, company) []:FTW Enterprise: ")
       if len(L) == 0:
          print "Please enter your Organization Name."
          continue
       OU = raw_input("Enter your Organizational Unit (eg, section) []:IT: ")
       if len(OU) == 0:
         print "Please enter your OU."
         continue
       break
   return C, ST, L, O, OU

   # Allows you to permanently set values required for CSR
   # To use, comment raw_input and uncomment this section.
   # C  = 'US'
   # ST = 'New York'
   # L  = 'Location'
   # O  = 'Organization'
   # OU = 'Organizational Unit'

# Generate Private Key
def generate_key(type, bits):
   key = crypto.PKey()
   key.generate_key(type, bits)
   return key

# Generate .csr/key files.
def generate_files(mkFile, request):
   if ".csr" in mkFile:
       f = open(mkFile, "w")
       f.write(crypto.dump_certificate_request(crypto.FILETYPE_PEM, request))
       f.close()
   elif ".key" in mkFile:
       f = open(mkFile, "w")
       f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, request))
       f.close()
   else:
       logging.debug("Failed to create CSR/Key files for %s" % (dest))
       exit()
