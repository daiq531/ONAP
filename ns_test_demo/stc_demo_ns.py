
##############################################################################
# Copyright (c) 2018 Spirent Communications and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Author: qiang.dai@spirent.com
#
##############################################################################

import logging
import sys
import time

import openstack

logger = logging.getLogger(__name__)


# params = {
#     "auth_url": "http://mosel.set.calenglab.spirentcom.com:5000/v3/",
#     "username": "qiang.dai",
#     "password": "spirent",
#     "identity_api_version": "v3",
#     "project_name": "qiang.dai",
#     "project_domain_name": "Default",
#     "user_domain_name": "default",
#     "region": "RegionOne",
#     "verify": False
# }
# cli = openstack.connect(**params)
# cli.authorize()
#
# server = cli.get_server("049eb491-04c2-467f-8916-9e1b9d176611")

#>>> server.addresses
#Munch({u'vnflcv-right': [{u'OS-EXT-IPS-MAC:mac_addr': u'fa:16:3e:bf:6a:a7', u'version': 4, u'addr': u'192.168.20.98', u'OS-EXT-IPS:type': u'fixed'}], u'public': [{u'OS-EXT-IPS-MAC:mac_addr': u'fa:16:3e:d8:2e:8a', u'version': 6, u'addr': u'fd00:a6d:b800::3f3', u'OS-EXT-IPS:type': u'fixed'}, {u'OS-EXT-IPS-MAC:mac_addr': u'fa:16:3e:d8:2e:8a', u'version': 4, u'addr': u'10.109.184.201', u'OS-EXT-IPS:type': u'fixed'}], u'vnflcv-left': [{u'OS-EXT-IPS-MAC:mac_addr': u'fa:16:3e:08:2e:b7', u'version': 4, u'addr': u'192.168.10.59', u'OS-EXT-IPS:type': u'fixed'}]})

class STCDemoNSError(Exception):
    pass

class STCDemoNS(object):

    # following parameters must be align with the csar package
    stc_west_instance_name = "stcv_west"
    stc_east_instance_name = "stcv_east"
    openwrt_instance_name = "dut"
    mgmt_net_name = "external"
    west_test_net_name = "west_net"
    east_test_net_name = "east_net"

    def __init__(self, onap):
        self.onap = onap
        self.ns_instance_id = None

        self.openstack_client = None

        self._stcv_west_ip = None
        self._stcv_west_test_port_ip = None
        self._stcv_east_ip = None
        self._stcv_east_test_port_ip = None
        self._dut_left_ip = None
        self._dut_right_ip = None

    @property
    def stcv_west_ip(self):
        return self._stcv_west_ip

    @property
    def stcv_west_test_port_ip(self):
        return self._stcv_west_test_port_ip

    @property
    def stcv_east_ip(self):
        return self._stcv_east_ip

    @property
    def stcv_east_test_port_ip(self):
        return self._stcv_east_test_port_ip

    @property
    def dut_left_ip(self):
        return self._dut_left_ip

    @property
    def dut_right_ip(self):
        return self._dut_right_ip

    def set_openstack_client(self, params):
        try:
            client = openstack.connect(**params)
            client.authorize()
        except Exception as e:
            logger.error(e)
            raise STCDemoNSError("create openstack client fail.")

        # server = client.get_server(name_or_id="ubuntu1604")
        self.openstack_client = client

    def instantiate(self, ns_pkg_id):
        vnfd_id_list = []

        # get vnfd id list according to ns_pkg_id
        vnf_pkg_id_list = self.onap.get_vnf_pkg_id_list(ns_pkg_id)
        for pkg_id in vnf_pkg_id_list:
            vnfd_id = self.onap.get_vnfd_id(pkg_id)
            vnfd_id_list.append(vnfd_id)

        ns_instance_id = self.onap.create_ns(ns_name="qdai_demostcns",
                            ns_desc="demo ns by qdai",
                            ns_pkg_id=ns_pkg_id,
                            service_type="vCPE1",       # TODO: should be changed into new service type
                            customer_name="hpa_cust1")  # TODO: should be changed into new customer
        try:
            ns_instance_jod_id = self.onap.instantiate_ns(ns_instance_id, vnfd_id_list=vnfd_id_list)
            self.onap.waitProcessFinished(ns_instance_id, ns_instance_jod_id, "instantiate")
        except Exception as e:
            self.onap.delete_ns(ns_instance_id)

        logger.info("instantiate ns success. ")
        self.ns_instance_id = ns_instance_id

        stc_west = self.get_stc_west_instance_info()
        self._stcv_west_ip = stc_west["mgmt_ip"]
        self._stcv_west_test_port_ip = stc_west["test_port_ip"]

        stc_east = self.get_stc_east_instance_info()
        self._stcv_east_ip = stc_east["mgmt_ip"]
        self._stcv_east_test_port_ip = stc_east["test_port_ip"]

        dut = self.get_dut_instance_info()
        self._dut_left_ip = dut["left_port_ip"]
        self._dut_right_ip = dut["right_port_ip"]

        return

    def terminate(self):
        self.onap.terminate_ns(self.ns_instance_id)
        self.onap.delete_ns(self.ns_instance_id)
        self.ns_instance_id = None
        return

    def wait_vnf_ready(self):
        time.sleep(10)
        return

    def get_stc_west_instance_info(self):
        # get server id from ns instance
        vnfid = self.onap.get_vnfid(self.ns_instance_id, self.stc_west_instance_name)
        server_id = self.onap.get_server_ids(vnfid)[0]
        server = self.openstack_client.get_server(server_id)
        server_name = server.name
        mgmt_ip = server.addresses[self.mgmt_net_name][0]["addr"]
        test_port_ip = server.addresses[self.west_test_net_name][0]["addr"]
        instance_info = {
            "name": server_name,
            "id": server_id,
            "mgmt_ip": mgmt_ip,
            "test_port_ip": test_port_ip
        }

        return instance_info

    def get_stc_east_instance_info(self):
        # get server id from ns instance
        vnfid = self.onap.get_vnfid(self.ns_instance_id, self.stc_east_instance_name)
        server_id = self.onap.get_server_ids(vnfid)[0]
        server = self.openstack_client.get_server(server_id)
        server_name = server.name
        mgmt_ip = server.addresses[self.mgmt_net_name][0]["addr"]
        test_port_ip = server.addresses[self.east_test_net_name][0]["addr"]
        instance_info = {
            "name": server_name,
            "id": server_id,
            "mgmt_ip": mgmt_ip,
            "test_port_ip": test_port_ip
        }

        return instance_info

    def get_dut_instance_info(self):
        # get server id from ns instance
        vnfid = self.onap.get_vnfid(self.ns_instance_id, self.openwrt_instance_name)
        server_id = self.onap.get_server_ids(vnfid)[0]
        server = self.openstack_client.get_server(server_id)
        server_name = server.name
        mgmt_ip = server.addresses[self.mgmt_net_name][0]["addr"]
        left_port_ip = server.addresses[self.west_test_net_name][0]["addr"]
        right_port_ip = server.addresses[self.east_test_net_name][0]["addr"]
        instance_info = {
            "name": server_name,
            "id": server_id,
            "mgmt_ip": mgmt_ip,
            "left_port_ip": left_port_ip,
            "right_port_ip": right_port_ip
        }

        return instance_info
