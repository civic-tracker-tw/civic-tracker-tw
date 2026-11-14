"""
Pure Python lightweight YAML subset parser.
Falls back to PyYAML if available; otherwise parses standard YAML structures
including nested dicts, lists of scalars, and lists of dicts.
"""

from typing import Any, List, Tuple, Union


def _strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    for i, ch in enumerate(line):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == '#' and not in_single and not in_double:
            return line[:i].rstrip()
    return line.rstrip()


def _parse_scalar(val: str) -> Any:
    val = val.strip()
    if not val:
        return ""
    # Quoted strings
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        return val[1:-1]
    # Booleans
    lower = val.lower()
    if lower in ("true", "yes", "on"):
        return True
    if lower in ("false", "no", "off"):
        return False
    if lower in ("null", "none", "~"):
        return None
    # Int
    try:
        if val.startswith("0") and len(val) > 1 and not val.startswith("0."):
            pass  # preserve leading zeroes as string if any
        else:
            return int(val)
    except ValueError:
        pass
    # Float
    try:
        return float(val)
    except ValueError:
        pass
    return val


def _split_key_val(line_text: str) -> Tuple[str, Union[str, None]]:
    in_single = False
    in_double = False
    for i, ch in enumerate(line_text):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == ':' and not in_single and not in_double:
            key = line_text[:i].strip()
            rest = line_text[i + 1:].strip()
            return key, rest
    return line_text.strip(), None


def _parse_tokens(lines: List[Tuple[int, int, str]], start: int, base_indent: int) -> Tuple[Any, int]:
    """
    Parses a block of tokens starting at index `start` with indent >= `base_indent`.
    Returns (parsed_object, next_index).
    """
    if start >= len(lines):
        return None, start

    _, indent, content = lines[start]
    if indent < base_indent:
        return None, start

    is_list = content.startswith("- ") or content == "-"

    if is_list:
        items = []
        i = start
        while i < len(lines):
            _, cur_indent, cur_text = lines[i]
            if cur_indent < indent:
                break
            if cur_indent > indent:
                # Sub-block inside current item; already handled in item parsing
                break
            if not (cur_text.startswith("- ") or cur_text == "-"):
                break

            remainder = cur_text[2:].strip() if cur_text.startswith("- ") else ""
            if not remainder:
                # Following lines at cur_indent + 2 belong to this list item
                nested, next_i = _parse_tokens(lines, i + 1, cur_indent + 1)
                items.append(nested)
                i = next_i
            elif ":" in remainder:
                # First field of a dict item in a list!
                # e.g. - id: "foo"
                #      name: "bar"
                dict_item = {}
                key, val = _split_key_val(remainder)
                if val:
                    dict_item[key] = _parse_scalar(val)
                    next_i = i + 1
                else:
                    # Nested block under this key
                    val_obj, next_i = _parse_tokens(lines, i + 1, cur_indent + 2)
                    dict_item[key] = val_obj

                # Collect subsequent sibling keys for this dict item
                # They will have indent >= cur_indent + 2 (usually cur_indent + 2 or 4)
                while next_i < len(lines):
                    _, sub_indent, sub_text = lines[next_i]
                    if sub_indent <= cur_indent:
                        break
                    if sub_text.startswith("- ") and sub_indent <= cur_indent + 2:
                        break
                    sub_key, sub_val = _split_key_val(sub_text)
                    if sub_val is not None and sub_val != "":
                        dict_item[sub_key] = _parse_scalar(sub_val)
                        next_i += 1
                    else:
                        sub_obj, after_i = _parse_tokens(lines, next_i + 1, sub_indent + 1)
                        dict_item[sub_key] = sub_obj
                        next_i = after_i
                items.append(dict_item)
                i = next_i
            else:
                # Simple scalar item
                items.append(_parse_scalar(remainder))
                i += 1
        return items, i

    else:
        # Mapping
        result_dict = {}
        i = start
        while i < len(lines):
            _, cur_indent, cur_text = lines[i]
            if cur_indent < indent:
                break
            if cur_indent > indent:
                break
            if cur_text.startswith("- "):
                break

            key, val = _split_key_val(cur_text)
            if val is not None and val != "":
                result_dict[key] = _parse_scalar(val)
                i += 1
            else:
                # Nested block follows
                nested_obj, next_i = _parse_tokens(lines, i + 1, cur_indent + 1)
                result_dict[key] = nested_obj
                i = next_i
        return result_dict, i


def parse_yaml_subset(yaml_content: str) -> Any:
    raw_lines = yaml_content.splitlines()
    processed: List[Tuple[int, int, str]] = []
    for idx, line in enumerate(raw_lines):
        stripped = _strip_comment(line)
        if not stripped.strip():
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        processed.append((idx, indent, stripped.strip()))

    if not processed:
        return {}

    parsed, _ = _parse_tokens(processed, 0, processed[0][1])
    return parsed


def load_yaml(content_or_path: str) -> Any:
    """
    Parses YAML from string content or file path.
    Uses PyYAML if installed; otherwise uses parse_yaml_subset.
    """
    try:
        import yaml
        has_pyyaml = True
    except ImportError:
        has_pyyaml = False

    text = content_or_path
    import os
    if os.path.exists(content_or_path) and os.path.isfile(content_or_path):
        with open(content_or_path, "r", encoding="utf-8") as f:
            text = f.read()

    if has_pyyaml:
        return yaml.safe_load(text)
    return parse_yaml_subset(text)
