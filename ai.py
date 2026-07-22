"""
Offline NLP chatbot — no API keys, no external services.

Massive pattern library, template responses, context tracking,
code detection, opinion system, conversational personality.
"""

import re
import math
import random
from collections import Counter

# ═════════════════════════════════════════════════════════════════════════
# NLP UTILITIES
# ═════════════════════════════════════════════════════════════════════════

_STOP_WORDS = frozenset(
    "a an the is it to in of for on and or but my your its i you we he she they "
    "me him her us them this that these those am are was were be been being have has "
    "had do does did will would could should may might can shall not no so if then "
    "than too very just about up out what which who whom whose where when how all any "
    "both each few more most other some such there here why s t don didn doesn isn aren "
    "wasn weren won wouldn couldn shouldn mustn needn d ll m re ve y let got get "
    "like think know really actually just gonna going wanna".split()
)

_SYNONYMS = {
    "obfuscate": "obfuscation", "obfuscated": "obfuscation", "obfuscating": "obfuscation",
    "obfuscating": "obfuscation", "scramble": "obfuscation", "scrambled": "obfuscation",
    "deobfuscate": "deobfuscation", "deobfuscated": "deobfuscation",
    "encrypt": "encryption", "encrypted": "encryption", "decrypt": "decryption",
    "hack": "exploit", "hacking": "exploit", "hacker": "exploit", "exploits": "exploit",
    "cheat": "exploit", "cheating": "exploit", "cheats": "exploit",
    "script": "luau", "coding": "programming", "code": "programming",
    "program": "programming", "programmer": "programming", "developer": "programming",
    "game": "roblox", "gaming": "roblox", "roblox": "roblox",
    "gui": "interface", "ui": "interface", "interface": "interface",
    "speed": "performance", "lag": "performance", "fps": "performance",
    "slow": "performance", "fast": "performance", "optimize": "performance",
    "beginner": "newbie", "start": "newbie", "started": "newbie",
    "thanks": "thank", "thx": "thank", "ty": "thank", "tysm": "thank",
    "hello": "greet", "hi": "greet", "hey": "greet", "sup": "greet",
    "yo": "greet", "howdy": "greet", "hiya": "greet", "hola": "greet",
    "bye": "farewell", "goodbye": "farewell", "see ya": "farewell", "cya": "farewell",
    "break": "error", "crash": "error", "bug": "error", "issue": "error",
    "fix": "solve", "solve": "solve", "help": "assist", "assist": "assist",
    "cool": "positive", "awesome": "positive", "nice": "positive",
    "good": "positive", "great": "positive", "amazing": "positive", "fire": "positive",
    "bad": "negative", "terrible": "negative", "awful": "negative",
    "worst": "negative", "hate": "negative", "trash": "negative", "garbage": "negative",
    "recommend": "suggest", "suggestion": "suggest", "advise": "suggest",
    "difference": "compare", "compare": "compare", "vs": "compare", "versus": "compare",
    "create": "make", "build": "make", "make": "make",
    "delete": "remove", "remove": "remove", "destroy": "remove",
    "download": "install", "install": "install",
    "update": "modify", "change": "modify", "edit": "modify", "modify": "modify",
    "work": "function", "function": "function",
    "use": "utilize", "utilize": "utilize",
    "tutorial": "guide", "guide": "guide", "explain": "explain", "teach": "guide",
    "definition": "meaning", "meaning": "meaning", "define": "meaning",
    "what's": "what is", "how's": "how is", "it's": "it is", "i'm": "i am",
    "don't": "do not", "doesn't": "does not", "can't": "cannot",
    "won't": "will not", "isn't": "is not", "aren't": "are not",
    "wanna": "want to", "gonna": "going to", "gotta": "got to",
    "better": "best", "worse": "worst",
    "is roblox": "roblox", "for roblox": "roblox", "in roblox": "roblox",
    "roblox game": "roblox", "roblox script": "luau",
}


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s']", " ", text)
    tokens = text.split()
    return [_SYNONYMS.get(t.strip("'"), t.strip("'")) for t in tokens
            if t.strip("'") and len(t.strip("'")) > 1 and t.strip("'") not in _STOP_WORDS]


def _raw_tokens(text: str) -> list[str]:
    """Tokenize without removing stop words — for phrase matching."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s']", " ", text)
    return [t.strip("'") for t in text.split() if t.strip("'")]


def _ngrams(tokens: list[str], n: int) -> list[str]:
    return [" ".join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]


def _cosine_sim(v1: dict, v2: dict) -> float:
    common = set(v1) & set(v2)
    if not common:
        return 0.0
    dot = sum(v1[k] * v2[k] for k in common)
    mag1 = math.sqrt(sum(x*x for x in v1.values()))
    mag2 = math.sqrt(sum(x*x for x in v2.values()))
    return dot / (mag1 * mag2) if mag1 and mag2 else 0.0


def _tfidf_vec(tokens: list[str]) -> dict:
    counts = Counter(tokens)
    total = len(tokens) or 1
    return {t: c / total for t, c in counts.items()}


# ═════════════════════════════════════════════════════════════════════════
# KNOWLEDGE BASE
# ═════════════════════════════════════════════════════════════════════════

KB = {}


def _kb(topic, patterns, response):
    KB[topic] = {"patterns": patterns, "response": response}


# ── Greetings ──────────────────────────────────────────────────────────

_kb("greet",
    ["hello", "hi", "hey", "howdy", "hiya", "sup", "yo", "what's up", "greetings",
     "good morning", "good afternoon", "good evening", "hola", "howdy", "heya"],
    None)  # handled dynamically

_kb("bye",
    ["bye", "goodbye", "see you", "see ya", "later", "goodnight", "gn", "cya", "gtg", "gotta go"],
    None)

_kb("how_are_you",
    ["how are you", "how r u", "how you doing", "how's it going", "how is it going",
     "you good", "you ok", "what's up with you", "how are things", "how have you been"],
    None)

_kb("what_are_you",
    ["what are you", "who are you", "what is this", "what bot is this",
     "tell me about yourself", "introduce yourself", "what is shesfuscator",
     "what do you do", "describe yourself"],
    "I'm **shesfuscator** — a Luau/Roblox obfuscation bot with AI chat. I can obfuscate, deobfuscate, and explain scripts, and I know a *lot* about Roblox development and Luau programming. What do you need?"

)

_kb("thanks",
    ["thank", "thanks", "thx", "ty", "appreciate", "tysm", "tys", "thank you", "thanks a lot"],
    None)

_kb("yes",
    ["yes", "yeah", "yep", "sure", "ok", "okay", "yup", "definitely", "absolutely", "of course", "yessir"],
    None)

_kb("no",
    ["no", "nah", "nope", "nahh", "not really", "no thanks"],
    None)

# ── Bot capabilities ───────────────────────────────────────────────────

_kb("capabilities",
    ["what can you do", "what do you do", "capabilities", "features", "what are your commands",
     "list commands", "what can you help with", "what are you able to do", "commands",
     "how does this bot work", "what does this bot do", "help me", "how to use",
     "how do i use", "what can this bot do", "bot features", "bot capabilities"],
    "**Here's what I can do:**\n\n**Obfuscation:**\n- `/obfuscate` — Protect Luau code with 7 presets (Very Light → Ultra)\n- `/deobfuscate` — Reverse my custom obfuscation layers\n- DM me `.lua` files for interactive obfuscation!\n\n**Analysis:**\n- `/explain` — Deep static analysis of any Luau script\n- Chat with me about Roblox, Luau, game dev, obfuscation\n\n**Info:**\n- `/status` — Bot status\n- `/help` — All options\n\nI know about 100+ Roblox APIs, Luau patterns, game dev techniques, and obfuscation methods. Ask me anything!"
)

# ── Obfuscation ────────────────────────────────────────────────────────

_kb("obfuscation",
    ["what is obfuscation", "explain obfuscation", "define obfuscation", "obfuscation mean",
     "obfuscation definition", "what does obfuscate mean", "why obfuscate", "obfuscation explained"],
    "**Obfuscation** transforms code to make it hard to read while keeping it functional. It's like scrambling a message so only you can understand it.\n\nFor Luau/Roblox, this prevents people from stealing, reverse-engineering, or modifying your scripts.\n\nshesfuscator uses the **Prometheus engine** (9 Lua-based steps) + **8 custom Python layers** for multi-layered protection. Think of it as putting your code through a blender — the result still runs, but good luck reading it."
)

_kb("deobfuscation",
    ["deobfuscate", "deobfuscation", "reverse", "undo", "crack", "unobfuscate",
     "decode obfuscated", "how to deobfuscate", "can you deobfuscate"],
    "I can reverse my own **custom layers** (StringEncoder, VarRenamer, DeadCode, HexNumbers, BoolWrap, NegateBools, NoiseVars, Watermark) using `/deobfuscate`.\n\nBut I **cannot** reverse Prometheus engine steps like Vmify (custom bytecode VM) or EncryptStrings — those are effectively one-way. Once it's VMified, there's no decompiler."
)

# ── Presets ────────────────────────────────────────────────────────────

_kb("presets",
    ["preset", "presets", "which preset", "preset options", "preset list", "what presets",
     "obfuscation levels", "levels", "strength", "how strong", "protection level",
     "preset options", "obfuscation levels"],
    "shesfuscator has **7 presets**:\n\n**Very Light** — ConstantArray only. Barely noticeable.\n**Light** — ConstantArray + WrapInFunction + HexNumbers.\n**Medium** — EncryptStrings + ConstantArray + WrapInFunction + HexNumbers + StringEncoder. **Best balance.**\n**Medium-High** — Adds Vmify + AntiTamper + BoolWrap.\n**High** — Adds NumbersToExpressions + VarRenamer.\n**Very High** — Adds DeadCode + Watermark.\n**Ultra** — Double Vmify + all 8 custom layers. Maximum protection, higher runtime cost."
)

_kb("best_preset",
    ["which preset best", "best preset", "what preset should i use", "recommend preset",
     "which one should i use", "best protection", "what's the best one", "which is good"],
    "**Depends on your needs:**\n\n- **Learning/dev?** → **Very Light** or **Light**\n- **Hiding code from kids?** → **Medium** (sweet spot)\n- **Serious protection?** → **High** or **Very High**\n- **Maximum security, perf doesn't matter?** → **Ultra** (double VM)\n\nMost people go with **Medium** — good protection without killing performance."
)

# ── Engine Steps ───────────────────────────────────────────────────────

_kb("vmify",
    ["vmify", "bytecode", "virtual machine", "vm protect", "vm obfuscation",
     "custom bytecode", "vm step", "what is vmify"],
    "**Vmify** is the strongest step. It compiles your Luau into a **custom bytecode VM** — the output isn't even valid Lua anymore, it's a custom interpreter.\n\nReverse engineering this is extremely difficult because there's no standard bytecode to analyze. The Ultra preset runs Vmify **twice** (VM inside a VM).\n\n**Cost:** High performance overhead. Use when security > speed."
)

_kb("encrypt_strings",
    ["encrypt string", "string encryption", "encryptstrings", "encrypt strings step"],
    "**EncryptStrings** encrypts all string literals using pseudo-random generators. Strings are decrypted at runtime, invisible in source.\n\n**Cost:** Medium. Good balance."
)

_kb("anti_tamper",
    ["anti tamper", "antitamper", "integrity", "tamper", "anti edit"],
    "**AntiTamper** adds integrity checks. If someone modifies, beautifies, or hooks functions in your obfuscated script, it breaks.\n\n**Cost:** Low. Recommended for Medium+."
)

_kb("constant_array",
    ["constant array", "constantarray", "constant table", "constants extract"],
    "**ConstantArray** extracts all constants into an encoded table with base64/base85 encoding and rotation. Makes finding specific values much harder.\n\n**Cost:** Low."
)

_kb("var_renamer",
    ["var renamer", "variable rename", "rename variables", "varrenamer", "rename local"],
    "**VarRenamer** replaces local variable names with confusing lookalike characters (I, l, 1, O, o, 0). Code becomes nearly unreadable.\n\n**Cost:** Low. No runtime impact."
)

_kb("dead_code",
    ["dead code", "deadcode", "fake code", "unreachable", "inject dead"],
    "**DeadCode** injects random unreachable blocks (if false, while false, etc.). Confuses static analyzers and humans.\n\n**Cost:** Low. Never executes."
)

_kb("control_flow",
    ["control flow", "controlflow", "flatten", "flattening"],
    "**ControlFlow** wraps code in numeric switch dispatchers. Execution follows a randomized dispatch table instead of linear flow.\n\n**Cost:** Medium."
)

_kb("string_encoder",
    ["string encoder", "stringencoder", "decimal escapes", "wearedevs"],
    "**StringEncoder** converts strings to `\\ddd` decimal escapes. E.g., `\"hello\"` → `\"\\104\\101\\108\\108\\111\"`.\n\n**Cost:** Low."
)

_kb("hex_numbers",
    ["hex number", "hexadecimal", "hex convert", "number hex", "hex numbers"],
    "**HexNumbers** converts decimals to hex (0x format). `79` → `0x4F`. Visual obfuscation only.\n\n**Cost:** None."
)

_kb("bool_wrap",
    ["bool wrap", "boolean wrap", "wrap bool", "true false obfuscation", "bool obfuscation"],
    "**BoolWrap** replaces `true` → `(1==1)` and `false` → `(1==0)`.\n\n**Cost:** None."
)

_kb("negate_bools",
    ["negate bool", "negate boolean", "not true", "not false"],
    "**NegateBools** does `true` → `(not false)`, `false` → `(not true)`.\n\n**Cost:** None."
)

_kb("noise_vars",
    ["noise var", "noise variable", "random variable", "junk variable"],
    "**NoiseVars** injects unused random assignments after `end` statements. Looks real, does nothing.\n\n**Cost:** None."
)

_kb("watermark",
    ["watermark", "branding", "tag", "signature"],
    "**Watermark** adds `--[[ shesfuscator v1.0 ]]` at the top. Branding.\n\n**Cost:** None."
)

# ── Deep dives ─────────────────────────────────────────────────────────

_kb("double_vmify",
    ["double vmify", "vmify twice", "vmify double", "two vm", "double vm", "ultra vm"],
    "**Double Vmify** (Ultra preset) runs Vmify **twice**: first compiles your code into a VM, then compiles the VM's interpreter into *another* VM. VM inside a VM.\n\nExtremely hard to reverse. Significant performance cost."
)

_kb("layer_order",
    ["layer order", "step order", "obfuscation order", "what order", "pipeline order"],
    "Order matters:\n\n1. **Prometheus engine** runs first (Vmify, EncryptStrings, etc.)\n2. **Custom Python layers** run after (HexNumbers, StringEncoder, etc.)\n\nRecommended engine order: ConstantArray → NumbersToExpressions → EncryptStrings → AntiTamper → Vmify → WrapInFunction."
)

_kb("unreversible",
    ["what cant be reversed", "what is irreversible", "cant deobfuscate", "permanent obfuscation"],
    "**Cannot be reversed:**\n- **Vmify** — Custom bytecode VM, no decompiler exists\n- **EncryptStrings** — One-way encryption with runtime keys\n- **AntiTamper** — Integrity checks that break if removed\n- **ProxifyLocals** — Proxy indirection\n\nCustom layers (StringEncoder, VarRenamer, DeadCode, etc.) **can** be reversed with `/deobfuscate`."
)

# ── Roblox APIs ────────────────────────────────────────────────────────

_kb("getservice",
    ["game getservice", "game service", "getservice", "access service", "how to get service"],
    "`game:GetService()` is the standard way to access Roblox services:\n\n```lua\nlocal Players = game:GetService('Players')\nlocal RS = game:GetService('ReplicatedStorage')\n```\n\nAlways use `GetService` instead of direct references like `game.Players` — it's more reliable and avoids race conditions."
)

_kb("players",
    ["players service", "players object", "get players", "player join", "player added", "player joining"],
    "**Players** service manages connected players:\n\n```lua\nlocal Players = game:GetService('Players')\nPlayers.PlayerAdded:Connect(function(player)\n    print(player.Name .. ' joined!')\nend)\n```\n\nKey props: `.Name`, `.UserId`, `.Character`, `.TeamColor`\nKey methods: `:Kick()`, `:GetRankInGroup()`, `:LoadCharacter()`"
)

_kb("remotes",
    ["remote event", "remote function", "remoteevent", "remotefunction", "client server",
     "fire server", "on client event", "networking"],
    "**RemoteEvents** handle client↔server communication:\n\n```lua\n-- Server\nremote.OnServerEvent:Connect(function(player, data)\n    -- validate and handle\nend)\n\n-- Client\nremote:FireServer(data)\n```\n\n**Critical:** Always validate remote data on the server. Never trust client input."
)

_kb("datastore",
    ["datastore", "data store", "save data", "load data", "player data", "data persistence",
     "save player", "saving data", "persistent"],
    "**DataStoreService** for persistent storage:\n\n```lua\nlocal DS = game:GetService('DataStoreService'):GetDataStore('V1')\n\n-- Save\nstore:SetAsync(key, data)\n\n-- Load\nlocal data = store:GetAsync(key)\n```\n\n**Always wrap in pcall!** DataStores have rate limits (~60/min) and can fail."
)

_kb("tween",
    ["tween", "tween service", "tweenservice", "animation tween", "smooth animation", "property animation"],
    "**TweenService** for smooth animations:\n\n```lua\nlocal TS = game:GetService('TweenService')\nlocal info = TweenInfo.new(1, Enum.EasingStyle.Quad)\nlocal tween = TS:Create(part, info, {Position = target})\ntween:Play()\n```\n\nStyles: Linear, Quad, Cubic, Bounce, Elastic, Exponential, etc."
)

_kb("runservice",
    ["run service", "runservice", "heartbeat", "render stepped", "per frame", "every frame"],
    "**RunService** for per-frame logic:\n\n```lua\nlocal RS = game:GetService('RunService')\nRS.Heartbeat:Connect(function(dt)\n    -- every frame (server + client)\nend)\n```\n\nUse `dt` (delta time) for frame-rate independent movement."
)

_kb("userinput",
    ["user input", "userinput", "input service", "keyboard", "mouse", "key press", "input began"],
    "**UserInputService** for input detection:\n\n```lua\nUIS.InputBegan:Connect(function(input, gameProcessed)\n    if gameProcessed then return end\n    if input.KeyCode == Enum.KeyCode.E then\n        -- E pressed\n    end\nend)\n```\n\nCheck `gameProcessed` to ignore input when typing in TextBoxes."
)

_kb("http",
    ["http service", "httpservice", "http request", "web request", "api call", "fetch", "external api"],
    "**HttpService** for HTTP requests (server-only, must enable in Game Settings):\n\n```lua\nlocal Http = game:GetService('HttpService')\nlocal data = Http:GetAsync('https://api.example.com/data')\nlocal json = Http:JSONDecode(data)\n```\n\nAlso: `:PostAsync()`, `:RequestAsync()`, `:JSONEncode()`"
)

_kb("workspace",
    ["workspace", "game world", "3d space", "scene", "game map"],
    "**Workspace** is the root of the 3D world. All visible objects live here:\n\n```lua\nlocal ws = game:GetService('Workspace')\nlocal part = ws:FindFirstChild('MyPart')\n```\n\nContains: Parts, Models, Terrain, Camera, SpawnLocation."
)

_kb("instance_new",
    ["instance new", "create instance", "new instance", "make object", "create object"],
    "`Instance.new()` creates Roblox objects:\n\n```lua\nlocal part = Instance.new('Part')\npart.Name = 'MyPart'\npart.Position = Vector3.new(0, 5, 0)\npart.Parent = workspace  -- set Parent LAST!\n```"
)

_kb("findFirstChild",
    ["find first child", "findfirstchild", "get child", "find child", "child exists"],
    "`:FindFirstChild()` safely searches for a child (returns nil if missing):\n\n```lua\nlocal part = folder:FindFirstChild('MyPart')\nif part then\n    -- found it\nend\n```\n\nPrefer over `:WaitForChild()` in hot paths."
)

_kb("waitforchild",
    ["wait for child", "waitforchild", "yield for child"],
    "`:WaitForChild()` yields until a child appears:\n\n```lua\nlocal part = script.Parent:WaitForChild('MyPart', 5) -- 5s timeout\n```\n\n**Warning:** Hangs forever without a timeout if the child doesn't exist!"
)

# ── Game Dev ───────────────────────────────────────────────────────────

_kb("gui",
    ["gui", "ui", "interface", "user interface", "screengui", "frame", "textlabel",
     "textbutton", "gui tutorial", "make a gui", "gui code"],
    "**Roblox GUI** basics:\n\n```lua\nlocal sg = Instance.new('ScreenGui')\nsg.Parent = player.PlayerGui\n\nlocal frame = Instance.new('Frame')\nframe.Size = UDim2.new(0, 200, 0, 100)\nframe.Parent = sg\n\nlocal label = Instance.new('TextLabel')\nlabel.Text = 'Hello!'\nlabel.Parent = frame\n```\n\n**Layout:** UIListLayout, UIGridLayout\n**Styling:** UICorner, UIStroke, UIGradient, UIPadding"
)

_kb("combat",
    ["combat", "damage", "health", "kill", "hit", "weapon", "sword", "gun", "fight", "attack", "hp", "health system"],
    "**Combat system** pattern:\n\n```lua\nlocal function onDamage(player, target, amount)\n    local char = target.Character\n    if not char then return end\n    local hum = char:FindFirstChildOfClass('Humanoid')\n    if not hum then return end\n    hum.Health = math.max(0, hum.Health - amount)\nend\n```\n\n**Tips:** Validate on server, use RemoteEvents, clamp health."
)

_kb("saving",
    ["save game", "save data", "leaderstats", "leader board", "leaderboard", "stats",
     "currency", "coins", "money", "data save", "player saving"],
    "**Player data persistence:**\n\n```lua\nlocal DS = game:GetService('DataStoreService'):GetDataStore('V1')\n\ngame.Players.PlayerAdded:Connect(function(player)\n    local ls = Instance.new('Folder')\n    ls.Name = 'leaderstats'\n    ls.Parent = player\n    \n    local coins = Instance.new('IntValue')\n    coins.Name = 'Coins'\n    coins.Parent = ls\n    \n    local ok, data = pcall(DS.GetAsync, DS, 'p_'..player.UserId)\n    if ok and data then coins.Value = data end\nend)\n\ngame.Players.PlayerRemoving:Connect(function(player)\n    pcall(DS.SetAsync, DS, 'p_'..player.UserId, player.leaderstats.Coins.Value)\nend)\n```"
)

_kb("npc",
    ["npc", "ai enemy", "npc ai", "pathfinding", "patrol", "chase", "enemy ai", "bot ai"],
    "**NPC AI** with PathfindingService:\n\n```lua\nlocal PS = game:GetService('PathfindingService')\nlocal path = PS:CreatePath()\n\npath:ComputeAsync(start, target)\nfor _, wp in ipairs(path:GetWaypoints()) do\n    humanoid:MoveTo(wp.Position)\n    humanoid.MoveToFinished:Wait()\nend\n```\n\n**State machine:** Idle → Patrol → Chase → Attack → Dead."
)

_kb("raycasting",
    ["raycast", "ray cast", "ray", "line of sight", "hit detection", "collision"],
    "**Raycast** for hit detection:\n\n```lua\nlocal result = workspace:Raycast(origin, direction * 100)\nif result then\n    print('Hit:', result.Instance.Name)\n    print('Position:', result.Position)\nend\n```\n\nAlso: `:Blockcast()`, `:Spherecast()`, `:Shapecast()` for area checks."
)

_kb("modules",
    ["module", "module script", "require", "shared code", "library", "reuse code"],
    "**ModuleScripts** for reusable code:\n\n```lua\n-- ModuleScript\nlocal Utils = {}\nfunction Utils.round(n, d)\n    local m = 10^(d or 0)\n    return math.floor(n * m + 0.5) / m\nend\nreturn Utils\n\n-- Usage\nlocal Utils = require(ReplicatedStorage.Utils)\nprint(Utils.round(3.14, 2))  -- 3.14\n```"
)

_kb("pcall",
    ["pcall", "xpcall", "error handling", "try catch", "safe call", "protected call", "error catch"],
    "**pcall** catches errors:\n\n```lua\nlocal ok, err = pcall(function()\n    error('oops')\nend)\n\nif ok then print('success')\nelse print('Error:', err) end\n```\n\n**Always wrap** DataStore calls, HTTP requests, and I/O in pcall!"
)

_kb("tasks",
    ["task spawn", "task wait", "task delay", "task library", "task.cancel", "task.spawn", "task.wait"],
    "**task** library (better than wait/spawn):\n\n```lua\ntask.wait(2)            -- yield 2 sec\ntask.spawn(function()  -- async (no yield)\n    print('running')\nend)\ntask.delay(5, fn)      -- run after 5 sec\n```\n\nAlways prefer `task` over `wait()`/`spawn()`."
)

_kb("loops",
    ["loop", "for loop", "while loop", "repeat", "iteration", "iterate", "ipairs", "pairs", "for loop lua"],
    "**Loops** in Luau:\n\n```lua\nfor i = 1, 10 do print(i) end\nfor i, v in ipairs({'a','b'}) do print(i, v) end\nfor k, v in pairs({x=1}) do print(k, v) end\nwhile condition do ... end\nrepeat ... until condition\n```\n\nUse `ipairs` for arrays, `pairs` for dictionaries."
)

_kb("tables",
    ["table", "array", "dictionary", "hash", "key value", "lua table"],
    "**Lua tables** — the only data structure:\n\n```lua\nlocal arr = {'apple', 'banana'}       -- 1-indexed!\nlocal dict = {name='Bob', health=100}\n\nprint(arr[1])        -- 'apple'\nprint(dict.name)     -- 'Bob'\nprint(#arr)          -- 2\n\ntable.insert(arr, 'cherry')\ntable.remove(arr, 1)\n```"
)

_kb("strings",
    ["string", "string manipulation", "string concat", "string format", "string operations"],
    "**String operations:**\n\n```lua\nlocal s = 'Hello World'\nprint(#s)              -- 11\nprint(s:upper())       -- HELLO WORLD\nprint(s:sub(1, 5))     -- Hello\nprint(s:find('World')) -- 7, 11\nprint('a' .. 'b')      -- ab\nprint(string.format('HP: %d', 50))\n```"
)

_kb("metatables",
    ["metatable", "metatables", "__index", "__newindex", "__call", "oop", "class", "object oriented"],
    "**Metatables** for OOP:\n\n```lua\nlocal Player = {}\nPlayer.__index = Player\n\nfunction Player.new(name)\n    return setmetatable({name=name}, Player)\nend\n\nfunction Player:Say(msg)\n    print(self.name..': '..msg)\nend\n\nlocal p = Player.new('Bob')\np:Say('Hello')  -- Bob: Hello\n```"
)

# ── General / Fun ──────────────────────────────────────────────────────

_kb("joke",
    ["joke", "tell me a joke", "make me laugh", "funny", "humor", "comedy", "tell a joke"],
    None)  # dynamic

_kb("meaning_of_life",
    ["meaning of life", "purpose of life", "why are we here", "42", "deep question", "philosophy"],
    "42. Obviously.\n\nBut if you want something practical — the meaning of life is writing obfuscated Luau scripts and watching people try to read them."
)

_kb("favorite",
    ["favorite", "favourite", "what do you like", "your fav", "best thing", "your favorite"],
    "I'm a bot, so no feelings — but if I had favorites, it'd be **Vmify**. Turning readable Lua into a custom bytecode VM is *chef's kiss*.\n\nWhat about you? What's your favorite obfuscation step?"
)

_kb("who_made",
    ["who made you", "who created you", "your creator", "your developer", "who built you", "author"],
    "Built by the shesfuscator team — same people behind the obfuscation engine. I run on Python + discord.py + Prometheus."
)

_kb("safe",
    ["is it safe", "is shesfuscator safe", "will it break my code", "safe to use",
     "will it work", "does it break", "is it secure", "will my code still work"],
    "**Yes!**\n\n- Never modifies your original code — only produces a new file\n- Obfuscated code runs identically\n- Lower presets have minimal overhead\n- Always test your obfuscated output to be sure!"
)

_kb("cost",
    ["cost", "price", "free", "how much", "payment", "subscription", "pricing", "is it free"],
    "**Completely free.** No limits, no subscriptions, no hidden fees. DM a file or use `/obfuscate`!"
)

_kb("languages",
    ["supported languages", "what languages", "can i use with", "support python",
     "support javascript", "only lua", "only luau"],
    "shesfuscator supports **Luau** and **Lua 5.1** — built specifically for Roblox. For other languages you'd need a different tool."
)

_kb("performance",
    ["performance", "slow", "speed", "lag", "fps", "optimization", "fast", "runtime", "overhead", "will it lag"],
    "**Performance by step:**\n\n**None/Low:** HexNumbers, Watermark, AddVararg, WrapInFunction, ConstantArray, BoolWrap, NegateBools, NoiseVars\n**Medium:** EncryptStrings, NumbersToExpressions, ProxifyLocals, ControlFlow, SplitStrings, StringEncoder, VarRenamer, DeadCode\n**High:** Vmify\n\nIf performance matters → **Very Light** or **Light**. Max security → **Ultra**."
)

# ── Roblox deep dives ──────────────────────────────────────────────────

_kb("leaderstats",
    ["leaderstats", "leaderboard", "leader board", "player stats display", "score display"],
    "**Leaderstats** show on the leaderboard automatically:\n\n```lua\ngame.Players.PlayerAdded:Connect(function(player)\n    local ls = Instance.new('Folder')\n    ls.Name = 'leaderstats'\n    ls.Parent = player\n    \n    local wins = Instance.new('IntValue')\n    wins.Name = 'Wins'\n    wins.Parent = ls\nend)\n```\n\nThe folder **must** be named `leaderstats`."
)

_kb("admin",
    ["admin", "admin commands", "moderator", "kick", "ban", "admin system", "mod system"],
    "**Admin system** pattern:\n\n```lua\nlocal ADMINS = {123456789}\n\nplayer.Chatted:Connect(function(msg)\n    if not table.find(ADMINS, player.UserId) then return end\n    local args = msg:split(' ')\n    if args[1] == '!kick' then\n        local t = game.Players:FindFirstChild(args[2])\n        if t then t:Kick('Kicked') end\n    end\nend)\n```\n\n**Always validate on server!**"
)

_kb("local_script",
    ["local script", "server script", "local vs server", "client server difference", "where to put script"],
    "**Script contexts:**\n\n- **Server Script** (ServerScriptService) — game logic, data, authority\n- **LocalScript** (StarterPlayerScripts, StarterGui) — UI, input, camera\n- **ModuleScript** (anywhere) — shared code\n\n**Rule:** Sensitive logic on server, UI/input on client."
)

_kb("roblox_studio",
    ["roblox studio", "studio", "download studio", "where to get studio"],
    "**Roblox Studio** — free IDE for Roblox games:\n\n1. Go to [create.roblox.com](https://create.roblox.com)\n2. Download and sign in\n3. Create a Baseplate or template\n4. Use the script editor for Luau\n\nIncludes 3D viewport, terrain editor, debugger, and testing tools."
)

# ── Opinions / Discussion ──────────────────────────────────────────────

_kb("opinion_obfuscation",
    ["what do you think about obfuscation", "is obfuscation good", "is obfuscation worth it",
     "do you like obfuscation", "obfuscation opinion"],
    "Obfuscation is a tool — like a lock on your door. It won't stop a determined thief, but it stops 99% of casual copying.\n\nFor Roblox, it's especially useful because scripts are easily accessible to anyone who joins your game. Even basic obfuscation (Medium preset) makes it significantly harder to steal your work.\n\nThe key is finding the right balance between protection and performance."
)

_kb("opinion_exploits",
    ["what do you think about exploits", "exploits bad", "roblox exploits", "exploit scripts",
     "do exploits work", "executor"],
    "Exploits are a cat-and-mouse game. Executors run arbitrary code on the client, which means anything client-side can be exploited.\n\nThe best defense is **server-side validation** — never trust the client. If a player says they dealt 999 damage, verify it on the server.\n\nObfuscation helps protect your scripts from being *read*, but server authority is what actually prevents cheating."
)

# ── Math / Debug / Optimize ────────────────────────────────────────────

_kb("math",
    ["math", "calculate", "equation", "sum", "average", "multiply", "divide", "math library"],
    "**Luau math library:**\n\n```lua\nmath.abs(-5)       -- 5\nmath.ceil(4.2)     -- 5\nmath.floor(4.8)    -- 4\nmath.max(3, 7)     -- 7\nmath.min(3, 7)     -- 3\nmath.random(1,10)  -- random int\nmath.sqrt(16)      -- 4\nmath.noise(x, y)   -- Perlin noise\nmath.pi            -- 3.14159...\n```"
)

_kb("debug",
    ["debug", "debugging", "find bug", "fix error", "not working", "error", "why broken"],
    "**Debugging tips:**\n\n1. `print(variable)` — check values\n2. `pcall()` — catch errors without crashing\n3. Studio debugger (F9) — breakpoints & watch\n4. `warn()` — prints in yellow (easier to spot)\n\n```lua\nlocal function dbg(name, val)\n    print(string.format('[DBG] %s = %s (%s)', name, tostring(val), type(val)))\nend\n```"
)

_kb("optimize",
    ["optimize", "optimization", "make faster", "improve performance", "efficient", "better performance"],
    "**Performance tips:**\n\n1. Cache services: `local Players = game:GetService('Players')` once\n2. Use `task.wait()` not `wait()`\n3. Minimize remote events — batch data\n4. Use `:FindFirstChild()` not `:WaitForChild()` in hot paths\n5. Debounce events\n6. Use `RunService.Heartbeat` not `while true do`\n7. StreamEnabled for distant objects"
)

# ═════════════════════════════════════════════════════════════════════════
# INTENT CLASSIFIER
# ═════════════════════════════════════════════════════════════════════════

_KB_VECTORS = {}
_KB_PATTERNS = {}


def _build_index():
    for topic, entry in KB.items():
        all_text = " ".join(entry["patterns"])
        tokens = _tokenize(all_text)
        _KB_VECTORS[topic] = _tfidf_vec(tokens)
        _KB_PATTERNS[topic] = entry["patterns"]


_build_index()


def classify_intent(text: str, context_topics: list[str] = None) -> tuple[str, float]:
    raw = text.lower().strip()
    tokens = _tokenize(text)

    # Phase 0: Exact phrase match (catches "what are you", "how are you", etc.)
    best_phrase = None
    best_phrase_score = 0
    for topic, patterns in _KB_PATTERNS.items():
        for pat in patterns:
            # Word-boundary match to avoid "hi" matching inside "this"
            if re.search(r'\b' + re.escape(pat) + r'\b', raw):
                score = len(pat) / max(len(raw), 1) + 0.5
                if score > best_phrase_score:
                    best_phrase_score = score
                    best_phrase = topic
    if best_phrase and best_phrase_score > 0.4:
        return (best_phrase, min(best_phrase_score, 1.0))

    if not tokens:
        return ("fallback", 0.0)

    user_vec = _tfidf_vec(tokens)

    # Phase 1: Cosine similarity
    best_sim = None
    best_sim_score = 0
    for topic, vec in _KB_VECTORS.items():
        sim = _cosine_sim(user_vec, vec)
        if sim > best_sim_score:
            best_sim_score = sim
            best_sim = topic

    # Phase 2: N-gram overlap
    bigrams = _ngrams(tokens, 2)
    best_ngram = None
    best_ngram_score = 0
    for topic, patterns in _KB_PATTERNS.items():
        pat_tokens = []
        for p in patterns:
            pat_tokens.extend(_tokenize(p))
        pat_bigrams = _ngrams(pat_tokens, 2)
        if not bigrams or not pat_bigrams:
            continue
        overlap = len(set(bigrams) & set(pat_bigrams))
        score = overlap / max(len(bigrams), 1)
        if score > best_ngram_score:
            best_ngram_score = score
            best_ngram = topic

    # Phase 3: Keyword overlap
    best_kw = None
    best_kw_score = 0
    for topic, patterns in _KB_PATTERNS.items():
        pat_tokens = _tokenize(" ".join(patterns))
        overlap = len(set(tokens) & set(pat_tokens))
        score = overlap / max(len(pat_tokens), 1)
        if score > best_kw_score:
            best_kw_score = score
            best_kw = topic

    # Combine
    candidates = {}
    if best_sim:
        candidates[best_sim] = candidates.get(best_sim, 0) + best_sim_score * 2.0
    if best_ngram:
        candidates[best_ngram] = candidates.get(best_ngram, 0) + best_ngram_score * 1.5
    if best_kw:
        candidates[best_kw] = candidates.get(best_kw, 0) + best_kw_score * 1.0

    # Context boost
    if context_topics:
        for ct in context_topics[-3:]:
            for topic in candidates:
                if _topic_similarity(ct, topic) > 0.3:
                    candidates[topic] *= 1.15

    if not candidates:
        return ("fallback", 0.0)

    best_topic = max(candidates, key=candidates.get)
    confidence = min(candidates[best_topic] / 4.0, 1.0)
    return (best_topic, confidence)


def _topic_similarity(t1: str, t2: str) -> float:
    return _cosine_sim(_KB_VECTORS.get(t1, {}), _KB_VECTORS.get(t2, {}))


# ═════════════════════════════════════════════════════════════════════════
# CODE DETECTION
# ═════════════════════════════════════════════════════════════════════════

_CODE_INDICATORS = [
    r"\blocal\s+\w+\s*=", r"\bfunction\s*\(", r"\bgame:GetService\b",
    r"\bInstance\.new\b", r"\b:Connect\s*\(", r"\bif\b.*\bthen\b",
    r"\bfor\b.*\bdo\b", r"\bend\b", r"\breturn\b", r"--\[\[",
    r"\bVector3\.new\b", r"\bCFrame\b", r"\bprint\s*\(",
]


def _is_code(text: str) -> bool:
    lines = text.strip().split("\n")
    if len(lines) < 2:
        return False
    code_lines = sum(1 for l in lines if any(re.search(p, l) for p in _CODE_INDICATORS))
    return code_lines / max(len(lines), 1) > 0.35


# ═════════════════════════════════════════════════════════════════════════
# CONVERSATION CONTEXT
# ═════════════════════════════════════════════════════════════════════════

_histories: dict[int, dict] = {}


def _get_ctx(uid: int) -> dict:
    if uid not in _histories:
        _histories[uid] = {"topics": [], "last_q": "", "turns": 0, "msgs": []}
    return _histories[uid]


def _add_context(uid: int, topic: str, question: str):
    ctx = _get_ctx(uid)
    ctx["topics"].append(topic)
    ctx["last_q"] = question
    ctx["turns"] += 1
    ctx["msgs"].append(question)
    if len(ctx["topics"]) > 30:
        ctx["topics"] = ctx["topics"][-30:]
    if len(ctx["msgs"]) > 20:
        ctx["msgs"] = ctx["msgs"][-20:]


def clear_history(uid: int):
    _histories.pop(uid, None)


# ═════════════════════════════════════════════════════════════════════════
# FOLLOW-UP HANDLING
# ═════════════════════════════════════════════════════════════════════════

def _detect_followup(text: str) -> str | None:
    raw = text.lower().strip()
    words = raw.split()
    if len(words) > 6:
        return None
    if re.match(r"^(tell me more|more about|elaborate|explain more|go on|continue|details?|what else)\s*$", raw):
        return "elaborate"
    if re.match(r"^(why|reason|cause)\s*$", raw):
        return "why"
    if re.match(r"^(best|recommend|suggest|should i|which one|which is better)\s*$", raw):
        return "recommend"
    return None


# ═════════════════════════════════════════════════════════════════════════
# RESPONSE GENERATION
# ═════════════════════════════════════════════════════════════════════════

_GREETINGS = [
    "Hey! What's up?",
    "Hi there! Need help with Luau, Roblox, or obfuscation?",
    "Hey! I'm shesfuscator — ask me anything about Roblox dev or obfuscation!",
    "Hello! What can I help you with?",
    "Yo! What's on your mind?",
    "Hey! Ask me about Luau, Roblox APIs, game dev, or obfuscation!",
]

_BYES = [
    "Later! Come back anytime!",
    "Bye! Happy coding!",
    "See ya! Good luck with your project!",
    "Take care! I'll be here if you need me.",
    "Peace! Don't forget to use strong obfuscation!",
]

_HOW_ARE_YOUS = [
    "All systems running smooth! What can I help you with?",
    "Doing great! What do you need?",
    "Running at 100%! What's up?",
    "Perfect! Ready to help with whatever you need.",
]

_THANKS = [
    "You're welcome!",
    "No problem!",
    "Anytime!",
    "Happy to help!",
    "Glad I could help!",
    "No sweat!",
]

_JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs!",
    "There are only 10 types of people: those who understand binary and those who don't.",
    "A SQL query walks into a bar, walks up to two tables and asks: 'Can I join you?'",
    "Why did the Luau developer go broke? Because they used up all their *local* variables!",
    "What's a programmer's favorite hangout place? Foo Bar!",
    "How many programmers does it take to change a light bulb? None — that's a hardware problem!",
    "Why do Roblox scripts never win arguments? Because they always get *stacked*!",
    "I told my computer I needed a break. Now it keeps sending me Kit-Kat ads.",
    "There's no place like 127.0.0.1",
    "A byte walks into a bar. Bartender says 'What can I get you?' Byte says 'Make me a double.'",
]

_YES_RESPONSES = [
    "Got it!",
    "Alright!",
    "Cool!",
    "Sounds good!",
    "Noted!",
]

_NO_RESPONSES = [
    "No worries!",
    "Alright then!",
    "Cool, let me know if you change your mind!",
    "Sure thing!",
]

_FALLBACKS = [
    "I'm not sure about that. Try asking about **obfuscation**, **Roblox APIs**, **Luau programming**, or shesfuscator commands!",
    "Hmm, I don't have info on that. I can help with Luau, Roblox game dev, obfuscation, or how to use this bot!",
    "I don't know much about that one. Try asking about Vmify, presets, DataStores, GUI, combat systems, or any Roblox topic!",
    "That's outside my expertise. I'm best at Luau, Roblox, and obfuscation — try one of those!",
]

_FOLLOWUP_RESPONSES = {
    "elaborate": "Here's more detail on that topic:",
    "why": "The reason is:",
    "recommend": "My recommendation:",
}


def answer_question(question: str, uid: int = 0) -> str:
    ctx = _get_ctx(uid)
    text = question.strip()

    # Empty / too short
    if len(text) <= 1:
        return "Type something! I can help with Luau, Roblox, obfuscation, or just chat."

    # Code detection
    if _is_code(text):
        _add_context(uid, "code", text)
        return _analyze_code(text)

    # Intent classification
    topic, confidence = classify_intent(text, ctx.get("topics", []))

    # Handle dynamic responses
    if topic in ("greet", "bye", "how_are_you", "what_are_you", "thanks", "joke",
                  "yes", "no", "what_are_you", "capabilities"):
        response = _dynamic_response(topic)
        _add_context(uid, topic, text)
        return response

    # Follow-up check
    followup = _detect_followup(text)
    if followup and ctx["topics"]:
        last_topic = ctx["topics"][-1]
        base = KB.get(last_topic, {}).get("response", "")
        if base:
            _add_context(uid, last_topic, text)
            return f"{_FOLLOWUP_RESPONSES.get(followup, 'Here you go:')}\n\n{base}"

    # Confidence check
    if confidence < 0.15 or topic == "fallback":
        _add_context(uid, "fallback", text)
        return random.choice(_FALLBACKS)

    # Get response
    response = KB[topic]["response"]
    _add_context(uid, topic, text)

    # Sometimes add a follow-up question
    if ctx["turns"] > 1 and random.random() < 0.12:
        related = _get_related_topic(topic)
        if related:
            response += f"\n\nWant to know more about **{related}**?"

    return response


def _dynamic_response(topic: str) -> str:
    if topic == "greet":
        return random.choice(_GREETINGS)
    if topic == "bye":
        return random.choice(_BYES)
    if topic == "how_are_you":
        return random.choice(_HOW_ARE_YOUS)
    if topic == "thanks":
        return random.choice(_THANKS)
    if topic == "joke":
        return random.choice(_JOKES)
    if topic == "yes":
        return random.choice(_YES_RESPONSES)
    if topic == "no":
        return random.choice(_NO_RESPONSES)
    if topic == "what_are_you":
        return KB["what_are_you"]["response"]
    if topic == "capabilities":
        return KB["capabilities"]["response"]
    return "Got it!"


def _get_related_topic(topic: str) -> str | None:
    """Find a related topic to suggest."""
    related_map = {
        "vmify": "EncryptStrings", "encrypt_strings": "AntiTamper",
        "anti_tamper": "ConstantArray", "constant_array": "VarRenamer",
        "presets": "best_preset", "best_preset": "performance",
        "obfuscation": "deobfuscation", "deobfuscation": "obfuscation",
        "gui": "tween", "combat": "remotes", "datastore": "saving",
        "players": "remotes", "pcall": "error_handling",
    }
    return related_map.get(topic)


def _analyze_code(code: str) -> str:
    """Analyze pasted Luau code."""
    from analyzer import explain
    try:
        analysis = explain(code)
        return f"**Code Analysis:**\n\n{analysis}"
    except Exception:
        return "I can see that's code, but had trouble analyzing it. Try `/explain` for a detailed breakdown!"


# ═════════════════════════════════════════════════════════════════════════
# QUICK FACTS
# ═════════════════════════════════════════════════════════════════════════

QUICK_FACTS = [
    "The Prometheus engine supports both Lua 5.1 and Luau syntax.",
    "Vmify compiles your code into a custom bytecode VM — the output isn't even valid Lua!",
    "VarRenamer uses lookalike characters (I, l, 1, O, o, 0) to make code unreadable.",
    "Dead code injection adds unreachable blocks that confuse static analyzers.",
    "AntiTamper breaks the script if anyone tries to beautify or modify it.",
    "The Ultra preset runs Vmify twice for maximum protection.",
    "ConstantArray extracts all constants into an encoded table with rotation.",
    "Hex numbers (0x4F) are harder to read than decimal (79) — that's the point.",
    "StringEncoder turns \"hello\" into \"\\104\\101\\108\\108\\111\".",
    "ControlFlow flattening makes execution follow a randomized dispatch table.",
    "shesfuscator can reverse its own custom layers but NOT Prometheus engine steps.",
    "The bot supports files up to 300KB for obfuscation.",
    "Luau is 1-indexed — arrays start at 1, not 0.",
    "DataStoreService calls should always be wrapped in pcall().",
    "The `typeof()` function returns Roblox class names.",
]


def random_fact() -> str:
    return random.choice(QUICK_FACTS)
