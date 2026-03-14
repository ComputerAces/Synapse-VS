
import json
import unittest
from unittest.mock import MagicMock
from axonpulse.core.flow_controller import FlowController
from axonpulse.core.migrations.v2_3_1_flow_standardization import migrate

class TestFlowStandardization(unittest.TestCase):
    def test_migration_and_execution(self):
        # 1. Simulate a legacy graph
        legacy_graph = {
            "version": "2.3.0",
            "nodes": [
                {"id": "node1", "type": "TestNode", "properties": {"outputs": ["Done", "Success"]}}
            ],
            "wires": [
                {"from_node": "node1", "from_port": "Done", "to_node": "node2", "to_port": "In"},
                {"from_node": "node1", "from_port": "Success", "to_node": "node3", "to_port": "In"}
            ]
        }
        
        # 2. Apply Migration
        new_data, modified = migrate(legacy_graph)
        self.assertTrue(modified)
        self.assertEqual(new_data["version"], "2.3.1")
        
        # Check wires
        for wire in new_data["wires"]:
            self.assertEqual(wire["from_port"], "Flow")
            
        # Check node outputs
        self.assertEqual(new_data["nodes"][0]["properties"]["outputs"], ["Flow", "Flow"])
        
        # 3. Execution Engine Simulation (FlowController)
        # Mock bridge
        bridge = MagicMock()
        bridge.get_batch.return_value = {
            "node1_ActivePorts": None, # Force fallback
            "node1_Condition": None,
            "node1_Priority": None
        }
        
        fc = FlowController("start_id")
        fc.pop() # Pop start
        
        # Standardized wires from migration
        wires = new_data["wires"]
        
        # Route outputs
        triggered = fc.route_outputs("node1", wires, bridge, context_stack=[])
        
        # Both migrated "Flow" wires should trigger because FlowController now checks port == "Flow"
        port_names = [p["from_port"] for p in triggered]
        print(f"Triggered ports: {port_names}")
        self.assertEqual(len(triggered), 2)
        for p in triggered:
            self.assertEqual(p["from_port"], "Flow")

if __name__ == "__main__":
    unittest.main()
