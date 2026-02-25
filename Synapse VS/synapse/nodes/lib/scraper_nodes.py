"""
Scraper & Parser Nodes.

HTML Parser: Extract data using BeautifulSoup (CSS Selectors).
JSON <-> CSV: Converter utility.

Dependencies (Lazy): beautifulsoup4.
"""
import json
import csv
import io
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager

# Lazy Global
BeautifulSoup = None

def ensure_bs4():
    global BeautifulSoup
    if BeautifulSoup: return True
    if DependencyManager.ensure("beautifulsoup4", "bs4"):
        from bs4 import BeautifulSoup as _B; BeautifulSoup = _B; return True
    return False


@NodeRegistry.register("HTML Parser", "Network/Scrapers")
class HTMLParserNode(SuperNode):
    """
    Parses HTML content and extracts data using CSS Selectors.
    
    This node takes an HTML string and applies a CSS selector (e.g., 'a', '.title', 
    '#content') to find matching elements, returning their stripped text content 
    as a list.
    
    Inputs:
    - Flow: Trigger the parsing process.
    - HTML String: The raw HTML content to parse.
    - Selector: CSS Selector string for targeting elements.
    
    Outputs:
    - Flow: Triggered after parsing completes.
    - Text List: List of extracted text strings from matching elements.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["HTML String"] = ""
        self.properties["Selector"] = "body"
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "HTML String": DataType.STRING,
            "Selector": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Text List": DataType.LIST
        }

    def register_handlers(self):
        self.register_handler("Flow", self.parse_html)

    def parse_html(self, HTML_String=None, Selector=None, **kwargs):
        # Fallback with legacy support
        html_string = HTML_String or self.properties.get("HTML String", self.properties.get("HTMLString", ""))
        selector = Selector or self.properties.get("Selector", self.properties.get("Selector", "body"))

        if not html_string:
            self.bridge.set(f"{self.node_id}_Text List", [], self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        if not ensure_bs4():
            self.logger.error("beautifulsoup4 not installed.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        try:
            soup = BeautifulSoup(html_string, "html.parser")
            elements = soup.select(selector)
            
            results = [el.get_text(strip=True) for el in elements]
            
            self.bridge.set(f"{self.node_id}_Text List", results, self.name)
            self.logger.info(f"Found {len(results)} items matching '{selector}'")
            
        except Exception as e:
            self.logger.error(f"Parse Error: {e}")

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True


@NodeRegistry.register("JSON CSV Converter", "Data/JSON")
class JsonCsvNode(SuperNode):
    """
    Converts between JSON (list of dicts) and CSV string formats.
    
    Inputs:
    - Flow: Execution trigger.
    - Data: The data to convert (List for JSON to CSV, String for CSV to JSON).
    
    Properties:
    - Action: Set to "JSON to CSV" or "CSV to JSON".
    
    Outputs:
    - Flow: Triggered after successful conversion.
    - Result: The converted data.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Action"] = "JSON to CSV"
        self.properties["Data"] = None
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Data": DataType.ANY
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.ANY
        }

    def register_handlers(self):
        self.register_handler("Flow", self.convert_data)

    def convert_data(self, Data=None, **kwargs):
        # Fallback with legacy support
        action = self.properties.get("Action", self.properties.get("Action", "JSON to CSV")).lower()
        data = Data if Data is not None else self.properties.get("Data", self.properties.get("Data"))
        
        if data is None:
            self.logger.warning("No Input Data")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        try:
            if "json to csv" in action:
                if not isinstance(data, list):
                    self.logger.error("Data must be a list for JSON to CSV.")
                    self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
                    return True
                
                if not data:
                     self.bridge.set(f"{self.node_id}_Result", "", self.name)
                     self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
                     return True

                output = io.StringIO()
                first = data[0]
                if isinstance(first, dict):
                    fieldnames = first.keys()
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)
                elif isinstance(first, list):
                    writer = csv.writer(output)
                    writer.writerows(data)
                else:
                    writer = csv.writer(output)
                    for row in data:
                         writer.writerow([row])
                         
                result = output.getvalue()
                self.bridge.set(f"{self.node_id}_Result", result, self.name)
                self.logger.info(f"Converted {len(data)} rows to CSV.")

            else: # CSV to JSON
                if not isinstance(data, str):
                    self.logger.error("Data must be a string for CSV to JSON.")
                    self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
                    return True
                
                if not data.strip():
                     self.bridge.set(f"{self.node_id}_Result", [], self.name)
                     self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
                     return True
                     
                input_io = io.StringIO(data)
                try:
                    dialect = csv.Sniffer().sniff(data[:2048])
                    input_io.seek(0)
                    reader = csv.DictReader(input_io, dialect=dialect)
                    result = list(reader)
                except:
                    input_io.seek(0)
                    reader = csv.DictReader(input_io)
                    result = list(reader)
                    
                self.bridge.set(f"{self.node_id}_Result", result, self.name)
                self.logger.info(f"Converted CSV to {len(result)} dicts.")

        except Exception as e:
            self.logger.error(f"Conversion Error: {e}")

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
