import json

import csv

import io

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.core.dependencies import DependencyManager

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

'\nScraper & Parser Nodes.\n\nHTML Parser: Extract data using BeautifulSoup (CSS Selectors).\nJSON <-> CSV: Converter utility.\n\nDependencies (Lazy): beautifulsoup4.\n'

BeautifulSoup = None

def ensure_bs4():
    global BeautifulSoup
    if BeautifulSoup:
        return True
    if DependencyManager.ensure('beautifulsoup4', 'bs4'):
        from bs4 import BeautifulSoup as _B
        BeautifulSoup = _B
        return True
    return False

@axon_node(category="Network/Scrapers", version="2.3.0", node_label="HTML Parser", outputs=['Text List'])
def HTMLParserNode(HTML_String: str = '', Selector: str = 'body', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Parses HTML content and extracts data using CSS Selectors.

This node takes an HTML string and applies a CSS selector (e.g., 'a', '.title', 
'#content') to find matching elements, returning their stripped text content 
as a list.

Inputs:
- Flow: Trigger the parsing process.
- HTML String: The raw HTML content to parse.
- Selector: CSS Selector string for targeting elements.

Outputs:
- Flow: Triggered after parsing completes.
- Text List: List of extracted text strings from matching elements."""
    html_string = HTML_String or _node.properties.get('HTML String', _node.properties.get('HTMLString', ''))
    selector = Selector or _node.properties.get('Selector', _node.properties.get('Selector', 'body'))
    if not html_string:
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    if not ensure_bs4():
        _node.logger.error('beautifulsoup4 not installed.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    try:
        soup = BeautifulSoup(html_string, 'html.parser')
        elements = soup.select(selector)
        results = [el.get_text(strip=True) for el in elements]
        _node.logger.info(f"Found {len(results)} items matching '{selector}'")
    except Exception as e:
        _node.logger.error(f'Parse Error: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return results


@axon_node(category="Data/JSON", version="2.3.0", node_label="JSON CSV Converter")
def JsonCsvNode(Data: Any = None, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Converts between JSON (list of dicts) and CSV string formats.

Inputs:
- Flow: Execution trigger.
- Data: The data to convert (List for JSON to CSV, String for CSV to JSON).

Properties:
- Action: Set to "JSON to CSV" or "CSV to JSON".

Outputs:
- Flow: Triggered after successful conversion.
- Result: The converted data."""
    action = _node.properties.get('Action', _node.properties.get('Action', 'JSON to CSV')).lower()
    data = Data if Data is not None else _node.properties.get('Data', _node.properties.get('Data'))
    if data is None:
        _node.logger.warning('No Input Data')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    try:
        if 'json to csv' in action:
            if not isinstance(data, list):
                _node.logger.error('Data must be a list for JSON to CSV.')
                _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
            else:
                pass
            if not data:
                _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
            else:
                pass
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
            _node.logger.info(f'Converted {len(data)} rows to CSV.')
        else:
            if not isinstance(data, str):
                _node.logger.error('Data must be a string for CSV to JSON.')
                _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
            else:
                pass
            if not data.strip():
                _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
            else:
                pass
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
            finally:
                pass
            _node.logger.info(f'Converted CSV to {len(result)} dicts.')
    except Exception as e:
        _node.logger.error(f'Conversion Error: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result
