from dataclasses import dataclass
import json

commands_schema = {
    "draw_icon": {"icon": str},
    "draw_image": {"relative_path": str},
    "draw_icon_bar": {"r": int, "g": int, "b": int, "a": int},
}


def draw_icon(icon):
    return json.dumps({"command": "draw_icon", "icon": icon})


def draw_image(relative_path):
    return json.dumps({"command": "draw_image", "relative_path": relative_path})


def draw_icon_bar(red, green, blue, alpha):
    return json.dumps({"command": "draw_icon_bar", "r": red, "g": green, "b": blue, "a": alpha})


def parse(command):
    cmd = json.loads(command)
    if "command" not in cmd:
        raise ValueError(f"message does not contain a command")
    for field, expected_type in commands_schema[cmd["command"]].items():
        if field not in cmd:
            raise ValueError(f'"{cmd["command"]}" does not contain required field: "{field}"')
        if not isinstance(cmd[field], expected_type):
            raise ValueError(f'{cmd["command"]}["{field}"] must be "{type}" not "{type(cmd[field])}"')
    return cmd
