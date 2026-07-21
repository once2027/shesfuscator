"""
Heuristic deobfuscator for shesfuscator output.

Reverses the custom Python post-processing layers:
  - Watermark removal
  - Dead code stripping (if false / while false / for _ = 1,0 / repeat until true)
  - Hex number reversal (0xHEX -> decimal)
  - String escape decoding (\\ddd -> characters)
  - Control flow reconstruction (dispatch table reorder)
  - WrapInFunction unwrapping (IIFE removal)

Does NOT reverse Prometheus engine steps (Vmify, EncryptStrings, etc.).
"""

import re

_WATERMARK = "--[[ shesfuscator v1.0 ]]"


# ─── Detection ─────────────────────────────────────────────────────────

def analyze(code: str) -> dict:
    """Detect which obfuscation layers are present in the code."""
    layers = {}
    layers["watermark"] = _WATERMARK in code
    layers["dead_code"] = _has_dead_code(code)
    layers["hex_numbers"] = bool(re.search(r"\b0x[0-9A-Fa-f]+\b", code))
    layers["string_escapes"] = bool(re.search(r'"\\[0-9]{2,}', code))
    layers["control_flow"] = bool(re.search(r"local\s+_s\s*=\s*\{", code))
    layers["wrap_in_function"] = bool(re.match(r"^\s*return\s*\(\s*function", code.strip()))
    return layers


def _has_dead_code(code: str) -> bool:
    dead_prefixes = (
        "if false then", "if nil then", "if 0 > 1 then",
        'if _VERSION == "fake" then', "while false do",
        "for _ = 1, 0 do",
    )
    for line in code.split("\n"):
        s = line.lstrip()
        if any(s.startswith(p) for p in dead_prefixes):
            return True
        if re.match(r"repeat\b.*\buntil\s+true\b", s):
            return True
    return False


# ─── Individual Reversal Functions ─────────────────────────────────────

def remove_watermark(code: str) -> str:
    """Strip the shesfuscator watermark comment."""
    return code.replace(_WATERMARK, "").lstrip("\n")


def reverse_hex_numbers(code: str) -> str:
    """Convert 0xHEX literals back to decimal."""
    def _from_hex(m):
        try:
            return str(int(m.group(0), 16))
        except ValueError:
            return m.group(0)
    return re.sub(r"\b0x[0-9A-Fa-f]+\b", _from_hex, code)


def decode_string_escapes(code: str) -> str:
    r"""Convert \ddd decimal escape sequences in strings back to characters."""
    def _decode_match(m):
        content = m.group(0)
        try:
            decoded = bytes(
                int(n) for n in re.findall(r"\\(\d+)", content)
            ).decode("utf-8", errors="replace")
            return '"' + decoded.replace("\\", "\\\\").replace('"', '\\"') + '"'
        except Exception:
            return content
    return re.sub(r'"(?:[^"\\]|\\.)*"', _decode_match, code)


def remove_dead_code(code: str) -> str:
    """Remove unreachable blocks injected by the DeadCode method.

    Handles single-line and multi-line dead blocks:
      - if false then ... end
      - if nil then ... end
      - if 0 > 1 then ... end
      - if _VERSION == "fake" then ... end
      - while false do ... end
      - for _ = 1, 0 do ... end
      - repeat ... until true
    """
    lines = code.split("\n")
    dead_prefixes = (
        "if false then", "if nil then", "if 0 > 1 then",
        "if _VERSION == \"fake\" then", "while false do",
        "for _ = 1, 0 do",
    )
    result = []
    skip_indent = -1

    for line in lines:
        if skip_indent >= 0:
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            if indent <= skip_indent and stripped.startswith("end"):
                skip_indent = -1
            continue

        stripped = line.lstrip()

        if any(stripped.startswith(p) for p in dead_prefixes):
            if stripped.endswith("end"):
                continue
            skip_indent = len(line) - len(stripped)
            continue

        if re.match(r"repeat\b.*\buntil\s+true\b", stripped):
            continue

        result.append(line)

    return "\n".join(result)


def reverse_control_flow(code: str) -> str:
    """Detect dispatch-table flattening, strip scaffolding, reorder blocks.

    The obfuscator produces:
        local _s = {N1, N2, N3}
        local _d = _s[math.random(1, #_s)]
        if _d == N1 then
          <block 1>
        end
        if _d == N2 then
          <block 2>
        end
        ...

    This extracts the blocks, strips the scaffolding, and returns them
    sorted by case number (original code order).
    """
    lines = code.split("\n")

    dispatch_idx = None
    dispatch_nums = []
    for i, line in enumerate(lines):
        m = re.match(r"local\s+_s\s*=\s*\{(.+)\}\s*$", line.strip())
        if m:
            dispatch_idx = i
            dispatch_nums = [
                int(n.strip()) for n in m.group(1).split(",") if n.strip().isdigit()
            ]
            break

    if dispatch_idx is None or not dispatch_nums:
        return code

    dispatch_var_idx = None
    for i in range(dispatch_idx + 1, min(dispatch_idx + 3, len(lines))):
        if re.match(r"\s*local\s+_d\s*=\s*_s\[", lines[i]):
            dispatch_var_idx = i
            break

    if dispatch_var_idx is None:
        return code

    skip = {dispatch_idx, dispatch_var_idx}

    cases = []
    i = 0
    while i < len(lines):
        if i in skip:
            i += 1
            continue

        m = re.match(r"\s*if\s+_d\s*==\s*(\d+)\s+then\s*$", lines[i])
        if m:
            case_num = int(m.group(1))
            indent = len(lines[i]) - len(lines[i].lstrip())
            block_lines = []
            i += 1
            depth = 1
            while i < len(lines) and depth > 0:
                stripped = lines[i].lstrip()
                cur_indent = len(lines[i]) - len(stripped)
                if stripped == "end" and cur_indent <= indent:
                    depth -= 1
                    if depth == 0:
                        i += 1
                        break
                elif re.match(r"\bif\b.*\bthen\b", stripped):
                    depth += 1
                block_lines.append(lines[i])
                i += 1
            if block_lines:
                common = min(
                    (len(bl) - len(bl.lstrip()) for bl in block_lines if bl.strip()),
                    default=0,
                )
                block_lines = [bl[common:] if len(bl) > common else bl for bl in block_lines]
            cases.append((case_num, block_lines))
        else:
            i += 1

    if not cases:
        return code

    cases.sort(key=lambda c: c[0])
    result = []
    for _, block in cases:
        result.extend(block)

    return "\n".join(result)


def unwrap_wrap_in_function(code: str) -> str:
    """Unwrap IIFE: return(function(...) ... end)(...) -> ... end"""
    code = code.strip()
    m = re.match(
        r"^return\s*\(\s*function\s*\(\s*\.\.\.\s*\)\s*(.*)\s*\)\s*\(\s*\.\.\.\s*\)\s*$",
        code,
        re.DOTALL,
    )
    if m:
        inner = m.group(1).strip()
        if inner.endswith(")"):
            inner = inner[:-1].strip()
        if inner.endswith("end"):
            inner = inner[:-3].strip()
        return inner
    return code


# ─── Pipeline ──────────────────────────────────────────────────────────

def deobfuscate(source: str) -> tuple[str, dict]:
    """Run the heuristic deobfuscation pipeline.

    Returns (deobfuscated_code, layers_reversed) where layers_reversed
    is a dict of booleans indicating which layers were detected and removed.

    Order matters:
    1. Watermark removal
    2. Dead code cleanup (before hex, as dead blocks may contain hex numbers)
    3. Hex reversal (converts 0xHH to decimal in string escapes)
    4. String escape decoding (\\ddd -> characters, must be after hex reversal)
    5. Control flow reconstruction (strip scaffolding, reorder blocks)
    6. WrapInFunction unwrapping (strip IIFE wrapper — re-detected after CF)
    """
    layers = analyze(source)
    code = source

    if layers["watermark"]:
        code = remove_watermark(code)
    if layers["dead_code"]:
        code = remove_dead_code(code)
    if layers["hex_numbers"]:
        code = reverse_hex_numbers(code)
    if layers["string_escapes"]:
        code = decode_string_escapes(code)
    if layers["control_flow"]:
        code = reverse_control_flow(code)
        # Re-analyze: WrapInFunction may be hidden inside dispatch blocks
        if not layers.get("wrap_in_function"):
            post_layers = analyze(code)
            layers["wrap_in_function"] = post_layers.get("wrap_in_function", False)
    if layers.get("wrap_in_function"):
        code = unwrap_wrap_in_function(code)

    return code, layers
