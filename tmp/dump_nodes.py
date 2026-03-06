import yaml, sys
sys.path.insert(0, r"F:\My Programs\Synapse VS")

data = yaml.safe_load(open(r'F:\My Programs\Synapse VS\sub_graphs\Bot\system\setup_bot.syp', 'r', encoding='utf-8'))
for n in data['nodes']:
    props = n.get('properties', {})
    gp = props.get('Graph Path') or props.get('graph_path') or props.get('GraphPath', '--')
    has_embed = bool(props.get('Embedded Data') or props.get('embedded_data'))
    print(f"ID:{n['id'][:8]}  TYPE:{n.get('type','?'):25s}  NAME:{n.get('name','?'):30s}  GP:{gp}  EMBED:{has_embed}")
