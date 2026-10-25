import unittest
from sentinel_forge.network_intent import classify_network_intent,NetworkIntent
from sentinel_forge.network_observation import observe_routes,observe_neighbors,observe_listeners,observe_dns,observe_interface_stats,network_health

class NetworkIntentTests(unittest.TestCase):
    def test_typed_intents(self):
        cases={
            "what is the system ip address?":NetworkIntent.LOCAL_ADDRESS,
            "what is the default gateway?":NetworkIntent.DEFAULT_GATEWAY,
            "show routes":NetworkIntent.ROUTES,
            "what dns is this system using?":NetworkIntent.DNS,
            "show the arp table":NetworkIntent.NEIGHBORS,
            "what ports are listening?":NetworkIntent.LISTENERS,
            "show interface statistics":NetworkIntent.LINK_STATS,
            "network health":NetworkIntent.HEALTH,
        }
        for q,want in cases.items():
            with self.subTest(q=q): self.assertEqual(want,classify_network_intent(q).intent)
    def test_remote_ip_not_local(self):
        self.assertEqual(NetworkIntent.NONE,classify_network_intent("what is reaper's ip address?").intent)

class LiveObservationTests(unittest.TestCase):
    def test_live_observations_are_read_only(self):
        self.assertIsInstance(observe_routes()["routes"],list)
        self.assertIsInstance(observe_neighbors()["neighbors"],list)
        self.assertIsInstance(observe_listeners()["listeners"],list)
        self.assertIsInstance(observe_dns()["resolvectl_dns"],list)
        self.assertIsInstance(observe_interface_stats()["interfaces"],list)
        h=network_health()
        self.assertFalse(h["observation"]["network_probe_performed"])
        self.assertFalse(h["observation"]["configuration_changed"])
