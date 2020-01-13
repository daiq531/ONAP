
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

from onap import ONAP
from simple_traffic import SimpleTrafficTest
from stc_demo_ns import STCDemoNS

labserver_ip = ""

def main():
    onap = ONAP(base_url="http://192.168.235.41:30280")
    onap.setup()

    ns = STCDemoNS(onap)
    params = {
        "auth_url": "http://mosel.set.calenglab.spirentcom.com:5000/v3/",
        "username": "qiang.dai",
        "password": "spirent",
        "identity_api_version": "v3",
        "project_name": "qiang.dai",
        "project_domain_name": "Default",
        "user_domain_name": "default",
        "region": "RegionOne",
        "verify": False
    }
    ns.set_openstack_client(params)

    ns_pkg_id = ""
    ns.instantiate(ns_pkg_id)
    ns.wait_vnf_ready()

    test = SimpleTrafficTest(labserver_ip=labserver_ip,
                                stcv_west_mgmt_ip=ns.stcv_west_ip,
                                stcv_west_test_port_ip=ns.stcv_west_test_port_ip,
                                stcv_east_mgmt_ip=ns.stcv_east_ip,
                                stcv_east_test_port_ip=ns.stcv_east_test_port_ip,
                                dut_left_ip=ns.dut_left_ip,
                                dut_right_ip=ns.dut_right_ip)
    test.run()
    test.show_result()

    ns.terminate()

    onap.teardown()

if __name__=="__main__":
    main()