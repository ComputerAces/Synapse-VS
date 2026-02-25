
import sys

def render_form_cli(form_name, schema):
    """
    Renders a text-based form in the terminal.
    
    Args:
        form_name (str): Title of the form.
        schema (list): List of dicts [{"label": "Name", "type": "text", "default": ""}]
        
    Returns:
        dict: The collected data.
    """
    print("\n" + "="*40)
    print(f" FORM: {form_name}")
    print("="*40)
    print("Please enter the following details:\n")

    data = {}

    for field in schema:
        label = field.get("label", "Field")
        f_type = field.get("type", "text")
        default = field.get("default", "")
        
        prompt = f"{label}"
        if default:
            prompt += f" [{default}]"
        prompt += ": "
        
        while True:
            try:
                user_input = input(prompt).strip()
                
                if not user_input and default:
                    user_input = default
                
                # Basic Validation
                if f_type == "number":
                    try:
                        if "." in user_input:
                            val = float(user_input)
                        else:
                            val = int(user_input)
                        data[label] = val
                        break
                    except ValueError:
                        print("  Error: Please enter a valid number.")
                        continue
                        
                elif f_type == "boolean":
                    lower = user_input.lower()
                    if lower in ["y", "yes", "true", "1"]:
                        data[label] = True
                    else:
                        data[label] = False
                    break
                
                elif f_type == "select":
                    options = field.get("options", [])
                    if not options:
                        data[label] = user_input
                        break
                    
                    # If user typed an exact option match
                    if user_input in [str(o) for o in options]:
                        data[label] = user_input
                        break
                        
                    # Show Options
                    print("  Options:")
                    for idx, opt in enumerate(options):
                        print(f"  {idx+1}. {opt}")
                    
                    # If empty input and default exists
                    if not user_input and default:
                         data[label] = default
                         break
                         
                    # Try to parse index
                    try:
                        idx = int(user_input) - 1
                        if 0 <= idx < len(options):
                            data[label] = options[idx]
                            break
                    except: pass
                    
                    print(f"  Invalid selection. Please enter option text or number (1-{len(options)}).")
                    
                else:
                    # Text
                    data[label] = user_input
                    break
                    
            except EOFError:
                # Handle Ctrl+D/Z
                return {}

    print("\n[Form Submitted]")
    return data
