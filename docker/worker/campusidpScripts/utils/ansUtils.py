#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from jinja2 import Environment, FileSystemLoader
import utils
import yaml
import logging

def prepare_dyn_inv(dict_yaml, dict_idp):
   # Create the jinja2 environment.
   # Notice the use of trim_blocks, which greatly helps control whitespace.
   j2_env = Environment(loader=FileSystemLoader(os.getcwd()),keep_trailing_newline=True,trim_blocks=True,lstrip_blocks=True)
   result = j2_env.get_template('templates/dyn-inv.py.j2').render(yaml_vals=dict_yaml,idp_vals=dict_idp)
   return result

def create_dyn_inv(dict_yaml, dict_idp, dest):
   idp_yml = open("%s/dyn-inv.py" % dest, "w")
   values = prepare_dyn_inv(dict_yaml, dict_idp)
   idp_yml.write(values)
   idp_yml.close()

