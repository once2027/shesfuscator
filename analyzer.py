"""
Deep Luau static analyzer — no external APIs.

Provides semantic analysis, section breakdown, security audit,
obfuscation detection, and purpose inference for Luau/Roblox scripts.
"""

import re
import math
from collections import Counter


# ─── Roblox API Knowledge Base ────────────────────────────────────────

API_DOCS = {
    # Services
    "game:GetService": "Accesses a Roblox service by name (e.g. Players, Workspace, ReplicatedStorage).",
    "game:FindService": "Safely accesses a Roblox service (returns nil if missing instead of erroring).",
    "workspace": "The Workspace service — contains all 3D objects (parts, models, terrain).",
    "Players": "The Players service — manages connected players and their characters.",
    "ReplicatedStorage": "Shared storage between client and server (LocalScripts can read, can't write).",
    "ServerScriptService": "Server-only storage — scripts here run on the server.",
    "ServerStorage": "Server-only storage not accessible from client.",
    "StarterGui": "Contains GUI templates copied to each player's PlayerGui on join.",
    "StarterPack": "Contains tools copied to each player's Backpack on join.",
    "StarterPlayer": "Contains StarterCharacterScripts and StarterPlayerScripts.",
    "Lighting": "The Lighting service — controls atmosphere, sky, post-processing effects.",
    "TweenService": "Creates smooth property animations (tweens) over time.",
    "RunService": "Provides Heartbeat/RenderStepped/Stepped events for per-frame logic.",
    "UserInputService": "Detects keyboard, mouse, touch, and gamepad input.",
    "HttpService": "Makes HTTP requests to external web APIs (server-only, must be enabled).",
    "DataStoreService": "Persistent key-value storage for saving player data across sessions.",
    "MarketplaceService": "Handles game passes, products, and asset purchases.",
    "PhysicsService": "Controls collision groups and physics settings.",
    "SoundService": "Manages ambient/global sounds.",
    "Chat": "The Chat service — handles bubble chat and chat messages.",
    "Teams": "Manages teams and team assignment.",
    "CollectionService": "Tags objects for group management.",
    "PathfindingService": "NPC pathfinding around obstacles.",
    "ProximityPromptService": "Creates proximity-based interaction prompts.",
    "VRService": "VR headset support.",
    "SocialService": "Friend requests and social features.",
    "TeleportService": "Teleports players between places/servers.",
    "TextChatService": "Modern chat system (RichText).",
    "LocalizationService": "Translation and localization.",
    "AnalyticsService": "Game analytics and reporting.",
    "BadgeService": "Award and check badges.",
    "GroupService": "Access player group info.",
    "FriendsService": "Player friend lists.",
    "CharacterAppearance": "Player avatar customization.",

    # Instance.new targets
    "Part": "A basic 3D building block — a rectangular prism by default.",
    "MeshPart": "A 3D part with a custom mesh shape.",
    "UnionOperation": "A boolean-merged combination of parts.",
    "TrussPart": "A structural support part (ladder-like).",
    "WedgePart": "A triangular prism part.",
    "CornerWedgePart": "A corner-cut wedge part.",
    "SpawnLocation": "A spawn point for players.",
    "Model": "A container that groups objects together.",
    "Folder": "An organizational container (no game logic).",
    "StringValue": "A string value object — holds text data.",
    "IntValue": "An integer value object.",
    "NumberValue": "A floating-point value object.",
    "BoolValue": "A boolean value object.",
    "ObjectValue": "A reference to another instance.",
    "StringValue": "Holds a string value.",
    "RemoteEvent": "Client-server communication — fires one-way messages.",
    "RemoteFunction": "Client-server communication — request/response pattern (yields).",
    "BindableEvent": "Server-to-server or client-to-client event communication.",
    "BindableFunction": "Server-to-server request/response.",
    "ScreenGui": "A 2D GUI container rendered on the player's screen.",
    "Frame": "A rectangular 2D GUI element (container or visual).",
    "TextLabel": "Displays read-only text in a GUI.",
    "TextButton": "A clickable GUI element that displays text.",
    "ImageLabel": "Displays an image in a GUI.",
    "ImageButton": "A clickable GUI element that displays an image.",
    "ScrollingFrame": "A scrollable GUI container.",
    "TextBox": "An editable text input field.",
    "UIListLayout": "Automatically arranges children in a list (vertical/horizontal).",
    "UIGridLayout": "Automatically arranges children in a grid.",
    "UIPageLayout": "Arranges children as swipeable pages.",
    "UICorner": "Rounds the corners of a GUI element.",
    "UIStroke": "Adds an outline/border to a GUI element.",
    "UIGradient": "Adds a gradient fill to a GUI element.",
    "UIPadding": "Adds padding inside a GUI element.",
    "UISizeConstraint": "Limits the size of a GUI element.",
    "UIAspectRatioConstraint": "Maintains aspect ratio on resize.",
    "BillboardGui": "A GUI element that floats above a 3D object.",
    "SurfaceGui": "A GUI element rendered on a part's surface.",
    "LocalScript": "A script that runs on the client (player's machine).",
    "Script": "A script that runs on the server.",
    "ModuleScript": "A reusable script that returns a table of functions/values.",
    "Sound": "Plays audio — 3D positional or global.",
    "ParticleEmitter": "Emits particles from a part.",
    "Fire": "A fire visual effect.",
    "Smoke": "A smoke visual effect.",
    "Sparkles": "Sparkle visual effect.",
    "Explosion": "Creates a visual and physical explosion.",
    "ForceField": "A protective energy shield around a character.",
    "BodyVelocity": "DEPRECATED — Applies velocity to a part (use VectorForce/LinearVelocity).",
    "BodyPosition": "DEPRECATED — Moves a part to a position (use AlignPosition).",
    "BodyGyro": "DEPRECATED — Orients a part (use AlignOrientation).",
    "RocketPropulsion": "DEPRECATED — Applies thrust toward a target.",
    "ClickDetector": "Detects mouse clicks on a part.",
    "Dragger": "Lets players drag parts around.",
    "AlignPosition": "Physically moves a part toward a target position.",
    "AlignOrientation": "Physically rotates a part toward a target orientation.",
    "VectorForce": "Applies a force in a direction to a part.",
    "LinearVelocity": "Applies velocity in a direction to a part.",
    "AngularVelocity": "Applies rotational velocity to a part.",
    "PrismaticConstraint": "Allows linear motion along one axis.",
    "HingeConstraint": "Allows rotation around one axis (like a door hinge).",
    "BallSocketConstraint": "Allows rotation around all axes (like a ball joint).",
    "CylindricalConstraint": "Allows both rotation and linear motion.",
    "RopeConstraint": "A flexible rope between two points.",
    "WeldConstraint": "Welds two parts together rigidly.",
    "Attachment": "A named connection point on a part.",
    "Beam": "A visual beam between two attachments.",
    "Trail": "A visual trail following a moving part.",
    "PointLight": "A light that radiates in all directions.",
    "SpotLight": "A cone-shaped light.",
    "SurfaceLight": "A light that emits from a surface.",
    "Decal": "An image applied to a part's face.",
    "Texture": "A tiled texture on a part's face.",
    "SurfaceGui": "A 2D GUI on a part's surface.",
    "Team": "Defines a team with a name and color.",
    "Region3": "An axis-aligned bounding box for spatial queries.",
}

# Common method patterns
METHOD_DOCS = {
    ":FindFirstChild": "Returns the first child with the given name (nil if not found).",
    ":FindFirstChildOfClass": "Returns the first child of the given class (nil if not found).",
    ":WaitForChild": "Yields until a child with the given name appears (hangs forever if missing!).",
    ":GetChildren": "Returns an array of all direct children.",
    ":GetDescendants": "Returns an array of all children, grandchildren, etc.",
    ":GetService": "Returns a Roblox service by class name.",
    ":Clone": "Creates a copy of the instance.",
    ":Destroy": "Removes the instance from the game permanently.",
    ":Remove": "Same as Destroy (deprecated).",
    ":SetParent": "Moves the instance to a new parent.",
    ":IsA": "Returns true if the instance inherits from the given class.",
    ":IsDescendantOf": "Returns true if the instance is inside the given ancestor.",
    ":GetPropertyChangedSignal": "Fires when a specific property changes.",
    ":Clone": "Creates a deep copy of the instance.",
    ".Connect": "Connects a function to an event — fires when the event occurs.",
    ":InvokeServer": "Calls a RemoteFunction on the server (yields until response).",
    ":FireServer": "Sends a message from client to server via RemoteEvent.",
    ":FireClient": "Sends a message from server to a specific client via RemoteEvent.",
    ":FireAllClients": "Sends a message from server to all clients via RemoteEvent.",
    ":OnClientEvent": "Listens for messages from the server (client-side RemoteEvent).",
    ":OnServerEvent": "Listens for messages from clients (server-side RemoteEvent).",
    ":OnInvoke": "Handles requests from BindableFunction (server-side).",
    ":Invoke": "Calls a BindableFunction (same-side communication).",
    ":GetAsync": "Reads data asynchronously (yields) — used by DataStore and HttpService.",
    ":SetAsync": "Writes data to DataStore (yields).",
    ":UpdateAsync": "Read-modify-write data in DataStore (yields, safer).",
    ":RemoveAsync": "Deletes a key from DataStore (yields).",
    ":GetOrderedDataStore": "Returns a sorted DataStore for pagination.",
    ":PostAsync": "Sends an HTTP POST request (yields).",
    ":RequestAsync": "Sends a custom HTTP request (yields, more control).",
    ":JSONEncode": "Converts a table to JSON string.",
    ":JSONDecode": "Converts a JSON string to a table.",
    ":UrlEncode": "URL-encodes a string.",
    ":Create": "Creates a new Tween instance.",
    ":Play": "Starts a tween animation.",
    ":Pause": "Pauses a tween.",
    ":Cancel": "Cancels a tween.",
    ":EasingStyle": "Sets the easing style (Linear, Quad, Cubic, etc.).",
    ":LoadAnimation": "Loads an Animation onto an Animator/character (deprecated, use Animator:LoadAnimation).",
    ":Play": "Plays a Sound or Animation.",
    ":Stop": "Stops a Sound or Animation.",
    ":Pause": "Pauses a Sound.",
    ":Resume": "Resumes a paused Sound.",
    ":GetMouse": "Returns the Player's Mouse object (deprecated, use UserInputService).",
    ":GetPlayers": "Returns an array of all connected players.",
    ":GetCharacter": "Returns a player's Character model.",
    ":CharacterAdded": "Fires when a player's character spawns.",
    ":CharacterRemoving": "Fires when a player's character is destroyed.",
    ":TeamColor": "The player's team color.",
    ":UserId": "The player's unique numeric ID.",
    ":Name": "The player's display name.",
    ":DisplayName": "The player's display name (can differ from Name).",
    ":AccountAge": "Days since the player joined Roblox.",
    ":LoadCharacter": "Forces a player's character to spawn.",
    ":Kick": "Kicks a player from the server with a message.",
    ":GetRankInGroup": "Returns the player's rank in a group.",
    ":GetRoleInGroup": "Returns the player's role name in a group.",
    ":IsInGroup": "Returns true if the player is in the given group.",
    ":SetCore": "Sets a core GUI element (e.g. health bar, chat).",
    ":GetCore": "Gets a core GUI element's state.",
    ":SetCoreGuiEnabled": "Enables/disables a core GUI (Health, Backpack, etc.).",
    ":RegisterTouchInterest": "Registers a part for touch events (deprecated).",
    ":GetTouchingParts": "Returns all parts currently touching this part.",
    ":Raycast": "Casts a ray and returns what it hits.",
    ":FindPartOnRay": "DEPRECATED — Raycasts from a point.",
    ":Blockcast": "Casts a box-shaped region along a direction.",
    ":Spherecast": "Casts a sphere along a direction.",
    ":Shapecast": "Casts an arbitrary shape along a direction.",
    ":GetPartBoundsInBox": "Returns all parts within a box region.",
    ":GetPartBoundsInRadius": "Returns all parts within a radius.",
    ":GetRegion3": "Returns all parts within a Region3.",
    ":SetSetting": "Saves a persistent user setting.",
    ":GetSetting": "Reads a persistent user setting.",
    ":PromptGamePassPurchase": "Prompts a player to buy a game pass.",
    ":PromptProductPurchase": "Prompts a player to buy a developer product.",
    ":PromptPurchase": "Prompts a player to buy a asset.",
    ":Signal": "Creates a custom signal (bindable event pattern).",
}

# Security-sensitive patterns
SECURITY_FLAGS = {
    "http_request": {
        "patterns": [r"HttpService", r":GetAsync", r":PostAsync", r":RequestAsync", r":GetAsync\("],
        "severity": "HIGH",
        "desc": "Makes external HTTP requests — could exfiltrate data or fetch malicious payloads.",
    },
    "remote_events": {
        "patterns": [r"RemoteEvent", r"RemoteFunction", r":FireServer", r":InvokeServer", r":OnClientEvent"],
        "severity": "MEDIUM",
        "desc": "Uses client-server remote events — potential for exploitation if inputs aren't validated.",
    },
    "datastore": {
        "patterns": [r"DataStoreService", r":GetAsync", r":SetAsync", r":UpdateAsync"],
        "severity": "MEDIUM",
        "desc": "Accesses DataStore — handles persistent player data. Ensure proper error handling.",
    },
    "loadstring": {
        "patterns": [r"loadstring\s*\(", r"pcall\s*\(\s*loadstring"],
        "severity": "CRITICAL",
        "desc": "Dynamic code execution via loadstring — massive security risk. Can execute arbitrary code.",
    },
    "require_injection": {
        "patterns": [r"require\s*\(\s*\d+", r"getfenv\s*\(", r"setfenv\s*\("],
        "severity": "HIGH",
        "desc": "Uses raw require with numeric IDs or manipulates function environments — potential exploit vector.",
    },
    "hooking": {
        "patterns": [r"hookfunction", r"hookmetamethod", r"__namecall", r"__index\s*=", r"__newindex\s*="],
        "severity": "HIGH",
        "desc": "Hooks or overrides built-in functions/metamethods — common in exploit scripts.",
    },
    "executor_detect": {
        "patterns": [r"\bsyn\b", r"\bfluxus\b", r"\bKRNL\b", r"script\.Environment", r"\bgetgenv\b", r"\bgetrenv\b", r"\bidentifyexecutor\b"],
        "severity": "CRITICAL",
        "desc": "References specific Roblox exploit executors — likely an exploit/cheat script.",
    },
    "anti_cheat_bypass": {
        "patterns": [r"bypass", r"anti.?kick", r"anti.?ban", r"noclip", r"fly.?hack", r"speed.?hack", r"teleport.?hack"],
        "severity": "CRITICAL",
        "desc": "Contains anti-cheat bypass or cheat functionality — likely malicious.",
    },
    "env_manipulation": {
        "patterns": [r"getfenv", r"setfenv", r"debug\.", r"string\.dump"],
        "severity": "HIGH",
        "desc": "Manipulates Lua environments or uses debug library — advanced exploit pattern.",
    },
}

# Obfuscation detection patterns
OBFUSCATION_SIGNATURES = {
    "string_escapes": {
        "pattern": r"\\[0-9]{3}",
        "name": "Decimal string escapes",
        "desc": "Strings encoded as \\ddd sequences (StringEncoder layer).",
    },
    "hex_numbers": {
        "pattern": r"\b0x[0-9A-Fa-f]{2,}\b",
        "name": "Hex numeric literals",
        "desc": "Numbers written in hexadecimal (HexNumbers layer).",
    },
    "confusing_vars": {
        "pattern": r"\b[Il1Oo0]{3,}\b(?![\w])",
        "name": "Confusing variable names",
        "desc": "Variables renamed to lookalike characters I/l/1/O/o/0 (VarRenamer layer).",
    },
    "dead_code": {
        "pattern": r"if\s+false\s+then|if\s+nil\s+then|while\s+false\s+do",
        "name": "Dead code blocks",
        "desc": "Unreachable code branches (DeadCode injection layer).",
    },
    "bool_wrap": {
        "pattern": r"\(1\s*==\s*1\)|\(1\s*==\s*0\)",
        "name": "Wrapped booleans",
        "desc": "Booleans replaced with comparisons (BoolWrap layer).",
    },
    "negated_bools": {
        "pattern": r"\(not\s+false\)|\(not\s+true\)",
        "name": "Negated booleans",
        "desc": "Booleans replaced with negations (NegateBools layer).",
    },
    "noise_vars": {
        "pattern": r"local\s+_[a-z]\s*=\s*(math\.random|tostring|tick|#\"|typeof)",
        "name": "Noise variable injection",
        "desc": "Unused random variable assignments (NoiseVars layer).",
    },
    "watermark": {
        "pattern": r"shesfuscator|made\s+tuffer|obfuscated\s+by",
        "name": "Obfuscation watermark",
        "desc": "Contains an obfuscation tool watermark comment.",
    },
    "base64_strings": {
        "pattern": r'"[A-Za-z0-9+/]{20,}={0,2}"',
        "name": "Base64 encoded strings",
        "desc": "Strings that appear base64-encoded — likely constant array payloads.",
    },
    "iife_wrapper": {
        "pattern": r"^\s*\(\s*function\s*\([^)]*\)\s*(?:local\s+\w+\s*=\s*[^;]+;\s*)*return\b",
        "name": "IIFE wrapper",
        "desc": "Immediately-invoked function expression wrapping the code (WrapInFunction layer).",
    },
    "vm_bytecode": {
        "pattern": r"local\s+\w+\s*=\s*\{[^}]{50,}\}\s*;\s*local\s+\w+\s*=\s*function",
        "name": "VM bytecode table",
        "desc": "Large data table followed by interpreter function — likely Vmify output.",
    },
}


# ─── Code Parsing ─────────────────────────────────────────────────────

def _split_sections(code: str) -> list[dict]:
    """Split code into logical sections (functions, blocks, comments)."""
    lines = code.split("\n")
    sections = []
    current = {"type": "code", "lines": [], "start": 1}

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Block comment
        if stripped.startswith("--[[") or stripped.startswith("--[=["):
            end_marker = "]]" if "[[" in stripped else "]=]"
            if end_marker in stripped and stripped.index(end_marker) > 4:
                sections.append({"type": "comment", "text": stripped, "start": i + 1})
                i += 1
                continue
            # Multi-line comment
            comment_lines = [line]
            while i < len(lines) and end_marker not in lines[i]:
                i += 1
                if i < len(lines):
                    comment_lines.append(lines[i])
            sections.append({"type": "comment", "text": "\n".join(comment_lines), "start": i + 1 - len(comment_lines) + 1})
            i += 1
            continue

        # Single-line comment
        if stripped.startswith("--"):
            sections.append({"type": "comment", "text": stripped, "start": i + 1})
            i += 1
            continue

        # Function definition
        func_match = re.match(r"(?:local\s+)?function\s+(\w+(?:[.:]\w+)*)\s*\(([^)]*)\)", stripped)
        if func_match:
            func_name = func_match.group(1)
            params = func_match.group(2).strip()
            func_lines = [line]
            depth = 1
            while i + 1 < len(lines) and depth > 0:
                i += 1
                func_lines.append(lines[i])
                inner = lines[i].strip()
                if re.match(r"(?:local\s+)?function\b", inner):
                    depth += 1
                elif inner == "end":
                    depth -= 1
            sections.append({
                "type": "function",
                "name": func_name,
                "params": params,
                "text": "\n".join(func_lines),
                "start": i + 1 - len(func_lines) + 1,
                "line_count": len(func_lines),
            })
            i += 1
            continue

        # Regular code
        current["lines"].append(line)
        i += 1

    if current["lines"]:
        sections.append({"type": "code", "text": "\n".join(current["lines"]), "start": current["start"]})

    return sections


def _analyze_function_body(body: str) -> dict:
    """Analyze a single function's body for what it does."""
    findings = []
    code_lower = body.lower()

    # API calls in this function
    api_calls = set()
    for api_name in API_DOCS:
        if api_name in body:
            api_calls.add(api_name)

    # Method calls
    methods = set()
    for method_name in METHOD_DOCS:
        if method_name in body:
            methods.add(method_name)

    # What the function likely does
    purposes = []
    if "connect" in code_lower or ":connect" in code_lower:
        purposes.append("event handler")
    if "new" in code_lower and ("instance" in code_lower or any(c in body for c in ["Part", "Frame", "TextLabel"])):
        purposes.append("creates instances")
    if "destroy" in code_lower or ":remove" in code_lower:
        purposes.append("cleans up/removes objects")
    if "tween" in code_lower or "tweeninfo" in code_lower:
        purposes.append("animates properties")
    if "wait" in code_lower or "task.wait" in code_lower or "yield" in code_lower:
        purposes.append("async/timing logic")
    if "spawn" in code_lower or "task.spawn" in code_lower:
        purposes.append("spawns concurrent tasks")
    if "for " in code_lower and ("ipairs" in code_lower or "pairs" in code_lower):
        purposes.append("iterates over collections")
    if "return " in code_lower:
        purposes.append("returns values")
    if "print" in code_lower or "warn" in code_lower or "error" in code_lower:
        purposes.append("logging/output")
    if "pcall" in code_lower or "xpcall" in code_lower:
        purposes.append("error handling")
    if "raycast" in code_lower or "findpart" in code_lower:
        purposes.append("spatial queries")
    if "getserv" in code_lower:
        purposes.append("accesses Roblox services")

    return {
        "api_calls": api_calls,
        "methods": methods,
        "purposes": purposes,
        "line_count": len(body.split("\n")),
    }


def _detect_patterns(code: str) -> dict:
    """Detect obfuscation and code patterns."""
    detected = {}
    for key, sig in OBFUSCATION_SIGNATURES.items():
        matches = re.findall(sig["pattern"], code)
        if matches:
            detected[key] = {
                "name": sig["name"],
                "desc": sig["desc"],
                "count": len(matches),
            }
    return detected


def _security_audit(code: str) -> list[dict]:
    """Scan for security-sensitive patterns."""
    flags = []
    for key, info in SECURITY_FLAGS.items():
        for pat in info["patterns"]:
            matches = re.findall(pat, code)
            if matches:
                flags.append({
                    "category": key,
                    "severity": info["severity"],
                    "desc": info["desc"],
                    "count": len(matches),
                })
                break
    return flags


def _score_complexity(code: str) -> dict:
    """Calculate complexity metrics."""
    lines = code.split("\n")
    non_empty = [l for l in lines if l.strip() and not l.strip().startswith("--")]

    # Cyclomatic complexity approximation
    cc = 1
    for line in non_empty:
        s = line.strip()
        if re.match(r"\b(if|elseif|while|for|repeat)\b", s):
            cc += 1
        elif re.match(r"\b(and|or)\b", s):
            cc += 1

    # Nesting depth
    depth = 0
    max_depth = 0
    for line in lines:
        s = line.strip()
        if re.match(r"(if|for|while|function|repeat|do)\b", s):
            depth += 1
            max_depth = max(max_depth, depth)
        elif s == "end":
            depth = max(0, depth - 1)

    # Halstead-like metric (very rough)
    operators = set()
    operands = set()
    for line in non_empty:
        for op in ["+", "-", "*", "/", "%", "^", "==", "~=", "<", ">", "<=", ">=", "=", "..", "#", "not", "and", "or"]:
            if op in line:
                operators.add(op)
        for word in re.findall(r"\b[a-zA-Z_]\w*\b", line):
            if word not in ("local", "function", "end", "if", "then", "elseif", "else", "for", "while", "do", "repeat", "until", "return", "in", "break", "continue", "true", "false", "nil", "not", "and", "or"):
                operands.add(word)

    return {
        "cyclomatic": cc,
        "max_nesting": max_depth,
        "halstead_volume": round(len(operators) * math.log2(max(len(operators), 1)) + len(operands) * math.log2(max(len(operands), 1)), 1) if operands else 0,
        "operators": len(operators),
        "operands": len(operands),
    }


# ─── Main Analysis ────────────────────────────────────────────────────

def analyze(code: str) -> dict:
    """Full deep analysis of Luau code."""
    lines = code.strip().split("\n")
    non_empty = [l for l in lines if l.strip() and not l.strip().startswith("--")]
    total_lines = len(lines)
    code_lines = len(non_empty)

    # Functions
    funcs_named = re.findall(r"\b(?:local\s+)?function\s+(\w+(?:[.:]\w+)*)\s*\(", code)
    funcs_anon = len(re.findall(r"\bfunction\s*\(", code)) - len(funcs_named)
    funcs_local = len(re.findall(r"\blocal\s+function\b", code))

    # Variables
    locals_count = len(re.findall(r"\blocal\s+\w+", code))
    globals_count = len(re.findall(r"^(?!\s*local\b)\s*(\w+)\s*=", code, re.MULTILINE))

    # Control flow
    ifs = len(re.findall(r"\bif\b", code))
    loops = len(re.findall(r"\b(for|while|repeat)\b", code))
    switches = len(re.findall(r"\belseif\b", code))

    # Roblox specifics
    services_used = []
    for api_name in API_DOCS:
        if "GetService" in api_name or "Service" in api_name:
            if api_name in code:
                services_used.append(api_name)

    instances_created = re.findall(r"Instance\.new\([\"'](\w+)[\"']\)", code)
    events = len(re.findall(r"\.Connect\s*\(", code))
    metatables = len(re.findall(r"getmetatable|setmetatable|__index|__newindex|__call", code))

    # Strings and numbers
    strings = len(re.findall(r'"[^"]*"|\'[^\']*\'', code))
    numbers = len(re.findall(r"\b\d+\.?\d*\b", code))

    # Comments
    comments = len(re.findall(r"(?<!\[)--(?!\[)", code))
    block_comments = len(re.findall(r"--\[\[", code))

    # Requires
    requires = re.findall(r"\brequire\s*\([\"']?([^)\"']+)[\"']?\)", code)

    # API calls found
    api_calls_found = set()
    for api_name in API_DOCS:
        if api_name in code:
            api_calls_found.add(api_name)

    methods_found = set()
    for method_name in METHOD_DOCS:
        if method_name in code:
            methods_found.add(method_name)

    # Sections
    sections = _split_sections(code)
    functions_sections = [s for s in sections if s["type"] == "function"]

    # Analyze each function
    func_analyses = []
    for sec in functions_sections:
        fa = _analyze_function_body(sec["text"])
        fa["name"] = sec["name"]
        fa["params"] = sec.get("params", "")
        fa["start_line"] = sec["start"]
        func_analyses.append(fa)

    # Patterns
    patterns = _detect_patterns(code)

    # Security
    security = _security_audit(code)

    # Complexity
    complexity = _score_complexity(code)

    # Purpose
    purpose = _guess_purpose({
        "services": services_used,
        "instances": instances_created,
        "events": events,
        "func_names": funcs_named,
        "metatables": metatables,
    }, code)

    return {
        "lines_total": total_lines,
        "lines_code": code_lines,
        "functions": len(funcs_named),
        "func_names": funcs_named,
        "func_analyses": func_analyses,
        "anon_functions": max(0, funcs_anon),
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
        "requires": requires,
        "api_calls": list(api_calls_found),
        "methods": list(methods_found),
        "patterns": patterns,
        "security": security,
        "complexity": complexity,
        "purpose": purpose,
        "sections": sections,
    }


def explain(code: str) -> str:
    """Return a detailed, structured explanation of the code."""
    info = analyze(code)

    parts = []

    # ── Header / Overview ──
    size = (
        "tiny" if info["lines_code"] < 10 else
        "small" if info["lines_code"] < 50 else
        "medium" if info["lines_code"] < 200 else
        "large" if info["lines_code"] < 500 else
        "very large"
    )
    parts.append(f"**Overview**\n{size.capitalize()} Luau script — {info['lines_code']} code lines, {info['lines_total']} total lines, {info['functions']} named function(s).")

    # ── Purpose ──
    if info["purpose"]:
        parts.append(f"**Purpose**\nThis script appears to be: **{info['purpose']}**.")

    # ── Complexity ──
    cx = info["complexity"]
    risk = (
        "low" if cx["cyclomatic"] <= 5 else
        "moderate" if cx["cyclomatic"] <= 15 else
        "high" if cx["cyclomatic"] <= 30 else
        "very high"
    )
    parts.append(f"**Complexity**\nCyclomatic: {cx['cyclomatic']} ({risk} risk) | Max nesting: {cx['max_nesting']} | Halstead volume: {cx['halstead_volume']}")

    # ── Functions ──
    if info["func_analyses"]:
        func_lines = []
        for fa in info["func_analyses"][:10]:
            desc_parts = []
            if fa["purposes"]:
                desc_parts.append(", ".join(fa["purposes"]))
            if fa["api_calls"]:
                desc_parts.append(f"calls: {', '.join(sorted(fa['api_calls'])[:4])}")
            desc = " — " + "; ".join(desc_parts) if desc_parts else ""
            func_lines.append(f"• `{fa['name']}({fa['params']})` (L{fa['start_line']}, {fa['line_count']} lines){desc}")
        if info["functions"] > 10:
            func_lines.append(f"  ... and {info['functions'] - 10} more")
        parts.append("**Functions**\n" + "\n".join(func_lines))

    # ── Roblox API Usage ──
    if info["services"]:
        svc_descs = []
        for s in info["services"][:8]:
            short = s.replace("game:GetService(", "").replace(")", "")
            svc_descs.append(f"`{short}`")
        parts.append("**Services**\n" + ", ".join(svc_descs))

    if info["instances"]:
        counts = Counter(info["instances"])
        inst_parts = [f"{n}× `{t}`" for t, n in counts.most_common(8)]
        parts.append("**Instances Created**\n" + ", ".join(inst_parts))

    if info["events"]:
        parts.append(f"**Events**\n{info['events']} event connection(s) — this script is {'event-driven' if info['events'] > 3 else 'mostly imperative'}.")

    # ── Control Flow ──
    flow = []
    if info["ifs"]:
        flow.append(f"{info['ifs']} conditionals")
    if info["loops"]:
        flow.append(f"{info['loops']} loops")
    if flow:
        parts.append(f"**Control Flow**\n{', '.join(flow)} | {info['switches']} elseif branches")

    # ── External Dependencies ──
    if info["requires"]:
        reqs = ", ".join(f"`{r}`" for r in info["requires"][:6])
        parts.append(f"**Dependencies**\nRequires: {reqs}")

    # ── Obfuscation Detection ──
    if info["patterns"]:
        pat_lines = []
        for key, p in info["patterns"].items():
            pat_lines.append(f"• **{p['name']}** — {p['desc']} ({p['count']} occurrence(s))")
        parts.append("**Obfuscation Detected**\n" + "\n".join(pat_lines))

    # ── Security Audit ──
    if info["security"]:
        sec_lines = []
        for s in info["security"]:
            icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(s["severity"], "⚪")
            sec_lines.append(f"{icon} **{s['severity']}** — {s['desc']}")
        parts.append("**Security Audit**\n" + "\n".join(sec_lines))

    # ── Key API Calls ──
    important_apis = [a for a in info["api_calls"] if "GetService" not in a]
    if important_apis:
        api_descs = []
        for a in important_apis[:8]:
            doc = API_DOCS.get(a, "")
            short = doc[:60] + "..." if len(doc) > 60 else doc
            api_descs.append(f"• `{a}` — {short}")
        parts.append("**Key API Calls**\n" + "\n".join(api_descs))

    # ── Methods Used ──
    if info["methods"]:
        method_descs = []
        for m in info["methods"][:10]:
            doc = METHOD_DOCS.get(m, "")
            short = doc[:50] + "..." if len(doc) > 50 else doc
            method_descs.append(f"• `{m}` — {short}")
        parts.append("**Methods**\n" + "\n".join(method_descs))

    # ── Style ──
    style = []
    if info["comments"] > 5:
        style.append(f"well-commented ({info['comments']} comments)")
    if info["strings"] > 20:
        style.append(f"string-heavy ({info['strings']} string literals)")
    if info["numbers"] > 15:
        style.append(f"number-heavy ({info['numbers']} numeric literals)")
    if info["metatables"] > 0:
        style.append(f"uses metatables ({info['metatables']} — likely OOP/proxy)")
    if style:
        parts.append("**Style**\n" + ", ".join(style) + ".")

    return "\n\n".join(parts)


def _guess_purpose(info: dict, code: str) -> str:
    """Infer the script's purpose from multiple signals."""
    code_lower = code.lower()
    hints = []

    # GUI
    gui_kws = ["screengui", "frame", "textlabel", "textbutton", "uistroke", "tweeninfo", "uicorner", "uipadding", "scrollingframe", "textbox", "imagebutton", "imagelabel", "uilistlayout"]
    if sum(1 for k in gui_kws if k in code_lower) >= 2:
        hints.append("GUI/interface system")

    # Combat
    if any(k in code_lower for k in ["health", "damage", "kill", "hit", "weapon", "sword", "gun", "bullet", "ammo"]):
        hints.append("combat/gameplay")

    # Admin
    if any(k in code_lower for k in ["ban", "kick", "admin", "moderator"]):
        hints.append("admin system")

    # Data persistence
    if any(k in code_lower for k in ["datastore", "save", "leaderstats", "data"]):
        hints.append("data persistence")

    # Networking
    if any(k in code_lower for k in ["remoteevent", "remotefunction", "fireserver", "onclientevent"]):
        hints.append("client-server networking")

    # Animation
    if any(k in code_lower for k in ["animate", "animation", "animator", "loadanimation"]):
        hints.append("animation system")

    # Physics
    if any(k in code_lower for k in ["bodyvelocity", "bodyposition", "vectorforce", "linearvelocity", "alignposition"]):
        hints.append("physics/movement")

    # Player input
    if any(k in code_lower for k in ["userinputservice", "mousebutton", "keyboard", "input began", "inputended"]):
        hints.append("player input handling")

    # Module
    if info["func_names"] and not info["events"]:
        hints.append("utility/module library")

    # Exploit
    if any(k in code_lower for k in ["hookfunction", "getgenv", "getrenv", "loadstring", "syn.", "fluxus", "krnl"]):
        hints.append("exploit/executor script")

    # GUI framework
    if any(k in code_lower for k in ["roact", "rodux", "fusion"]):
        hints.append("UI framework (Roact/Rodux/Fusion)")

    # NPC/AI
    if any(k in code_lower for k in ["pathfindingservice", "navmesh", "npc", "brain", "state machine", "patrol"]):
        hints.append("NPC AI/pathfinding")

    # Shop/economy
    if any(k in code_lower for k in ["marketplace", "gamepass", "devproduct", "promptpurchase", "currency", "coins", "gems"]):
        hints.append("shop/economy system")

    # Chat
    if any(k in code_lower for k in ["textchatservice", "chatservice", "bubblechat", "message"]):
        hints.append("chat system")

    if hints:
        return ", ".join(hints[:3])
    return ""
