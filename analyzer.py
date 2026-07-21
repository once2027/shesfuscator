"""
Simple regex-based Luau code analyzer.

Parses common patterns to give a human-readable explanation of what a script does.
No external dependencies — pure regex + heuristics.
"""

import re
from collections import Counter


def _find_pattern(code: str, pattern: str) -> list[re.Match]:
    return list(re.finditer(pattern, code, re.IGNORECASE | re.MULTILINE))


def _count_pattern(code: str, pattern: str) -> int:
    return len(_find_pattern(code, pattern))


def analyze(code: str) -> dict:
    """Analyze Luau code and return structured info."""
    lines = code.strip().split("\n")
    non_empty = [l for l in lines if l.strip() and not l.strip().startswith("--")]
    total_lines = len(lines)
    code_lines = len(non_empty)

    # Functions
    funcs_named = _find_pattern(code, r"\bfunction\s+(\w+(?:\.\w+)*)\s*\(")
    funcs_anon = _count_pattern(code, r"\bfunction\s*\(")
    funcs_local = _count_pattern(code, r"\blocal\s+function\b")
    func_names = [m.group(1) for m in funcs_named]

    # Variables
    locals_count = _count_pattern(code, r"\blocal\s+\w+")
    globals_count = _count_pattern(code, r"^(?!\s*local\b)\s*(\w+)\s*=")

    # Control flow
    ifs = _count_pattern(code, r"\bif\b")
    loops = _count_pattern(code, r"\b(for|while|repeat)\b")
    switches = _count_pattern(code, r"\belseif\b")

    # Roblox API calls
    roblox_patterns = {
        "game:GetService": r"game:GetService\([\"'](\w+)[\"']\)",
        "game.Workspace": r"\bworkspace\b",
        "game.Players": r"\bPlayers\b",
        "Instance.new": r"Instance\.new\([\"'](\w+)[\"']\)",
        "RemoteEvent": r"RemoteEvent",
        "RemoteFunction": r"RemoteFunction",
        "BindableEvent": r"BindableEvent",
        "HttpService": r"HttpService",
        "TweenService": r"TweenService",
        "RunService": r"RunService",
        "UserInputService": r"UserInputService",
        "MarketplaceService": r"MarketplaceService",
        "DataStoreService": r"DataStoreService",
        "PhysicsService": r"PhysicsService",
        "Sound": r"\bSound\b",
        "Part": r"\bPart\b",
        "Script": r"\bScript\b",
        "LocalScript": r"\bLocalScript\b",
        "ModuleScript": r"\bModuleScript\b",
    }

    services_used = []
    for name, pat in roblox_patterns.items():
        matches = _find_pattern(code, pat)
        if matches:
            services_used.append(name)

    # Instances created
    instances_created = []
    for m in _find_pattern(code, r"Instance\.new\([\"'](\w+)[\"']\)"):
        instances_created.append(m.group(1))

    # Connections (events)
    events = _count_pattern(code, r"\.Connect\s*\(")

    # Metatables
    metatables = _count_pattern(code, r"getmetatable|setmetatable|__index|__newindex|__call")

    # String operations
    strings = _count_pattern(code, r'"[^"]*"|\'[^\']*\'')

    # Numbers
    numbers = _count_pattern(code, r"\b\d+\.?\d*\b")

    # Comments
    comments = _count_pattern(code, r"--")
    block_comments = _count_pattern(code, r"--\[\[")

    # Imports / requires
    requires = _find_pattern(code, r"\brequire\s*\([\"']?([^)\"']+)[\"']?\)")

    # Complexity indicators
    nested_depth = 0
    max_depth = 0
    for line in lines:
        stripped = line.strip()
        if re.match(r"(if|for|while|function|repeat)\b", stripped):
            nested_depth += 1
            max_depth = max(max_depth, nested_depth)
        if stripped == "end":
            nested_depth = max(0, nested_depth - 1)

    return {
        "lines_total": total_lines,
        "lines_code": code_lines,
        "functions": len(funcs_named),
        "func_names": func_names,
        "anon_functions": funcs_anon,
        "local_functions": funcs_local,
        "locals": locals_count,
        "globals": globals_count,
        "ifs": ifs,
        "loops": loops,
        "switches": switches,
        "services": services_used,
        "instances": instances_created,
        "events": events,
        "metatables": metatables,
        "strings": strings,
        "numbers": numbers,
        "comments": comments,
        "block_comments": block_comments,
        "requires": [m.group(1) for m in requires],
        "max_depth": max_depth,
    }


def explain(code: str) -> str:
    """Return a human-readable explanation of the code."""
    info = analyze(code)

    parts = []

    # Overview
    size = "tiny" if info["lines_code"] < 10 else "small" if info["lines_code"] < 50 else "medium" if info["lines_code"] < 200 else "large" if info["lines_code"] < 500 else "very large"
    parts.append(f"This is a **{size}** Luau script ({info['lines_code']} lines of code, {info['lines_total']} total lines).")

    # Functions
    if info["functions"] > 0:
        names = ", ".join(f"`{n}`" for n in info["func_names"][:8])
        extra = f" (+ {info['functions'] - 8} more)" if info["functions"] > 8 else ""
        parts.append(f"Defines **{info['functions']} function(s)**: {names}{extra}")
    if info["anon_functions"] > 0:
        parts.append(f"Has **{info['anon_functions']} anonymous function(s)** (closures/lambdas).")

    # Variables
    if info["locals"] > 0 or info["globals"] > 0:
        parts.append(f"Uses **{info['locals']} local variable(s)** and **{info['globals']} global assignment(s)**.")

    # Control flow
    flow = []
    if info["ifs"]:
        flow.append(f"{info['ifs']} if/elseif")
    if info["loops"]:
        flow.append(f"{info['loops']} loop(s)")
    if flow:
        parts.append(f"Control flow: {', '.join(flow)} (max nesting depth: {info['max_depth']}).")

    # Roblox specifics
    if info["services"]:
        svc = ", ".join(f"`{s}`" for s in info["services"][:6])
        parts.append(f"Uses Roblox services: {svc}.")

    if info["instances"]:
        counts = Counter(info["instances"])
        inst = ", ".join(f"{n}x `{t}`" for t, n in counts.most_common(5))
        parts.append(f"Creates instances: {inst}.")

    if info["events"]:
        parts.append(f"Has **{info['events']} event connection(s)** (`.Connect`).")

    if info["metatables"]:
        parts.append(f"Uses **metatables** ({info['metatables']} occurrence(s)) — likely OOP or proxy patterns.")

    # Requires
    if info["requires"]:
        reqs = ", ".join(f"`{r}`" for r in info["requires"][:5])
        parts.append(f"Requires: {reqs}.")

    # Style observations
    style = []
    if info["comments"] > 3:
        style.append(f"well-commented ({info['comments']} comments)")
    if info["strings"] > 20:
        style.append(f"string-heavy ({info['strings']} string literals)")
    if info["numbers"] > 15:
        style.append(f"number-heavy ({info['numbers']} numeric literals)")
    if style:
        parts.append(f"Style: {', '.join(style)}.")

    # Likely purpose
    purpose = _guess_purpose(info, code)
    if purpose:
        parts.append(f"**Likely purpose:** {purpose}")

    return "\n\n".join(parts)


def _guess_purpose(info: dict, code: str) -> str:
    code_lower = code.lower()

    hints = []

    # GUI
    if any(k in code_lower for k in ["screenGui", "frame", "textlabel", "textbutton", "uistroke", "tweeninfo"]):
        hints.append("GUI/interface")

    # Combat
    if any(k in code_lower for k in ["health", "damage", "kill", "hit", "weapon", "sword", "gun"]):
        hints.append("combat/gameplay")

    # Admin
    if any(k in code_lower for k in ["ban", "kick", "admin", "moderator", "权限"]):
        hints.append("admin system")

    # Data
    if any(k in code_lower for k in ["datastore", "save", "load", "data", "leaderstats"]):
        hints.append("data persistence")

    # Networking
    if any(k in code_lower for k in ["remoteevent", "remotefunction", "fireserver", "onclientevent"]):
        hints.append("client-server networking")

    # Animation
    if any(k in code_lower for k in ["animate", "animation", "animator", "loadanimation"]):
        hints.append("animation")

    # Physics
    if any(k in code_lower for k in ["bodyvelocity", "bodyposition", "attachment", "constraint", "vectorforce"]):
        hints.append("physics/movement")

    # UI scripting
    if "localplayer" in code_lower or "mouse" in code_lower or "input" in code_lower:
        hints.append("player input handling")

    # Module
    if info["func_names"] and not info["events"]:
        hints.append("utility/module library")

    if hints:
        return ", ".join(hints[:3])
    return ""
