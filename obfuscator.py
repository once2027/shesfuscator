"""
Bridge between Python and the Prometheus Lua obfuscator + custom post-processing layers.

Runs the Prometheus CLI via subprocess, then applies additional Python-based
obfuscation transformations on the output.
"""

import os
import random
import re
import subprocess
import tempfile

_PROMETHEUS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Prometheus-master")
_LUAJIT = "luajit"
_CLI = os.path.join(_PROMETHEUS_DIR, "cli.lua")

# ─── Prometheus Steps ─────────────────────────────────────────────────

ALL_PROMETHEUS_STEPS = (
    "Vmify",
    "EncryptStrings",
    "AntiTamper",
    "ConstantArray",
    "NumbersToExpressions",
    "WrapInFunction",
    "SplitStrings",
    "ProxifyLocals",
    "AddVararg",
)

STEP_SETTINGS = {
    "Vmify": {},
    "EncryptStrings": {},
    "AntiTamper": {"UseDebug": False},
    "ConstantArray": {
        "Threshold": 1, "StringsOnly": True, "Shuffle": True,
        "Rotate": True, "LocalWrapperThreshold": 0,
    },
    "NumbersToExpressions": {},
    "WrapInFunction": {},
    "SplitStrings": {},
    "ProxifyLocals": {},
    "AddVararg": {},
}

PRESETS = {
    "Very Light": {
        "steps": ["ConstantArray"],
        "custom": [],
    },
    "Light": {
        "steps": ["ConstantArray", "WrapInFunction"],
        "custom": ["HexNumbers"],
    },
    "Medium": {
        "steps": ["EncryptStrings", "ConstantArray", "WrapInFunction"],
        "custom": ["HexNumbers", "StringEncoder"],
    },
    "Medium-High": {
        "steps": ["EncryptStrings", "AntiTamper", "Vmify", "ConstantArray", "WrapInFunction"],
        "custom": ["HexNumbers", "StringEncoder", "BoolWrap"],
    },
    "High": {
        "steps": ["EncryptStrings", "AntiTamper", "Vmify", "ConstantArray", "NumbersToExpressions", "WrapInFunction"],
        "custom": ["HexNumbers", "StringEncoder", "VarRenamer", "BoolWrap"],
    },
    "Very High": {
        "steps": ["Vmify", "EncryptStrings", "AntiTamper", "ConstantArray", "NumbersToExpressions", "WrapInFunction"],
        "custom": ["HexNumbers", "StringEncoder", "VarRenamer", "DeadCode", "BoolWrap", "Watermark"],
    },
    "Ultra": {
        "steps": ["Vmify", "EncryptStrings", "AntiTamper", "Vmify", "ConstantArray", "NumbersToExpressions", "WrapInFunction"],
        "custom": ["HexNumbers", "StringEncoder", "VarRenamer", "DeadCode", "BoolWrap", "NegateBools", "NoiseVars", "Watermark"],
    },
}

PRESET_NAMES = list(PRESETS.keys())

# ─── Custom Post-Processing Methods ───────────────────────────────────

ALL_CUSTOM_METHODS = (
    "StringEncoder",
    "VarRenamer",
    "DeadCode",
    "HexNumbers",
    "Watermark",
    "BoolWrap",
    "NegateBools",
    "NoiseVars",
)

CUSTOM_METHOD_INFO = {
    "StringEncoder": {
        "short": "Encode strings as decimal escapes",
        "desc": "Converts string literals to \\ddd escape sequences like WeAreDevs style.",
        "perf": "Low",
    },
    "VarRenamer": {
        "short": "Rename local variables",
        "desc": "Renames local variable declarations to confusing lookalike characters.",
        "perf": "Low",
    },
    "DeadCode": {
        "short": "Inject dead code blocks",
        "desc": "Inserts random unreachable if/while blocks after end statements.",
        "perf": "Low",
    },
    "HexNumbers": {
        "short": "Convert numbers to hex",
        "desc": "Converts numeric literals to 0xHEX format.",
        "perf": "None",
    },
    "Watermark": {
        "short": "Add watermark comment",
        "desc": "Embeds a hidden watermark in the output.",
        "perf": "None",
    },
    "BoolWrap": {
        "short": "Wrap booleans in expressions",
        "desc": "Converts true/false to (1==1)/(1==0).",
        "perf": "None",
    },
    "NegateBools": {
        "short": "Negate boolean literals",
        "desc": "Converts true to not false, false to not true.",
        "perf": "None",
    },
    "NoiseVars": {
        "short": "Inject random variables",
        "desc": "Adds unused local variable assignments after end statements.",
        "perf": "None",
    },
}


# ─── Prometheus CLI ───────────────────────────────────────────────────

def _build_config_lua(steps: list[str]) -> str:
    step_entries = []
    for name in steps:
        settings = STEP_SETTINGS.get(name, {})
        if settings:
            s = ", ".join(f"{k} = {_lua_lit(v)}" for k, v in settings.items())
            step_entries.append(f'        {{ Name = "{name}", Settings = {{ {s} }} }}')
        else:
            step_entries.append(f'        {{ Name = "{name}", Settings = {{}} }}')
    body = ",\n".join(step_entries)
    return f"""return {{
    LuaVersion = "Luau",
    VarNamePrefix = "",
    NameGenerator = "MangledShuffled",
    PrettyPrint = false,
    Seed = 0,
    Steps = {{
{body}
    }},
}}
"""


def _lua_lit(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        return f'"{v}"'
    if isinstance(v, list):
        return "{ " + ", ".join(_lua_lit(x) for x in v) + " }"
    return str(v)


def _run_cli(args: list[str], source: str) -> str:
    with tempfile.TemporaryDirectory(prefix="shesfuscator_") as tmp:
        in_path = os.path.join(tmp, "input.lua")
        out_path = os.path.join(tmp, "output.lua")
        with open(in_path, "w", encoding="utf-8") as f:
            f.write(source)
        cmd = [_LUAJIT, _CLI, "--LuaU", "--nocolors", "--out", out_path] + args + [in_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=_PROMETHEUS_DIR)
        if result.returncode != 0:
            err = result.stderr.strip()
            if any(k in err.lower() for k in ("parse", "syntax", "unexpected")):
                raise SyntaxError(err)
            raise RuntimeError(f"Prometheus error (exit {result.returncode}):\n{err}")
        if not os.path.exists(out_path):
            raise RuntimeError("Prometheus produced no output.")
        with open(out_path, "r", encoding="utf-8") as f:
            return f.read()


# ─── Custom Obfuscation Layers ────────────────────────────────────────

def _encode_strings(code: str) -> str:
    """Encode string literals as decimal escape sequences (WeAreDevs style)."""
    def _encode_match(m):
        s = m.group(1)
        if not s or len(s) < 2:
            return m.group(0)
        encoded = "".join(f"\\{ord(c):03d}" for c in s)
        return f'"{encoded}"'

    return re.sub(r'"((?:[^"\\]|\\.)*)"', _encode_match, code)


def _rename_vars(code: str) -> str:
    """Rename local variable declarations to confusing lookalike characters."""
    confusing = list("Il1Oo0")
    used = set()
    mapping = {}

    def _gen_name():
        while True:
            length = random.randint(2, 5)
            name = "".join(random.choices(confusing, k=length))
            if name not in used and not name[0].isdigit():
                used.add(name)
                return name

    lua_keywords = {
        "and", "break", "do", "else", "elseif", "end", "false", "for",
        "function", "if", "in", "local", "nil", "not", "or", "repeat",
        "return", "then", "true", "until", "while", "continue",
        "print", "typeof", "type", "tostring", "tonumber", "pairs",
        "ipairs", "next", "select", "unpack", "pcall", "xpcall",
        "error", "assert", "require", "game", "workspace", "script",
        "self", "_G", "_ENV",
    }

    for m in re.finditer(r"\blocal\s+(\w+)\s*[=,]", code):
        name = m.group(1)
        if name in lua_keywords or name.startswith("_") or len(name) <= 1:
            continue
        if name not in mapping:
            mapping[name] = _gen_name()

    for m in re.finditer(r"\bfunction\s+(\w+)\s*\(", code):
        name = m.group(1)
        if name in lua_keywords or name.startswith("_") or len(name) <= 1:
            continue
        if name not in mapping:
            mapping[name] = _gen_name()

    for old, new in sorted(mapping.items(), key=lambda x: -len(x[0])):
        code = re.sub(r"\b" + re.escape(old) + r"\b", new, code)

    return code


def _inject_dead_code(code: str) -> str:
    """Inject random unreachable code blocks after 'end' statements."""
    fake_blocks = [
        'if false then local _d = 1 end',
        'if nil then local _d = 2 end',
        'if 0 > 1 then local _d = 3 end',
        'while false do local _d = 4 end',
        'for _ = 1, 0 do local _d = 5 end',
    ]

    lines = code.split("\n")
    result = []
    for line in lines:
        result.append(line)
        stripped = line.strip()
        if stripped == "end" and random.random() < 0.2:
            result.append("  " + random.choice(fake_blocks))
    return "\n".join(result)


def _hex_numbers(code: str) -> str:
    """Convert decimal number literals to hex."""
    def _to_hex(m):
        num = int(m.group(0))
        if num > 9 and random.random() < 0.7:
            return f"0x{num:X}"
        return m.group(0)

    return re.sub(r"\b(\d{2,})\b", _to_hex, code)


def _add_watermark(code: str) -> str:
    """Add a watermark comment."""
    wm = "--[[ made tuffer by shesfuscator v1 ]] "
    if wm.strip() not in code:
        code = wm + code
    return code


def _wrap_bools(code: str) -> str:
    """Wrap boolean literals in expressions: true -> (1==1), false -> (1==0)."""
    code = re.sub(r"\btrue\b", "(1==1)", code)
    code = re.sub(r"\bfalse\b", "(1==0)", code)
    return code


def _negate_bools(code: str) -> str:
    """Negate boolean literals: true -> (not false), false -> (not true)."""
    def _negate(m):
        if m.group(0) == "true":
            return "(not false)"
        return "(not true)"

    return re.sub(r"\b(true|false)\b", _negate, code)


def _inject_noise_vars(code: str) -> str:
    """Inject unused local variable assignments after 'end' statements."""
    noise_vars = [
        "local _n = math.random(1,999)",
        "local _s = tostring(math.random())",
        "local _t = tick and tick() or 0",
        "local _w = #\"noise\"",
        "local _z = typeof(nil)",
    ]

    lines = code.split("\n")
    result = []
    for line in lines:
        result.append(line)
        stripped = line.strip()
        if stripped == "end" and random.random() < 0.2:
            result.append("  " + random.choice(noise_vars))
    return "\n".join(result)


_CUSTOM_METHODS_MAP = {
    "StringEncoder": _encode_strings,
    "VarRenamer": _rename_vars,
    "DeadCode": _inject_dead_code,
    "HexNumbers": _hex_numbers,
    "Watermark": _add_watermark,
    "BoolWrap": _wrap_bools,
    "NegateBools": _negate_bools,
    "NoiseVars": _inject_noise_vars,
}


# ─── Public API ───────────────────────────────────────────────────────

def get_preset_steps(preset: str) -> list[str]:
    return list(PRESETS.get(preset, {}).get("steps", []))


def get_preset_custom(preset: str) -> list[str]:
    return list(PRESETS.get(preset, {}).get("custom", []))


def obfuscate_custom(
    source: str,
    steps: list[str],
    custom_methods: list[str] | None = None,
) -> str:
    """Obfuscate with custom Prometheus steps + optional custom post-processing."""
    for s in steps:
        if s not in STEP_SETTINGS:
            raise ValueError(f"Unknown step {s!r}. Valid: {', '.join(ALL_PROMETHEUS_STEPS)}")
    config_lua = _build_config_lua(steps)
    with tempfile.TemporaryDirectory(prefix="shesfuscator_") as tmp:
        config_path = os.path.join(tmp, "config.lua")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(config_lua)
        result = _run_cli(["--config", config_path], source)
    return _apply_custom(result, custom_methods)


def _apply_custom(code: str, methods: list[str] | None) -> str:
    if not methods:
        return code
    for m in methods:
        fn = _CUSTOM_METHODS_MAP.get(m)
        if fn:
            code = fn(code)
    return code
