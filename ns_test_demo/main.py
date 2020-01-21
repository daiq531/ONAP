
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

from onap import ONAP
from simple_traffic import SimpleTrafficTest
from stc_demo_ns import STCDemoNS

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(hdlr=handler)
logger.setLevel(logging.DEBUG)
logger.propagate=True

labserver_ip = "192.168.235.98"

def main():
    onap = ONAP(base_url="http://192.168.235.41:30280")
    onap.setup()

    ns = STCDemoNS(onap)
    params = {
        "auth_url": "http://192.168.235.2:5000/v3",
        "username": "admin",
        "password": "Onap@10086",
        "identity_api_version": "3",
        "project_id": "8e6e4267c13240fc81d75bf18f8b59c0",
        "project_domain_id": "default",
        "user_domain_name": "Default",
        "region": "RegionOne",
        "verify": False,
        "auth_type": "password"
    }
    ns.set_openstack_client(params)

    ns_pkg_id = "4c32c96c-3224-43c5-ae7c-cdc6e97d949d"
    ns.instantiate(ns_pkg_id)
    ns.wait_vnf_ready()

    test = SimpleTrafficTest(labserver_ip=labserver_ip,
                                stcv_west_mgmt_ip=ns.stcv_west_ip,
                                stcv_west_test_port_ip=ns.stcv_west_test_port_ip,
                                stcv_east_mgmt_ip=ns.stcv_east_ip,
                                stcv_east_test_port_ip=ns.stcv_east_test_port_ip,
                                dut_left_ip=ns.dut_left_ip,
                                dut_right_ip=ns.dut_right_ip)
    test.run(port_rate=10, duration=60)
    test.show_result()

    ns.terminate()

    onap.teardown()

if __name__=="__main__":
    main()