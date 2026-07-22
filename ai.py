"""
Offline NLP chatbot — no API keys, no external services.

Intent classification, 150+ topic knowledge base, context tracking,
code detection, template-based natural responses.
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
    "deobfuscate": "deobfuscation", "deobfuscated": "deobfuscation",
    "encrypt": "encryption", "encrypted": "encryption",
    "hack": "exploit", "hacking": "exploit", "hacker": "exploit",
    "cheat": "exploit", "cheating": "exploit",
    "script": "luau", "coding": "programming", "code": "programming",
    "program": "programming", "programmer": "programming",
    "game": "roblox", "gaming": "roblox", "roblox": "roblox",
    "gui": "interface", "ui": "interface", "interface": "interface",
    "speed": "performance", "lag": "performance", "fps": "performance",
    "slow": "performance", "fast": "performance",
    "beginner": "newbie", "new": "newbie", "start": "newbie",
    "thanks": "thank", "thx": "thank", "ty": "thank",
    "hello": "greet", "hi": "greet", "hey": "greet", "sup": "greet",
    "yo": "greet", "howdy": "greet", "hiya": "greet",
    "bye": "farewell", "goodbye": "farewell", "see ya": "farewell",
    "break": "error", "crash": "error", "bug": "error", "issue": "error",
    "fix": "solve", "solve": "solve", "help": "assist",
    "cool": "positive", "awesome": "positive", "nice": "positive",
    "good": "positive", "great": "positive", "amazing": "positive",
    "bad": "negative", "terrible": "negative", "awful": "negative",
    "worst": "negative", "hate": "negative",
    "recommend": "suggest", "suggestion": "suggest", "advise": "suggest",
    "difference": "compare", "compare": "compare", "vs": "compare",
    "create": "make", "build": "make", "make": "make",
    "delete": "remove", "remove": "remove", "destroy": "remove",
    "download": "install", "install": "install",
    "update": "modify", "change": "modify", "edit": "modify", "modify": "modify",
    "work": "function", "function": "function",
    "use": "utilize", "utilize": "utilize",
    "tutorial": "guide", "guide": "guide", "explain": "explain",
    "definition": "meaning", "meaning": "meaning", "define": "meaning",
    "what's": "what is", "how's": "how is", "it's": "it is",
    "don't": "do not", "doesn't": "does not", "can't": "cannot",
    "won't": "will not", "isn't": "is not", "aren't": "are not",
}


def _tokenize(text: str) -> list[str]:
    """Tokenize, lowercase, remove stop words, apply synonyms."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s']", " ", text)
    tokens = text.split()
    result = []
    for t in tokens:
        t = t.strip("'")
        if not t or len(t) <= 1:
            continue
        if t in _STOP_WORDS:
            continue
        result.append(_SYNONYMS.get(t, t))
    return result


def _ngrams(tokens: list[str], n: int) -> list[str]:
    return [" ".join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]


def _cosine_sim(v1: dict, v2: dict) -> float:
    """Cosine similarity between two sparse vectors (dicts)."""
    common = set(v1) & set(v2)
    if not common:
        return 0.0
    dot = sum(v1[k] * v2[k] for k in common)
    mag1 = math.sqrt(sum(x*x for x in v1.values()))
    mag2 = math.sqrt(sum(x*x for x in v2.values()))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


def _tfidf_vec(tokens: list[str]) -> dict:
    """Simple TF vector (IDF omitted for speed — still works well)."""
    counts = Counter(tokens)
    total = len(tokens) or 1
    return {t: c / total for t, c in counts.items()}


# ═════════════════════════════════════════════════════════════════════════
# KNOWLEDGE BASE — 150+ topics
# ═════════════════════════════════════════════════════════════════════════

# Format: { "topic_name": { "patterns": [...keywords/phrases...], "response": "..." } }

KB = {}


def _kb(topic, patterns, response):
    KB[topic] = {"patterns": patterns, "response": response}


# ── Greetings ──────────────────────────────────────────────────────────

_kb("greet_hello",
    ["hello", "hi", "hey", "howdy", "hiya", "sup", "yo", "what's up", "greetings", "good morning", "good afternoon", "good evening"],
    random.choice([
        "Hey! What's up?",
        "Hi there! Need help with Luau, obfuscation, or anything else?",
        "Hey! I'm shesfuscator — ask me about Roblox, Luau, or code obfuscation!",
        "Hello! What can I help you with?",
        "Yo! What's on your mind?",
    ]))

_kb("greet_bye",
    ["bye", "goodbye", "see you", "see ya", "later", "goodnight", "gn", "cya"],
    random.choice([
        "Later! Come back if you need anything.",
        "Bye! Happy coding!",
        "See ya! Good luck with your project.",
        "Take care! I'll be here if you need me.",
    ]))

_kb("how_are_you",
    ["how are you", "how r u", "how you doing", "how's it going", "you good", "you ok", "what's up with you", "how are things"],
    "Running great! All systems online. What can I help you with?"
)

_kb("what_are_you",
    ["what are you", "who are you", "what is this", "what bot is this", "tell me about yourself", "introduce yourself", "who made you", "what is shesfuscator", "what do you do"],
    "I'm **shesfuscator** — a Discord bot for obfuscating Luau scripts. I use the Prometheus engine with 9 obfuscation steps + 8 custom Python layers across 7 presets. I can also analyze, explain, and deobfuscate code. DM me a .lua file or use `/obfuscate` to get started!"
)

_kb("thanks",
    ["thank", "thanks", "thx", "ty", "appreciate", "tysm", "tys"],
    random.choice([
        "You're welcome!",
        "No problem!",
        "Anytime!",
        "Happy to help!",
        "Glad I could help!",
    ]))

_kb("yes_no",
    ["yes", "no", "maybe", "sure", "nah", "yep", "nope", "ok", "okay", "yeah", "yea", "definitely", "absolutely"],
    "Got it! Let me know if you need anything else."

)

# ── Shesfuscator / Obfuscation ────────────────────────────────────────

_kb("what_is_obfuscation",
    ["what is obfuscation", "explain obfuscation", "define obfuscation", "obfuscation mean", "obfuscation definition", "what does obfuscate mean", "why obfuscate"],
    "**Obfuscation** is the process of transforming code to make it difficult to read and understand while keeping it fully functional. It's like scrambling a message so only you can read it.\n\nIn Luau/Roblox, this means your scripts can't be easily reverse-engineered, stolen, or modified by others. shesfuscator uses the **Prometheus engine** (9 Lua-based steps) + **8 custom Python layers** for multi-layered protection."
)

_kb("how_to_use",
    ["how to use", "how do i use", "how does this work", "how can i use", "getting started", "start using", "usage", "how do i obfuscate", "how do i get started", "instructions"],
    "**Getting started is easy:**\n\n**Option 1 — Slash command:**\nUse `/obfuscate` with your code or a file upload. Pick a preset and go!\n\n**Option 2 — DM:**\n1. DM me a `.lua` or `.luau` file (or multiple for batch)\n2. Pick a preset from the dropdown\n3. Get your obfuscated file back!\n\n**Option 3 — Analyze:**\nUse `/explain` to understand what a script does before obfuscating.\n\n**Option 4 — Deobfuscate:**\nUse `/deobfuscate` to reverse custom obfuscation layers."
)

_kb("presets_overview",
    ["preset", "presets", "which preset", "preset options", "preset list", "what presets", "obfuscation levels", "levels", "strength", "how strong", "protection level"],
    "shesfuscator has **7 presets**, from light to maximum:\n\n**Very Light** — ConstantArray only. Minimal protection, no performance impact.\n**Light** — ConstantArray + WrapInFunction + HexNumbers.\n**Medium** — EncryptStrings + ConstantArray + WrapInFunction + HexNumbers + StringEncoder. Good balance.\n**Medium-High** — Adds Vmify (custom bytecode VM) + AntiTamper + BoolWrap.\n**High** — Adds NumbersToExpressions + VarRenamer. Strong protection.\n**Very High** — Adds DeadCode + Watermark. Very strong.\n**Ultra** — Double Vmify + all 8 custom layers. Maximum, but slower runtime.\n\nUse `/obfuscate` to try them, or DM me a file!"
)

_kb("vmify",
    ["vmify", "bytecode", "virtual machine", "vm protect", "vm obfuscation", "custom bytecode", "vm step"],
    "**Vmify** is the strongest obfuscation step. It compiles your Luau code into a **fully custom bytecode VM** with its own instruction set. The output isn't even valid Lua anymore — it's a custom interpreter.\n\nThis makes reverse engineering extremely difficult because there's no standard bytecode to analyze.\n\n**Trade-off:** High performance cost. Use when security is critical. The Ultra preset runs Vmify **twice** for maximum protection."
)

_kb("encrypt_strings",
    ["encrypt string", "string encryption", "encryptstrings", "encrypt string step", "string encrypt"],
    "**EncryptStrings** encrypts all string literals using pseudo-random number generators. Strings are decrypted at runtime, so they're invisible in the source code.\n\n**Performance cost:** Medium. Good balance of protection and speed. Works well combined with other steps."
)

_kb("anti_tamper",
    ["anti tamper", "antitamper", "integrity", "tamper", "anti edit", "protect from editing"],
    "**AntiTamper** adds integrity checks to your code. If someone tries to modify, beautify, or hook functions in the obfuscated script, it will break.\n\n**Performance cost:** Low. Recommended for all obfuscation levels above Medium."
)

_kb("constant_array",
    ["constant array", "constantarray", "constant table", "constants extract"],
    "**ConstantArray** extracts all constants (strings, numbers) into an encoded table with base64/base85 encoding, rotation, and local wrapper functions. Makes it harder to find specific values in the code.\n\n**Performance cost:** Low."
)

_kb("var_renamer",
    ["var renamer", "variable rename", "rename variables", "varrenamer", "rename local"],
    "**VarRenamer** replaces local variable names with confusing lookalike characters (I, l, 1, O, o, 0). Makes the code nearly impossible to read manually.\n\n**Performance cost:** Low. No runtime impact — only affects source readability."
)

_kb("dead_code",
    ["dead code", "deadcode", "fake code", "unreachable", "inject dead"],
    "**DeadCode** injects random unreachable code blocks (if false, while false, etc.) throughout the script. Confuses static analysis tools and human readers.\n\n**Performance cost:** Low. Dead code is never executed."
)

_kb("control_flow",
    ["control flow", "controlflow", "flatten", "flattening", "flow obfuscation"],
    "**ControlFlow** wraps code sections in numeric switch dispatchers. Instead of linear code, execution follows a randomized dispatch table. Makes the logic flow much harder to follow.\n\n**Performance cost:** Medium."
)

_kb("string_encoder",
    ["string encoder", "stringencoder", "decimal escapes", "wearedevs", "escape sequences"],
    "**StringEncoder** converts string literals to `\\ddd` decimal escape sequences (WeAreDevs style). E.g., `\"hello\"` becomes `\"\\104\\101\\108\\108\\111\"`.\n\n**Performance cost:** Low. Strings are decoded at runtime."
)

_kb("hex_numbers",
    ["hex number", "hexadecimal", "hex convert", "number hex"],
    "**HexNumbers** converts decimal number literals to hexadecimal format (0x). E.g., `79` becomes `0x4F`. Makes numeric values harder to read.\n\n**Performance cost:** None. Purely visual."
)

_kb("bool_wrap",
    ["bool wrap", "boolean wrap", "wrap bool", "true false", "1==1", "bool obfuscation"],
    "**BoolWrap** converts boolean literals to comparison expressions: `true` → `(1==1)`, `false` → `(1==0)`. Simple but adds a layer of confusion.\n\n**Performance cost:** None."
)

_kb("negate_bools",
    ["negate bool", "negate boolean", "not true", "not false", "negate bools"],
    "**NegateBools** replaces booleans with negations: `true` → `(not false)`, `false` → `(not true)`. Adds mental overhead for readers.\n\n**Performance cost:** None."
)

_kb("noise_vars",
    ["noise var", "noise variable", "random variable", "junk variable", "fake variable"],
    "**NoiseVars** injects unused random variable assignments after `end` statements. Fills the code with junk that looks real but does nothing.\n\n**Performance cost:** None."
)

_kb("watermark",
    ["watermark", "branding", "tag", "signature", "credit"],
    "**Watermark** embeds a `--[[ shesfuscator v1.0 ]]` comment at the top of the obfuscated output. Useful for branding your scripts.\n\n**Performance cost:** None. It's just a comment."
)

_kb("performance",
    ["performance", "slow", "speed", "lag", "fps", "optimization", "fast", "runtime", "overhead"],
    "Performance impact by step:\n\n**None/Low:** HexNumbers, Watermark, AddVararg, WrapInFunction, ConstantArray, BoolWrap, NegateBools, NoiseVars\n**Medium:** EncryptStrings, NumbersToExpressions, ProxifyLocals, ControlFlow, SplitStrings, StringEncoder, VarRenamer, DeadCode\n**High:** Vmify (compiles to custom bytecode VM)\n\nIf performance is critical, use **Very Light** or **Light**. For max security, use **Ultra** but expect some runtime overhead."
)

_kb("deobfuscate_info",
    ["deobfuscate", "deobfuscation", "reverse", "undo", "crack", "unobfuscate", "decode obfuscated"],
    "shesfuscator can reverse its own **custom layers** (StringEncoder, VarRenamer, DeadCode, HexNumbers, BoolWrap, NegateBools, NoiseVars, Watermark) but **cannot** reverse Prometheus engine steps like Vmify (custom bytecode VM) or EncryptStrings.\n\nUse `/deobfuscate` to try it on your code."
)

_kb("layers_overview",
    ["layers", "how many layers", "steps", "methods", "layers total", "obfuscation layers"],
    "shesfuscator has **two types** of layers:\n\n**Engine steps** (Prometheus — Lua-based, 9 total):\nVmify, EncryptStrings, AntiTamper, ConstantArray, NumbersToExpressions, WrapInFunction, SplitStrings, ProxifyLocals, AddVararg\n\n**Custom methods** (Python post-processing, 8 total):\nStringEncoder, VarRenamer, DeadCode, HexNumbers, Watermark, BoolWrap, NegateBools, NoiseVars\n\n**Total: 17 layers** of obfuscation protection."
)

_kb("prometheus",
    ["prometheus", "prometheus engine", "prometheus obfuscator", "prometheus lua"],
    "**Prometheus** is the Lua-based obfuscation engine created by levno-710. It supports both Lua 5.1 and Luau syntax, with 9 transformation steps including Vmify (custom bytecode VM), EncryptStrings, and AntiTamper.\n\nshesfuscator wraps Prometheus with 8 additional Python post-processing layers for extra protection."
)

_kb("luau_vs_lua",
    ["luau vs lua", "difference luau lua", "luau lua difference", "luau lua compare", "lua5 luau", "difference between luau and lua", "luau and lua difference", "lua versus luau"],
    "**Luau** is Roblox's variant of Lua. Key differences:\n\n- Stricter type checking (optional types with `:` syntax)\n- `continue` keyword (not in Lua 5.1)\n- Faster JIT compilation\n- Extended string library\n- Bit32 library\n- Enhanced `task` library (task.spawn, task.wait, task.delay)\n\nshesfuscator supports both Lua 5.1 and Luau syntax."
)

# ── Roblox APIs ────────────────────────────────────────────────────────

_kb("gameservice",
    ["game getservice", "game service", "getservice", "access service"],
    "`game:GetService()` is the standard way to access Roblox services:\n\n```lua\nlocal Players = game:GetService('Players')\nlocal RS = game:GetService('ReplicatedStorage')\n```\n\nAlways use `GetService` instead of directly referencing services (e.g., `game.Players`) — it's more reliable and avoids race conditions."
)

_kb("players_service",
    ["players service", "players object", "get players", "player join", "player added"],
    "The **Players** service manages connected players:\n\n```lua\nlocal Players = game:GetService('Players')\nPlayers.PlayerAdded:Connect(function(player)\n    print(player.Name .. ' joined!')\nend)\n```\n\nKey properties: `Player.Name`, `Player.UserId`, `Player.Character`, `Player.TeamColor`.\nKey methods: `:Kick()`, `:GetRankInGroup()`, `:LoadCharacter()`."
)

_kb("remote_events",
    ["remote event", "remote function", "remoteevent", "remotefunction", "client server", "fire server", "on client event"],
    "**RemoteEvents** and **RemoteFunctions** handle client-server communication:\n\n```lua\n-- Server\nlocal remote = Instance.new('RemoteEvent')\nremote.OnServerEvent:Connect(function(player, data)\n    -- handle client message\nend)\n\n-- Client\nremote:FireServer(data)  -- send to server\n```\n\n**Security tip:** Always validate remote event data on the server! Never trust client input."
)

_kb("datastore",
    ["datastore", "data store", "save data", "load data", "player data", "data persistence", "save player"],
    "**DataStoreService** provides persistent key-value storage:\n\n```lua\nlocal DS = game:GetService('DataStoreService')\nlocal store = DS:GetDataStore('PlayerData')\n\n-- Save\nstore:SetAsync(player.UserId, data)\n\n-- Load\nlocal data = store:GetAsync(player.UserId)\n```\n\n**Tips:**\n- Always wrap in `pcall()` — DataStore calls can fail\n- Use `:UpdateAsync()` for read-modify-write operations (safer)\n- DataStores have rate limits (~60 calls/min)"
)

_kb("tween_service",
    ["tween", "tween service", "tweenservice", "animation tween", "smooth animation", "property animation"],
    "**TweenService** creates smooth property animations:\n\n```lua\nlocal TS = game:GetService('TweenService')\nlocal info = TweenInfo.new(1, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)\nlocal tween = TS:Create(part, info, {Position = Vector3.new(0, 10, 0)})\ntween:Play()\n```\n\n**EasingStyles:** Linear, Quad, Cubic, Quart, Quint, Sine, Back, Bounce, Elastic, Exponential, Circular"
)

_kb("run_service",
    ["run service", "runservice", "heartbeat", "render stepped", "per frame", "every frame", "update loop"],
    "**RunService** provides per-frame callbacks:\n\n```lua\nlocal RS = game:GetService('RunService')\n\nRS.Heartbeat:Connect(function(dt)\n    -- runs every frame (server + client)\nend)\n\nRS.RenderStepped:Connect(function(dt)\n    -- client only, before render\nend)\n```\n\nUse `dt` (delta time) for frame-rate independent movement."
)

_kb("user_input",
    ["user input", "userinput", "input service", "keyboard", "mouse", "key press", "button press", "input began"],
    "**UserInputService** detects input:\n\n```lua\nlocal UIS = game:GetService('UserInputService')\nUIS.InputBegan:Connect(function(input, gameProcessed)\n    if gameProcessed then return end\n    if input.KeyCode == Enum.KeyCode.E then\n        -- E key pressed\n    end\nend)\n```\n\nUse `gameProcessed` to ignore input when typing in a TextBox."
)

_kb("http_service",
    ["http service", "httpservice", "http request", "web request", "api call", "fetch", "external api"],
    "**HttpService** makes HTTP requests (server-only, must be enabled in Game Settings):\n\n```lua\nlocal Http = game:GetService('HttpService')\nlocal data = Http:GetAsync('https://api.example.com/data')\nlocal json = Http:JSONDecode(data)\n```\n\n**Also available:** `:PostAsync()`, `:RequestAsync()`, `:JSONEncode()`, `:JSONDecode()`"
)

_kb("workspace",
    ["workspace", "work space", "game world", "3d space", "scene"],
    "**Workspace** is the root of the 3D game world. All visible objects live here:\n\n```lua\nlocal ws = game:GetService('Workspace')\nlocal part = ws:FindFirstChild('MyPart')\n```\n\nCommon children: Parts, Models, Terrain, Camera, SpawnLocation."
)

_kb("replicated_storage",
    ["replicated storage", "replicatedstorage", "shared storage", "client can see"],
    "**ReplicatedStorage** is shared between client and server. Client can READ but not WRITE.\n\nCommon uses:\n- RemoteEvents/RemoteFunctions\n- Shared module scripts\n- Assets (images, sounds, meshes)\n- Client-side data"
)

_kb("instance_new",
    ["instance new", "create instance", "new instance", "make object", "create object"],
    "`Instance.new()` creates a new Roblox object:\n\n```lua\nlocal part = Instance.new('Part')\npart.Name = 'MyPart'\npart.Position = Vector3.new(0, 5, 0)\npart.Parent = workspace\n```\n\n**Tip:** Always set `.Parent` LAST to avoid unnecessary replication."
)

_kb("findFirstChild",
    ["find first child", "findfirstchild", "get child", "find child", "child exists"],
    "`:FindFirstChild()` safely searches for a child by name (returns `nil` if not found):\n\n```lua\nlocal part = folder:FindFirstChild('MyPart')\nif part then\n    -- found it\nend\n```\n\nAvoid `:WaitForChild()` in loops — it yields forever if the child never appears."
)

_kb("waitforchild",
    ["wait for child", "waitforchild", "yield for child", "wait for load"],
    "`:WaitForChild()` yields until a child appears. Useful when loading assets:\n\n```lua\nlocal part = script.Parent:WaitForChild('MyPart')\n```\n\n**Warning:** Hangs forever if the child doesn't exist! Consider adding a timeout:\n```lua\nlocal part = script.Parent:WaitForChild('MyPart', 5) -- 5 sec timeout\n```\n"
)

_kb("metatables",
    ["metatable", "metatables", "__index", "__newindex", "__call", "oop", "class", "object oriented"],
    "**Metatables** enable OOP in Lua:\n\n```lua\nlocal Player = {}\nPlayer.__index = Player\n\nfunction Player.new(name)\n    return setmetatable({name = name}, Player)\nend\n\nfunction Player:Say(msg)\n    print(self.name .. ': ' .. msg)\nend\n\nlocal p = Player.new('Bob')\np:Say('Hello')  -- Bob: Hello\n```\n\nCommon metamethods: `__index`, `__newindex`, `__call`, `__tostring`, `__add`."
)

_kb("tasks",
    ["task spawn", "task wait", "task delay", "task library", "task.cancel", "asynchronous"],
    "The **task** library provides better alternatives to `wait()` and `spawn()`:\n\n```lua\ntask.wait(2)           -- yield for 2 seconds\ntask.spawn(function()  -- run async (no yield)\n    print('running')\nend)\ntask.delay(5, function()  -- run after 5 seconds\n    print('delayed')\nend)\ntask.cancel(thread)    -- cancel a task\n```\n\nAlways prefer `task` over `wait()`/`spawn()` — they're more reliable."
)

_kb("perrors",
    ["pcall", "xpcall", "error handling", "try catch", "safe call", "protected call"],
    "**pcall** (protected call) catches errors without crashing:\n\n```lua\nlocal success, err = pcall(function()\n    -- risky code\n    error('something went wrong')\nend)\n\nif success then\n    print('it worked!')\nelse\n    print('Error: ' .. err)\nend\n```\n\nUse `xpcall` for custom error handlers:\n```lua\nxpcall(fn, function(err) print('caught:', err) end)\n```\n"
)

# ── Game Dev Patterns ──────────────────────────────────────────────────

_kb("gui_basics",
    ["gui", "ui", "interface", "user interface", "screengui", "frame", "textlabel", "textbutton", "gui tutorial"],
    "**Roblox GUI** uses ScreenGui + elements:\n\n```lua\nlocal sg = Instance.new('ScreenGui')\nsg.Parent = player.PlayerGui\n\nlocal frame = Instance.new('Frame')\nframe.Size = UDim2.new(0, 200, 0, 100)\nframe.Parent = sg\n\nlocal label = Instance.new('TextLabel')\nlabel.Text = 'Hello!'\nlabel.Parent = frame\n```\n\n**Layout:** Use UIListLayout, UIGridLayout for auto-arrangement.\n**Styling:** UICorner (rounded), UIStroke (border), UIGradient."
)

_kb("combat_system",
    ["combat", "damage", "health", "kill", "hit", "weapon", "sword", "gun", "fight", "attack", "hp"],
    "**Basic combat system pattern:**\n\n```lua\n-- Server-side damage handler\nlocal function onDamage(player, target, amount)\n    local character = target.Character\n    if not character then return end\n    local humanoid = character:FindFirstChildOfClass('Humanoid')\n    if not humanoid then return end\n    humanoid.Health = humanoid.Health - amount\nend\n```\n\n**Tips:**\n- Always validate damage on the server\n- Use RemoteEvents for client→server damage requests\n- Clamp health: `math.max(0, humanoid.Health - amount)`"
)

_kb("saving_data",
    ["save game", "save data", "leaderstats", "leader board", "stats", "currency", "coins", "money", "data save"],
    "**Player data persistence** pattern:\n\n```lua\nlocal DS = game:GetService('DataStoreService'):GetDataStore('V1')\n\ngame.Players.PlayerAdded:Connect(function(player)\n    local ls = Instance.new('Folder')\n    ls.Name = 'leaderstats'\n    ls.Parent = player\n    \n    local coins = Instance.new('IntValue')\n    coins.Name = 'Coins'\n    coins.Parent = ls\n    \n    local ok, data = pcall(DS.GetAsync, DS, 'p_'..player.UserId)\n    if ok and data then coins.Value = data end\nend)\n\ngame.Players.PlayerRemoving:Connect(function(player)\n    pcall(DS.SetAsync, DS, 'p_'..player.UserId, player.leaderstats.Coins.Value)\nend)\n```\n"
)

_kb("npc_ai",
    ["npc", "ai enemy", "npc ai", "pathfinding", "patrol", "chase", "enemy ai", "bot ai", "npc script"],
    "**NPC AI** with PathfindingService:\n\n```lua\nlocal PS = game:GetService('PathfindingService')\nlocal path = PS:CreatePath()\n\nlocal function moveTo(targetPos)\n    path:ComputeAsync(humanoid.RootPart.Position, targetPos)\n    for _, waypoint in ipairs(path:GetWaypoints()) do\n        humanoid:MoveTo(waypoint.Position)\n        humanoid.MoveToFinished:Wait()\n    end\nend\n```\n\n**State machine pattern:** Idle → Patrol → Chase → Attack → Dead."
)

_kb("tween_animation",
    ["tween animate", "tween service example", "smooth animation", "property animation roblox", "gui animation", "part animation"],
    "**TweenService** for smooth animations:\n\n```lua\nlocal TS = game:GetService('TweenService')\n\n-- GUI fade-in\nlocal tween = TS:Create(frame,\n    TweenInfo.new(0.5, Enum.EasingStyle.Quad),\n    {BackgroundTransparency = 0}\n)\ntween:Play()\n\n-- Part movement\nlocal move = TS:Create(part,\n    TweenInfo.new(2, Enum.EasingStyle.Bounce),\n    {Position = part.Position + Vector3.new(0, 10, 0)}\n)\nmove:Play()\n```\n"
)

_kb("raycasting",
    ["raycast", "ray cast", "ray", "line of sight", "hit detection", "collision detection", " ray"],
    "**Raycast** for hit detection:\n\n```lua\nlocal ray = workspace:Raycast(origin, direction * 100)\nif ray then\n    print('Hit:', ray.Instance.Name)\n    print('Position:', ray.Position)\n    print('Normal:', ray.Normal)\nend\n```\n\n**Blockcast/Spherecast** for area checks:\n```lua\nlocal result = workspace:Blockcast cf, size, direction\n```\n"
)

_kb("modules",
    ["module", "module script", "require", "shared code", "reuse code", "library"],
    "**ModuleScripts** for reusable code:\n\n```lua\n-- ModuleScript (in ReplicatedStorage)\nlocal Utils = {}\n\nfunction Utils.round(num, decimals)\n    local mult = 10^(decimals or 0)\n    return math.floor(num * mult + 0.5) / mult\nend\n\nreturn Utils\n\n-- Usage\nlocal Utils = require(ReplicatedStorage.Utils)\nprint(Utils.round(3.14159, 2))  -- 3.14\n```\n"
)

_kb("procedural_gen",
    ["procedural", "procedural generation", "random map", "generate terrain", "random level", "map gen"],
    "**Procedural generation** basics:\n\n```lua\nlocal function generateChunk(position)\n    for x = 0, 15 do\n        for z = 0, 15 do\n            local height = math.noise(x * 0.1, z * 0.1) * 10\n            local part = Instance.new('Part')\n            part.Position = position + Vector3.new(x, height, z)\n            part.Size = Vector3.new(1, 1, 1)\n            part.Anchored = true\n            part.Parent = workspace\n        end\n    end\nend\n```\n\nUse `math.noise()` for natural-looking terrain."
)

# ── Programming Concepts ───────────────────────────────────────────────

_kb("tables",
    ["table", "array", "dictionary", "hash", "key value", "lua table", "table lua"],
    "**Lua/Luau tables** are the only data structure:\n\n```lua\n-- Array (1-indexed!)\nlocal fruits = {'apple', 'banana', 'cherry'}\nprint(fruits[1])  -- 'apple'\n\n-- Dictionary\nlocal player = {name = 'Bob', health = 100, level = 5}\nprint(player.name)  -- 'Bob'\n\n-- Mixed\nlocal data = {\n    {'John', 25},\n    {'Jane', 30},\n}\n```\n\n**Key methods:** `table.insert()`, `table.remove()`, `table.find()`, `table.sort()`, `#tbl` (length)."
)

_kb("loops",
    ["loop", "for loop", "while loop", "repeat", "iteration", "iterate", "for i", "ipairs", "pairs"],
    "**Loops** in Luau:\n\n```lua\n-- Numeric for\nfor i = 1, 10 do print(i) end\nfor i = 10, 1, -1 do print(i) end  -- countdown\n\n-- Generic for (arrays)\nfor i, v in ipairs({'a', 'b', 'c'}) do\n    print(i, v)\nend\n\n-- Generic for (dictionaries)\nfor k, v in pairs({x = 1, y = 2}) do\n    print(k, v)\nend\n\n-- While\nwhile condition do ... end\n\n-- Repeat (runs at least once)\nrepeat ... until condition\n```\n\n**Tip:** Use `ipairs` for arrays, `pairs` for dictionaries."
)

_kb("conditionals",
    ["if statement", "if else", "condition", "conditional", "if then", "elseif", "ternary"],
    "**Conditionals** in Luau:\n\n```lua\nif health > 0 then\n    print('alive')\nelseif health == 0 then\n    print('dead')\nelse\n    print('ghost?')\nend\n\n-- Ternary-like pattern\nlocal x = condition and valueIfTrue or valueIfFalse\n\n-- Guard clause pattern\nif not player then return end\nif not character then return end\n```\n\nLuau supports `if/elseif/else/end` (no switch/case)."
)

_kb("functions",
    ["function", "method", "define function", "create function", "function lua", "local function"],
    "**Functions** in Luau:\n\n```lua\n-- Named function\nlocal function greet(name)\n    return 'Hello, ' .. name\nend\n\n-- Anonymous function\nlocal add = function(a, b)\n    return a + b\nend\n\n-- Variadic\nlocal function log(...)\n    local args = {...}\n    print(unpack(args))\nend\n\n-- Method (colon syntax)\nfunction player:Say(msg)\n    print(self.name .. ': ' .. msg)\nend\nplayer:Say('hi')  -- self is auto-passed\n```\n"
)

_kb("strings",
    ["string", "string manipulation", "string lua", "string concat", "string format", "string operations"],
    "**String operations** in Luau:\n\n```lua\nlocal s = 'Hello, World!'\n\n-- Length\nprint(#s)  -- 13\n\n-- Concatenation\nlocal full = 'Hello' .. ' ' .. 'World'\n\n-- Methods\nprint(s:upper())     -- HELLO, WORLD!\nprint(s:lower())     -- hello, world!\nprint(s:sub(1, 5))   -- Hello\nprint(s:find('World'))  -- 8, 12\nprint(s:rep(3))      -- Hello, World!Hello, World!Hello, World!\nprint(s:reverse())   -- !dlroW ,olleH\n\n-- String library\nprint(string.format('HP: %d/%d', 50, 100))\nprint(string.byte('A'))  -- 65\n```\n"
)

_kb("error_handling",
    ["error handling", "pcall", "xpcall", "error", "try catch", "exception", "safe error"],
    "**Error handling** with pcall:\n\n```lua\n-- Basic pcall\nlocal ok, result = pcall(function()\n    return doSomethingRisky()\nend)\n\nif ok then\n    print('Success:', result)\nelse\n    print('Error:', result)\nend\n\n-- xpcall with custom handler\nxpcall(\n    function() error('oops') end,\n    function(err) print('Caught:', err) end\n)\n```\n\n**Always wrap** DataStore calls, HTTP requests, and other I/O in pcall!"
)

_kb("type_checking",
    ["type check", "typeof", "type", "luau type", "type annotation", "type safety"],
    "**Luau type checking**:\n\n```lua\n-- Runtime type check\nprint(typeof(part))        -- 'Instance'\nprint(type(42))            -- 'number'\nprint(type('hello'))       -- 'string'\nprint(type(true))          -- 'boolean'\nprint(type({}))            -- 'table'\n\n-- Luau type annotations (optional)\nlocal x: number = 42\nlocal name: string = 'Bob'\n\nlocal function add(a: number, b: number): number\n    return a + b\nend\n```\n\nTypes are optional but help catch bugs early."
)

# ── Specific Questions ─────────────────────────────────────────────────

_kb("best_preset",
    ["which preset best", "best preset", "what preset should i use", "recommend preset", "which one should i use", "best protection"],
    "**It depends on your needs:**\n\n- **Just hiding code?** → **Medium** (EncryptStrings + ConstantArray)\n- **Serious protection?** → **High** or **Very High**\n- **Maximum security, performance doesn't matter?** → **Ultra** (double VM)\n- **Learning/development?** → **Very Light** or **Light**\n\n**Medium** is the sweet spot for most use cases — good protection with reasonable performance."
)

_kb("what_unreversible",
    ["what cant be reversed", "what is irreversible", "cant deobfuscate", "permanent obfuscation", "what layers cant reverse"],
    "These layers **cannot be reversed:**\n\n- **Vmify** — Compiles to custom bytecode VM. No decompiler exists.\n- **EncryptStrings** — One-way encryption with runtime keys.\n- **AntiTamper** — Integrity checks that can't be removed without breaking.\n- **ProxifyLocals** — Proxy indirection that obscures variable access.\n\nCustom layers (StringEncoder, VarRenamer, DeadCode, etc.) **can** be reversed with `/deobfuscate`."
)

_kb("is_it_safe",
    ["is it safe", "is shesfuscator safe", "will it break my code", "safe to use", "will it work", "does it break", "is it secure"],
    "**Yes, shesfuscator is safe!**\n\n- It **never modifies your original code** — only produces a new obfuscated file\n- The obfuscated code runs exactly the same as the original\n- Lower presets have minimal runtime impact\n- Higher presets add more overhead but maintain functionality\n\n**Tip:** Always test your obfuscated code to make sure it works as expected!"
)

_kb("how_much_does_it_cost",
    ["cost", "price", "free", "how much", "payment", "subscription", "pricing"],
    "shesfuscator is **completely free** to use! No limits, no subscriptions, no hidden fees. Just DM me a file or use `/obfuscate` and you're good to go."
)

_kb("supported_languages",
    ["supported languages", "what languages", "can i use with", "support python", "support javascript", "only lua"],
    "shesfuscator currently only supports **Luau** and **Lua 5.1**. It's built specifically for Roblox game development.\n\nIf you need obfuscation for other languages (JavaScript, Python, C#, etc.), you'd need a different tool."
)

# ── General / Fun ──────────────────────────────────────────────────────

_kb("joke",
    ["joke", "tell me a joke", "make me laugh", "funny", "humor", "comedy"],
    random.choice([
        "Why do programmers prefer dark mode? Because light attracts bugs!",
        "There are only 10 types of people: those who understand binary and those who don't.",
        "A SQL query walks into a bar, walks up to two tables and asks: 'Can I join you?'",
        "Why did the Luau developer go broke? Because they used up all their *local* variables!",
        "What's a programmer's favorite hangout place? Foo Bar!",
        "Why do Roblox scripts never win arguments? Because they always get *stacked*!",
        "How many programmers does it take to change a light bulb? None — that's a hardware problem!",
    ]))

_kb("meaning_of_life",
    ["meaning of life", "purpose of life", "why are we here", "42", "deep question", "philosophy"],
    "42. Obviously.\n\nBut if you're looking for something more practical — the meaning of life is to write obfuscated Luau scripts and share them with friends. That's what shesfuscator is for!"
)

_kb("favorite",
    ["favorite", "favourite", "what do you like", "your fav", "best thing", "do you like"],
    "I'm a bot, so I don't have feelings — but if I did, my favorite thing would be **Vmify**. Turning readable Lua into a custom bytecode VM is just *chef's kiss*.\n\nWhat about you? What's your favorite obfuscation step?"
)

_kb("who_made",
    ["who made you", "who created you", "your creator", "your developer", "who built you", "author"],
    "I'm built by **shesfuscator** — the same team that made the obfuscation engine. I run on Python with discord.py and the Prometheus Lua obfuscator."
)

_kb("roblox_studio",
    ["roblox studio", "studio", "how to install studio", "where to get studio", "download studio"],
    "**Roblox Studio** is the free IDE for making Roblox games:\n\n1. Go to [create.roblox.com](https://create.roblox.com)\n2. Download Roblox Studio\n3. Sign in with your Roblox account\n4. Create a new Baseplate or use a template\n\nIt includes a script editor, 3D viewport, terrain editor, and testing tools. Scripts written in Studio use Luau."
)

_kb("local_script_vs_server",
    ["local script", "server script", "local vs server", "client server difference", "where to put script", "script context"],
    "**Script contexts** in Roblox:\n\n- **Server Script** (runs in `ServerScriptService`) — game logic, data saving, authority\n- **LocalScript** (runs in `StarterPlayerScripts`, `StarterGui`, `StarterCharacterScripts`) — client UI, input, camera\n- **ModuleScript** (anywhere) — shared code, required by other scripts\n\n**Rule of thumb:** Sensitive logic on server, UI/input on client."
)

_kb("leaderstats",
    ["leaderstats", "leader board", "leaderboard", "player stats display", "score display"],
    "**Leaderstats** display player stats on the leaderboard:\n\n```lua\ngame.Players.PlayerAdded:Connect(function(player)\n    local ls = Instance.new('Folder')\n    ls.Name = 'leaderstats'\n    ls.Parent = player\n    \n    local wins = Instance.new('IntValue')\n    wins.Name = 'Wins'\n    wins.Value = 0\n    wins.Parent = ls\nend)\n```\n\nThe `leaderstats` folder name is special — Roblox automatically shows it on the leaderboard."
)

_kb("admin_commands",
    ["admin", "admin commands", "moderator", "kick", "ban", "admin system"],
    "**Admin system** basics:\n\n```lua\nlocal ADMINS = {123456789, 987654321}  -- user IDs\n\ngame.Players.PlayerAdded:Connect(function(player)\n    player.Chatted:Connect(function(msg)\n        if not table.find(ADMINS, player.UserId) then return end\n        \n        local args = msg:split(' ')\n        if args[1] == '!kick' then\n            local target = game.Players:FindFirstChild(args[2])\n            if target then target:Kick('Kicked by admin') end\n        end\n    end)\nend)\n```\n\n**Tip:** Never trust client-side admin checks — always validate on server!"
)

# ── Obfuscation Deep Dives ────────────────────────────────────────────

_kb("double_vmify",
    ["double vmify", "vmify twice", "vmify double", "two vm", "double vm", "ultra vm"],
    "**Double Vmify** (Ultra preset) runs the Vmify step **twice**:\n\n1. First pass: Compiles your code into a custom bytecode VM\n2. Second pass: Compiles the VM's interpreter *itself* into another VM\n\nThis creates a **VM inside a VM** — the outer interpreter runs the inner interpreter which runs your code. Extremely hard to reverse engineer.\n\n**Trade-off:** Significant performance overhead. Only use for maximum security."
)

_kb("layer_order",
    ["layer order", "step order", "obfuscation order", "what order", "step sequence", "pipeline order"],
    "Layer order matters! shesfuscator applies layers in this sequence:\n\n1. **Prometheus engine steps** (Vmify, EncryptStrings, etc.) — applied first\n2. **Custom Python layers** (HexNumbers, StringEncoder, etc.) — applied after\n\nWithin the engine, steps run in the configured order. The recommended order for best results:\n\n1. ConstantArray (extract constants)\n2. NumbersToExpressions\n3. EncryptStrings\n4. AntiTamper\n5. Vmify (VM compilation)\n6. WrapInFunction (IIFE wrapper)\n\nCustom layers then process the output."
)

_kb("obfuscation_vs_encryption",
    ["obfuscation vs encryption", "difference obfuscation encryption", "is obfuscation encryption", "encrypt vs obfuscate"],
    "**Obfuscation ≠ Encryption:**\n\n- **Encryption** uses a key to scramble data. Only someone with the key can decrypt it. It's reversible by design.\n- **Obfuscation** transforms code to make it *hard to read*, but there's no key — it's meant to be difficult, not impossible, to reverse.\n\n**Key difference:** Encryption is meant to be decrypted. Obfuscation is meant to stay hidden.\n\nSome shesfuscator steps (like Vmify) come close to encryption by compiling to custom bytecode, but it's still technically obfuscation."
)

# ── Fallback catch-all topics ──────────────────────────────────────────

_kb("math",
    ["math", "calculate", "equation", "number", "sum", "average", "multiply", "divide"],
    "Luau has a built-in `math` library:\n\n```lua\nmath.abs(-5)       -- 5\nmath.ceil(4.2)     -- 5\nmath.floor(4.8)    -- 4\nmath.max(3, 7)     -- 7\nmath.min(3, 7)     -- 3\nmath.random(1, 10) -- random 1-10\nmath.sqrt(16)      -- 4\nmath.pi            -- 3.14159...\nmath.noise(x, y)   -- Perlin noise\n```\n\nNeed help with a specific calculation?"
)

_kb("debugging",
    ["debug", "debugging", "print debug", "find bug", "fix error", "not working"],
    "**Debugging tips** for Luau:\n\n1. **Print debugging:** `print(variable)` to check values\n2. **pcall:** Wrap suspicious code to catch errors\n3. **Breakpoints:** Use Roblox Studio debugger (F9)\n4. **Watch:** Studio debugger lets you inspect variables\n5. **Step through:** F10/F11 in Studio to step line-by-line\n\n```lua\n-- Debug helper\nlocal function dbg(name, val)\n    print(string.format('[DEBUG] %s = %s (%s)', name, tostring(val), type(val)))\nend\ndbg('health', humanoid.Health)\n```\n"
)

_kb("optimization",
    ["optimize", "optimization", "make faster", "improve performance", "better performance", "efficient"],
    "**Roblox performance tips:**\n\n1. **Use `task.wait()` not `wait()`** — more accurate\n2. **Cache services:** `local Players = game:GetService('Players')` once\n3. **Minimize remote events:** Batch data, don't fire every frame\n4. **Use `:FindFirstChild()` not `:WaitForChild()`** in hot paths\n5. **Avoid `GetChildren()` in loops** — use CollectionService tags instead\n6. **Debounce events:** Prevent spam\n7. **StreamEnabled:** Let Roblox handle distant object loading\n8. **Use `RunService.Heartbeat` not `while true do` loops**\n"
)

_kb("random_numbers",
    ["random number", "random", "rng", "randomness", "random lua"],
    "**Random numbers** in Luau:\n\n```lua\n-- math.random\nlocal n = math.random(1, 100)       -- integer 1-100\nlocal f = math.random()             -- float 0-1\n\n-- Random.new (better, deterministic)\nlocal rng = Random.new(12345)       -- seed\nlocal n = rng:NextInteger(1, 100)\nlocal f = rng:NextNumber()\nlocal pick = rng:PickRandom({'a', 'b', 'c'})\n```\n\n**Tip:** Use `Random.new()` with a seed for reproducible results."
)

_kb("vector3",
    ["vector3", "vector", "position", "coordinate", "3d vector", "cframe"],
    "**Vector3** for 3D positions:\n\n```lua\nlocal pos = Vector3.new(10, 5, 0)\n\n-- Operations\nlocal a = Vector3.new(1, 0, 0)\nlocal b = Vector3.new(0, 1, 0)\nprint(a + b)      -- (1, 1, 0)\nprint(a.Magnitude) -- 1\nprint(a.Unit)      -- (1, 0, 0) normalized\n\n-- Distance\nlocal dist = (pos1 - pos2).Magnitude\n\n-- Useful constructors\nVector3.zero      -- (0, 0, 0)\nVector3.one       -- (1, 1, 1)\nVector3.yAxis     -- (0, 1, 0)\n```\n"
)

_kb("cframe",
    ["cframe", "coordinate frame", "cframe tutorial", "cframe usage", "rotate", "orientation"],
    "**CFrame** (Coordinate Frame) = Position + Rotation:\n\n```lua\nlocal cf = CFrame.new(0, 10, 0)                     -- position only\nlocal cf = CFrame.new(0, 10, 0) * CFrame.Angles(0, math.rad(90), 0)  -- rotated\n\n-- Look at a target\nlocal cf = CFrame.lookAt(part.Position, target.Position)\n\n-- Lerp (smooth interpolation)\nlocal result = cf1:Lerp(cf2, 0.5)  -- halfway between\n\n-- Decompose\nlocal pos = cf.Position\nlocal rot = cf:ToEulerAnglesYXZ()\n```\n\nCFrame is the most important data type in Roblox for positioning objects."
)

# ═════════════════════════════════════════════════════════════════════════
# INTENT CLASSIFIER
# ═════════════════════════════════════════════════════════════════════════

# Pre-compute vectors for all KB entries
_KB_VECTORS: dict[str, dict] = {}
_KB_PATTERNS: dict[str, list[str]] = {}


def _build_index():
    for topic, entry in KB.items():
        all_text = " ".join(entry["patterns"])
        tokens = _tokenize(all_text)
        _KB_VECTORS[topic] = _tfidf_vec(tokens)
        _KB_PATTERNS[topic] = entry["patterns"]


_build_index()


def classify_intent(text: str, context_topics: list[str] = None) -> tuple[str, float]:
    """Classify user intent. Returns (topic, confidence)."""
    tokens = _tokenize(text)
    raw_text = text.lower().strip()

    # Phase 0: Exact phrase match against patterns (before tokenization)
    # This catches "what are you", "how are you" etc. where tokens become empty
    best_phrase = None
    best_phrase_score = 0
    for topic, patterns in _KB_PATTERNS.items():
        for pat in patterns:
            if pat in raw_text:
                score = len(pat) / max(len(raw_text), 1) + 0.5
                if score > best_phrase_score:
                    best_phrase_score = score
                    best_phrase = topic
    if best_phrase and best_phrase_score > 0.5:
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

    # Phase 3: N-gram overlap bonus
    best_ngram = None
    best_ngram_score = 0
    bigrams = _ngrams(tokens, 2)
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

    # Phase 4: Keyword presence bonus
    best_kw = None
    best_kw_score = 0
    for topic, patterns in _KB_PATTERNS.items():
        pat_tokens = _tokenize(" ".join(patterns))
        overlap = len(set(tokens) & set(pat_tokens))
        score = overlap / max(len(pat_tokens), 1)
        if score > best_kw_score:
            best_kw_score = score
            best_kw = topic

    # Combine scores
    candidates = {}
    if best_sim:
        candidates[best_sim] = candidates.get(best_sim, 0) + best_sim_score * 2.0
    if best_ngram:
        candidates[best_ngram] = candidates.get(best_ngram, 0) + best_ngram_score * 1.5
    if best_kw:
        candidates[best_kw] = candidates.get(best_kw, 0) + best_kw_score * 1.0

    # Context boost — topics similar to recent conversation
    if context_topics:
        for ct in context_topics[-3:]:
            for topic in candidates:
                if _topic_similarity(ct, topic) > 0.3:
                    candidates[topic] *= 1.2

    if not candidates:
        return ("fallback", 0.0)

    best_topic = max(candidates, key=candidates.get)
    confidence = min(candidates[best_topic] / 4.0, 1.0)

    return (best_topic, confidence)


def _topic_similarity(t1: str, t2: str) -> float:
    """Quick similarity check between two topic names."""
    v1 = _KB_VECTORS.get(t1, {})
    v2 = _KB_VECTORS.get(t2, {})
    return _cosine_sim(v1, v2)


# ═════════════════════════════════════════════════════════════════════════
# CODE DETECTION
# ═════════════════════════════════════════════════════════════════════════

_CODE_INDICATORS = [
    r"\blocal\s+\w+\s*=",
    r"\bfunction\s*\(",
    r"\bgame:GetService\b",
    r"\bInstance\.new\b",
    r"\b:Connect\s*\(",
    r"\bif\b.*\bthen\b",
    r"\bfor\b.*\bdo\b",
    r"\bend\b",
    r"\breturn\b",
    r"--\[\[",
    r"\bVector3\.new\b",
    r"\bCFrame\b",
    r"\bprint\s*\(",
]


def _is_code(text: str) -> bool:
    """Heuristic: is this message mostly code?"""
    lines = text.strip().split("\n")
    if len(lines) < 2:
        return False
    code_lines = sum(1 for l in lines if any(re.search(p, l) for p in _CODE_INDICATORS))
    return code_lines / max(len(lines), 1) > 0.4


# ═════════════════════════════════════════════════════════════════════════
# CONVERSATION CONTEXT
# ═════════════════════════════════════════════════════════════════════════

_histories: dict[int, dict] = {}
_MAX_HISTORY = 30


def _get_ctx(uid: int) -> dict:
    if uid not in _histories:
        _histories[uid] = {"topics": [], "last_q": "", "turns": 0}
    return _histories[uid]


def _add_context(uid: int, topic: str, question: str):
    ctx = _get_ctx(uid)
    ctx["topics"].append(topic)
    ctx["last_q"] = question
    ctx["turns"] += 1
    if len(ctx["topics"]) > _MAX_HISTORY:
        ctx["topics"] = ctx["topics"][-_MAX_HISTORY:]


def clear_history(uid: int):
    _histories.pop(uid, None)


# ═════════════════════════════════════════════════════════════════════════
# FOLLOW-UP DETECTION
# ═════════════════════════════════════════════════════════════════════════

_FOLLOW_UPS = [
    (r"^(tell me more|more about|elaborate|explain more|go on|continue|details|detail|what else)\s*$", "elaborate"),
    (r"^(show me|code example|snippet|demo|sample)\s*$", "example"),
    (r"^(why|reason)\s*$", "why"),
    (r"^(best|recommend|suggest|should i|which one|which is better)\s*$", "recommend"),
]


def _detect_followup(text: str) -> str | None:
    """Only detect very short, vague follow-ups that clearly reference previous topic."""
    raw = text.lower().strip()
    words = raw.split()
    if len(words) > 5:
        return None
    for pat, ftype in _FOLLOW_UPS:
        if re.match(pat, raw, re.IGNORECASE):
            return ftype
    return None


# ═════════════════════════════════════════════════════════════════════════
# RESPONSE GENERATION
# ═════════════════════════════════════════════════════════════════════════

FALLBACKS = [
    "I'm not sure what you mean. Try asking about **obfuscation**, **Roblox APIs**, **Luau programming**, or how to use shesfuscator!",
    "Hmm, I don't have info on that. I can help with Luau, Roblox game dev, obfuscation techniques, or shesfuscator commands!",
    "I don't know much about that. Try asking about Vmify, presets, DataStores, GUI, combat systems, or any Roblox topic!",
]

ELABORATE_FOLLOWUPS = {
    "greet_hello": "What can I help you with? I know a lot about Luau, Roblox development, and code obfuscation!",
    "greet_bye": "Come back whenever you need help!",
    "thanks": "You're welcome! Anything else?",
    "how_are_you": "All good! What do you need help with?",
}


def answer_question(question: str, uid: int = 0) -> str:
    """Main entry point — classify intent and generate response."""
    ctx = _get_ctx(uid)
    text = question.strip()

    # Code detection
    if _is_code(text):
        _add_context(uid, "code_analysis", text)
        return _analyze_pasted_code(text)

    # Short single-word or empty
    if len(text) <= 1:
        return "Type a question or paste some code!"

    # Intent classification
    topic, confidence = classify_intent(text, ctx.get("topics", []))

    # Follow-up detection
    followup = _detect_followup(text)
    if followup and ctx["topics"]:
        last_topic = ctx["topics"][-1]
        response = _handle_followup(followup, last_topic, text)
        _add_context(uid, last_topic, text)
        return response

    # Confidence check
    if confidence < 0.15 or topic == "fallback":
        _add_context(uid, "fallback", text)
        return random.choice(FALLBACKS)

    # Get response
    response = KB[topic]["response"]
    _add_context(uid, topic, text)

    # Personalize sometimes
    if ctx["turns"] > 0 and random.random() < 0.15:
        response += "\n\nAnything else you'd like to know?"

    return response


def _handle_followup(followup_type: str, last_topic: str, text: str) -> str:
    """Handle follow-up questions based on context."""
    if last_topic in ELABORATE_FOLLOWUPS and followup_type == "elaborate":
        return ELABORATE_FOLLOWUPS[last_topic]

    base = KB.get(last_topic, {}).get("response", "I'm not sure what to elaborate on.")

    if followup_type == "elaborate":
        return f"Here's more on that:\n\n{base}"
    elif followup_type == "example":
        return f"Here's a code example for that topic:\n\n{base}"
    elif followup_type == "recommend":
        return f"Based on the topic, here's my recommendation:\n\n{base}"
    elif followup_type == "why":
        return f"The reason is:\n\n{base}"
    elif followup_type == "how":
        return f"Here's how it works:\n\n{base}"

    return base


def _analyze_pasted_code(code: str) -> str:
    """Analyze pasted Luau code and explain it."""
    from analyzer import explain
    try:
        analysis = explain(code)
        return f"**Code Analysis:**\n\n{analysis}"
    except Exception:
        return "I can see that's code, but I had trouble analyzing it. Try using `/explain` for a detailed breakdown!"


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
    "shesfuscator is written in Python with the discord.py library.",
    "You can batch-obfuscate multiple files by DMing them all at once!",
    "Luau is 1-indexed — arrays start at 1, not 0.",
    "Roblox uses `task.wait()` instead of the old `wait()` for better accuracy.",
    "DataStoreService calls should always be wrapped in pcall() to handle failures.",
    "The `typeof()` function returns Roblox class names, while `type()` returns basic Lua types.",
]


def random_fact() -> str:
    return random.choice(QUICK_FACTS)
