#!/usr/bin/env python
#-*- coding:utf-8 -*-

from setuptools import setup, find_packages

setup(
    name = "ytvpn",
    version = "1.0.0",
    keywords = ("vpn"),
    description = "an opensource vpn tool",
    license = "MIT",

    url = "https://github.com/cao19881125/ytvpn.git",
    author = "yuntao.cao",
    author_email = "yuntao.cao@nocsys.com.cn",

    packages = find_packages(),
    include_package_data = True,
    platforms = "any",
    install_requires = ['enum','ConfigParser','oslo_config','pycrypto'],
    data_files = [('/etc/ytvpn',['./etc/server.cfg','./etc/client.cfg','./etc/user_file'])],
    scripts=['tools/ytvpn']
)
