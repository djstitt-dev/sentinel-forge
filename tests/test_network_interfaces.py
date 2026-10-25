import json
import subprocess
import unittest

from sentinel_forge.ai_console import _requested_tool
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.network_interfaces import collect_network_interfaces


class FakeResult:
    returncode=0
    stdout=json.dumps([
        {"ifname":"lo","operstate":"UNKNOWN","mtu":65536,"addr_info":[
            {"family":"inet","local":"127.0.0.1","prefixlen":8,"scope":"host"}
        ]},
        {"ifname":"enp0s3","operstate":"UP","mtu":1500,"addr_info":[
            {"family":"inet","local":"10.0.2.15","prefixlen":24,"scope":"global","dynamic":True},
            {"family":"inet6","local":"fd00::15","prefixlen":64,"scope":"global"}
        ]}
    ])


class NetworkInterfaceTests(unittest.TestCase):
    def test_fixed_read_only_argv_and_structured_addresses(self):
        seen={}
        def runner(argv,**kwargs):
            seen["argv"]=argv; seen.update(kwargs); return FakeResult()
        result=collect_network_interfaces(runner=runner)
        self.assertEqual(("/usr/sbin/ip","-j","address","show"),seen["argv"])
        self.assertIs(seen["shell"],False)
        self.assertEqual(["10.0.2.15"],result["primary_global_ipv4"])
        self.assertFalse(result["observation"]["network_probe_performed"])
        self.assertFalse(result["observation"]["configuration_changed"])

    def test_failure_is_blocked(self):
        def runner(*a,**k):
            r=FakeResult(); r.returncode=1; return r
        with self.assertRaises(EnrollmentError):
            collect_network_interfaces(runner=runner)

    def test_exact_operator_question_routes_to_observation(self):
        self.assertEqual("network_interfaces",_requested_tool("What is the IP address of forge?"))

    def test_interface_question_routes_to_observation(self):
        self.assertEqual("network_interfaces",_requested_tool("Show me the network interfaces"))


if __name__=="__main__":
    unittest.main()

class LocalIpIntentTests(unittest.TestCase):
    def test_first_person_current_ip_routes(self):
        variants=(
            "what is your current ip address?",
            "what is your ip address?",
            "what's forge's ip address?",
            "show your ipv4 address",
            "what is the local ip address?",
        )
        for q in variants:
            with self.subTest(q=q):
                self.assertEqual("network_interfaces",_requested_tool(q))

class LocalSystemIpVocabularyTests(unittest.TestCase):
    def test_local_system_referents_route_to_observation(self):
        variants=(
            "what is the system ip address?",
            "what is this system's ip address?",
            "what is the host ip address?",
            "what is this host's ipv4 address?",
            "what is the machine ip address?",
            "show this machine's ip address",
        )
        for q in variants:
            with self.subTest(q=q):
                self.assertEqual("network_interfaces",_requested_tool(q))

    def test_unrelated_remote_host_does_not_route_as_local_interface(self):
        self.assertEqual("network_knowledge", _requested_tool("what is reaper's ip address?"))
        self.assertNotEqual("network_interfaces", _requested_tool("what is reaper's ip address?"))
        self.assertIsNone(_requested_tool("what is google's ip address?"))
