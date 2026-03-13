from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.utils.datetime_utils import add_to_datetime, subtract_from_datetime

from axonpulse.core.date_units import DateUnitType

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Data/DateTime", version="2.3.0", node_label="Date Add")
def DateAddNode(Date: str = '', Amount: Any = '1', Unit: Any = 'Day', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Adds a specified amount of time to a provided date string and returns the new date.

Inputs:
- Flow: Execution trigger.
- Date: The starting date string (ISO format or 'now').
- Amount: The numeric value to add to the date.
- Unit: The time unit (Milliseconds, Seconds, Minutes, Hours, Day, Week, Month, Year).

Outputs:
- Flow: Triggered once the calculation is complete.
- Result: The calculated date as a string."""
    date_val = Date if Date is not None else _node.properties.get('Date', '')
    amount = Amount if Amount is not None else _node.properties.get('Amount', '1')
    unit = Unit if Unit is not None else _node.properties.get('Unit', 'Day')
    result = add_to_datetime(date_val, amount, unit)
    return result


@axon_node(category="Data/DateTime", version="2.3.0", node_label="Date Subtract")
def DateSubtractNode(Date: str = '', Amount: Any = '1', Unit: Any = 'Day', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Subtracts a specified amount of time from a provided date string and returns the new date.

Inputs:
- Flow: Execution trigger.
- Date: The starting date string (ISO format or 'now').
- Amount: The numeric value to subtract from the date.
- Unit: The time unit (Milliseconds, Seconds, Minutes, Hours, Day, Week, Month, Year).

Outputs:
- Flow: Triggered once the calculation is complete.
- Result: The calculated date as a string."""
    date_val = Date if Date is not None else _node.properties.get('Date', '')
    amount = Amount if Amount is not None else _node.properties.get('Amount', '1')
    unit = Unit if Unit is not None else _node.properties.get('Unit', 'Day')
    result = subtract_from_datetime(date_val, amount, unit)
    return result
