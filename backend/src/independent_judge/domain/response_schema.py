"""Generate required JSON output shapes from the same models used for validation."""
from pydantic import BaseModel


def items_schema(item_model: type[BaseModel], key: str) -> dict:
    item = item_model.model_json_schema()
    definitions = item.pop('$defs', {})
    root = {'type': 'object', 'properties': {key: {'type': 'array', 'items': item}},
            'required': [key], 'additionalProperties': False}
    if definitions:
        root['$defs'] = definitions

    def portable(node):
        if isinstance(node, dict):
            # Provider output grammars enforce shape; length checks remain local.
            node = {k: portable(v) for k, v in node.items()
                    if k not in ('title', 'default', 'minLength', 'maxLength', 'minItems', 'maxItems')}
            if node.get('type') == 'object':
                node['required'] = list(node.get('properties', {}))
                node['additionalProperties'] = False
        elif isinstance(node, list):
            node = [portable(v) for v in node]
        return node

    return portable(root)
