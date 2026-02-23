import os
import sys

# Ensure we can import synapse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from tools.tests.modules.base import setup_engine, load_registry
from synapse.nodes.registry import NodeRegistry

def test_type_casting_collision():
    """
    STRESS TEST: Verifies that the engine gracefully handles incompatible types.
    """
    print(f"\n{'='*50}")
    print(f"[STAGE 11: Type Collision Validator]")
    print(f"{'='*50}")
    
    bridge, engine = setup_engine("Casting Test")
    load_registry()
    
    # 1. Create a Math Divide Node (expects Numbers for A and B)
    # We use Divide because Add uses DataType.ANY
    DivCls = NodeRegistry.get_node_class("Divide")
        
    div_node = DivCls("math_1", "Divide Node", bridge)
    div_node.properties["A"] = 10
    div_node.properties["B"] = 2
    engine.register_node(div_node)
    
    # 2. Inject an INCOMPATIBLE type (Dictionary) into the input via runtime injection
    print(f"    [Action] Injecting Dictionary into Number port...")
    # Injecting dict into "A" which is DataType.NUMBER in DivideNode
    runtime_inputs = {"A": {"illegal": "data"}} 
    
    print(f"    [Action] Executing Node with invalid inputs...")
    final_args = div_node.prepare_execution_args(runtime_inputs)
    
    print(f"    [Verify] Checking cast results...")
    print(f"      - Original Input: {runtime_inputs['A']}")
    print(f"      - Cast Result (A): {final_args['A']} (Type: {type(final_args['A']).__name__})")
    
    # TypeCaster.to_number(dict) -> returns 0
    if not isinstance(final_args['A'], (int, float)):
        raise RuntimeError(f"Type Collision FAIL: Input A remained a {type(final_args['A']).__name__}")
    
    if final_args['A'] != 0:
        raise RuntimeError(f"Type Collision FAIL: Input A was cast to {final_args['A']} instead of fallback 0.")

    print(f"[SUCCESS] TypeCaster shielded the node from incompatible data.")

if __name__ == "__main__":
    test_type_casting_collision()
