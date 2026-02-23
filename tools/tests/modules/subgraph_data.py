from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from .base import setup_engine

def test_subgraph_data_passing():
    bridge, engine = setup_engine("STAGE 6: Sub-Graph Data Routing")
    
    # Generate all data types
    all_types = [t.value for t in DataType if t not in (DataType.FLOW, DataType.PROVIDER_FLOW)]
    
    # 1. Build the SubGraph Data mapped dictionary
    subgraph_data = {
        "nodes": [
            {
                "id": "sub_start",
                "type": "Start Node",
                "properties": {
                     "AdditionalOutputs": [f"Var_{t.capitalize()}" for t in all_types]
                },
                "outputs": ["Flow"] + [f"Var_{t.capitalize()}" for t in all_types]
            },
            {
                "id": "sub_ret",
                "type": "Return Node",
                "properties": {
                    "Label": "Flow",
                    "AdditionalInputs": [f"Var_{t.capitalize()}" for t in all_types]
                },
                "inputs": ["Flow"] + [f"Var_{t.capitalize()}" for t in all_types]
            }
        ],
        "wires": [{"from_node": "sub_start", "from_port": "Flow", "to_node": "sub_ret", "to_port": "Flow"}]
    }
    
    # Wire every port directly across the Sub-Graph boundary
    for t in all_types:
        port_name = f"Var_{t.capitalize()}"
        subgraph_data["wires"].append({
            "from_node": "sub_start",
            "from_port": port_name,
            "to_node": "sub_ret",
            "to_port": port_name
        })

    # 2. Setup the Parent Graph
    StartCls = NodeRegistry.get_node_class("Start Node")
    SubGraphCls = NodeRegistry.get_node_class("SubGraph Node")
    
    n_start = StartCls("main_start", "Start", bridge)
    n_sub = SubGraphCls("main_sub", "Data Passing SubGraph", bridge)
    
    # Inject the embedded data and force a schema refresh
    n_sub.properties["EmbeddedData"] = subgraph_data
    n_sub.rebuild_ports()
    
    # 3. Inject mock data into the Parent's variables registry so the SubGraph can pull them
    # The SubGraph Node maps parent wires, but since we are natively injecting, we can just 
    # set the inputs dict logically during the execution phase, OR set them as properties. 
    # Actually, a SubGraph dynamically maps inputs to internal properties.
    mock_data = {
        "Var_Any": {"complex": "data"},
        "Var_String": "Hello Synapse",
        "Var_Number": 42.5,
        "Var_Boolean": True,
        "Var_List": [1, 2, 3],
        "Var_Dict": {"engine": "v2"},
        "Var_Image": "base64_img_string",
        "Var_Color": "#FF00FF",
        "Var_Bytes": b"raw_data",
        "Var_Sceneobject": "Node1",
        "Var_Scenelist": ["Node1", "Node2"],
        "Var_Writemode": "Append",
        "Var_Password": "secret_hash"
    }
    
    for t in all_types:
        port_name = f"Var_{t.capitalize()}"
        if port_name in mock_data:
            n_sub.properties[port_name] = mock_data[port_name]
    
    # 4. Attach nodes locally to engine
    engine.register_node(n_start)
    engine.register_node(n_sub)
    engine.connect("main_start", "Flow", "main_sub", "Flow")
    
    # 5. Execute Parent Flow
    engine.run("main_start")
    
    import time
    time.sleep(0.5)
    
    # 6. Verify the data successfully routed back
    print("    [Verify] Checking Data Types successfully routed back to Parent scope...")
    success_count = 0
    total_ports = len(mock_data)
    
    for t in all_types:
        port_name = f"Var_{t.capitalize()}"
        if port_name in mock_data:
            expected = mock_data[port_name]
            val = bridge.get(f"{n_sub.node_id}_{port_name}")
            if val == expected:
                success_count += 1
            else:
                print(f"      [Mismatch] {port_name}: Expected {expected}, Got {val}")
                
    print(f"      Verified {success_count}/{total_ports} data types perfectly matched!")
    
    if success_count < total_ports:
        raise ValueError("Data Passage Integrity mismatch detected.")

    print("[SUCCESS] All Data Types beautifully penetrated the Sub-Graph boundary scopes in both directions!\n")
    return True
