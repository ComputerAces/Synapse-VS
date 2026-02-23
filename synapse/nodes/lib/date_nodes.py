from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.utils.datetime_utils import add_to_datetime, subtract_from_datetime
from synapse.core.date_units import DateUnitType
from synapse.core.types import DataType

@NodeRegistry.register("Date Add", "Data/DateTime")
class DateAddNode(SuperNode):
    """
    Adds a specified amount of time to a provided date string and returns the new date.
    
    Inputs:
    - Flow: Execution trigger.
    - Date: The starting date string (ISO format or 'now').
    - Amount: The numeric value to add to the date.
    - Unit: The time unit (Milliseconds, Seconds, Minutes, Hours, Day, Week, Month, Year).
    
    Outputs:
    - Flow: Triggered once the calculation is complete.
    - Result: The calculated date as a string.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Date"] = ""
        self.properties["Amount"] = "1"
        self.properties["Unit"] = "Day"
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Date": DataType.STRING,
            "Amount": DataType.INT,
            "Unit": DateUnitType
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.calculate_date_add)

    def calculate_date_add(self, Date=None, Amount=None, Unit=None, **kwargs):
        date_val = Date if Date is not None else self.properties.get("Date", "")
        amount = Amount if Amount is not None else self.properties.get("Amount", "1")
        unit = Unit if Unit is not None else self.properties.get("Unit", "Day")
        
        result = add_to_datetime(date_val, amount, unit)
        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        return True

@NodeRegistry.register("Date Subtract", "Data/DateTime")
class DateSubtractNode(SuperNode):
    """
    Subtracts a specified amount of time from a provided date string and returns the new date.
    
    Inputs:
    - Flow: Execution trigger.
    - Date: The starting date string (ISO format or 'now').
    - Amount: The numeric value to subtract from the date.
    - Unit: The time unit (Milliseconds, Seconds, Minutes, Hours, Day, Week, Month, Year).
    
    Outputs:
    - Flow: Triggered once the calculation is complete.
    - Result: The calculated date as a string.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Date"] = ""
        self.properties["Amount"] = "1"
        self.properties["Unit"] = "Day"
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Date": DataType.STRING,
            "Amount": DataType.INT,
            "Unit": DateUnitType
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.calculate_date_subtract)

    def calculate_date_subtract(self, Date=None, Amount=None, Unit=None, **kwargs):
        date_val = Date if Date is not None else self.properties.get("Date", "")
        amount = Amount if Amount is not None else self.properties.get("Amount", "1")
        unit = Unit if Unit is not None else self.properties.get("Unit", "Day")
        
        result = subtract_from_datetime(date_val, amount, unit)
        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        return True
