import jsonschema
import msgpack

control_schema = {
    "type": "object",
    "required": ["broccoli_githash", "running_floret"],
    "properties": {
        "broccoli_githash": {"type": "string"},
        "running_floret": {
            "type": "object",
            "required": ["function", "kwargs"],
            "properties": {
                "function": {"type": "string"},
                "kwargs": {"type": "object"},
            },
        },
    },
}


def decode_control_message(msg):
    decoded = msgpack.unpackb(msg, raw=False)
    try:
        jsonschema.validate(decoded, control_schema)
    except jsonschema.ValidationError as e:
        raise ValueError(e)
    return decoded
