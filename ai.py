"""
Simple pattern-matching Q&A for shesfuscator.

No external APIs — just keyword matching and a knowledge base of
obfuscation-related topics.
"""

import re
import random

# ─── Knowledge Base ───────────────────────────────────────────────────

KNOWLEDGE = {
    "obfuscation": {
        "keywords": ["obfuscate", "obfuscation", "obfuscating", "what is obfuscation"],
        "answer": (
            "Obfuscation is the process of making code difficult to read and understand "
            "while keeping it functional. In Luau/Roblox, this means transforming your "
            "scripts so others can't easily reverse-engineer or steal them.\n\n"
            "shesfuscator uses the **Prometheus** engine with 9 steps (Vmify, EncryptStrings, "
            "AntiTamper, etc.) plus 6 custom Python post-processing layers."
        ),
    },
    "deobfuscation": {
        "keywords": ["deobfuscate", "deobfuscation", "reverse", "undo obfuscation", "crack"],
        "answer": (
            "Deobfuscation is reversing obfuscated code back to something readable. "
            "shesfuscator can reverse its own **custom layers** (StringEncoder, VarRenamer, "
            "DeadCode, ControlFlow, HexNumbers, Watermark) but **cannot** reverse "
            "Prometheus engine steps like Vmify (custom bytecode VM) or EncryptStrings."
        ),
    },
    "vmify": {
        "keywords": ["vmify", "bytecode", "virtual machine", "vm"],
        "answer": (
            "**Vmify** is the strongest obfuscation step. It compiles your Lua code into a "
            "fully custom bytecode VM with its own instruction set. The output is no longer "
            "readable Lua — it's a custom bytecode interpreter. This makes reverse engineering "
            "extremely difficult.\n\n"
            "Performance cost: **High**. Use only when security is critical."
        ),
    },
    "encrypt_strings": {
        "keywords": ["encrypt string", "string encryption", "encryptstrings"],
        "answer": (
            "**EncryptStrings** encrypts all string literals in your code using pseudo-random "
            "number generators. Strings are decrypted at runtime, so they're not visible in "
            "the source.\n\n"
            "Performance cost: **Medium**. Good balance of protection and speed."
        ),
    },
    "anti_tamper": {
        "keywords": ["anti tamper", "antitamper", "integrity", "tamper"],
        "answer": (
            "**AntiTamper** adds integrity checks to your code. If someone tries to modify, "
            "beautify, or hook functions in the obfuscated script, it will break.\n\n"
            "Performance cost: **Low**. Recommended for all obfuscation levels."
        ),
    },
    "constant_array": {
        "keywords": ["constant array", "constantarray", "constants"],
        "answer": (
            "**ConstantArray** extracts all constants (strings, numbers) into a table with "
            "base64/base85 encoding, rotation, and local wrapper functions. This makes it "
            "harder to find specific values in the code.\n\n"
            "Performance cost: **Low**."
        ),
    },
    "presets_general": {
        "keywords": ["preset", "presets", "which preset", "preset options", "preset obfuscation"],
        "answer": (
            "shesfuscator has 7 presets:\n\n"
            "**Very Light** \u2014 ConstantArray\n"
            "**Light** \u2014 ConstantArray, WrapInFunction + HexNumbers\n"
            "**Medium** \u2014 EncryptStrings, ConstantArray, WrapInFunction + HexNumbers, StringEncoder\n"
            "**Medium-High** \u2014 EncryptStrings, AntiTamper, Vmify, ConstantArray, WrapInFunction + HexNumbers, StringEncoder, BoolWrap\n"
            "**High** \u2014 EncryptStrings, AntiTamper, Vmify, ConstantArray, NumbersToExpressions, WrapInFunction + HexNumbers, StringEncoder, VarRenamer, BoolWrap\n"
            "**Very High** \u2014 Vmify, EncryptStrings, AntiTamper, ConstantArray, NumbersToExpressions, WrapInFunction + all 6 extras\n"
            "**Ultra** \u2014 Double Vmify, EncryptStrings, AntiTamper, ConstantArray, NumbersToExpressions, WrapInFunction + all 8 extras\n\n"
            "Use `/obfuscate` or DM me a file to pick one."
        ),
    },
    "performance": {
        "keywords": ["performance", "slow", "speed", "lag", "fps", "optimization"],
        "answer": (
            "Performance impact depends on the steps used:\n"
            "- **None/Low**: HexNumbers, Watermark, AddVararg, WrapInFunction, ConstantArray\n"
            "- **Medium**: EncryptStrings, NumbersToExpressions, ProxifyLocals, ControlFlow, SplitStrings\n"
            "- **High**: Vmify (compiles to custom bytecode VM)\n\n"
            "Use the **Weak** preset if performance is critical."
        ),
    },
    "how_to_use": {
        "keywords": ["how to use", "how do i", "getting started", "start", "usage"],
        "answer": (
            "Using shesfuscator is easy:\n\n"
            "**Option 1 — Slash command:**\n"
            "Use `/obfuscate` with your code or a file upload.\n\n"
            "**Option 2 — DM:**\n"
            "1. DM me a `.lua` or `.luau` file\n"
            "2. Pick a preset (Weak/Medium/Strong)\n"
            "3. Customize engine steps and extra methods\n"
            "4. Click Obfuscate\n\n"
            "**Option 3 — Deobfuscate:**\n"
            "Use `/deobfuscate` to reverse custom layers."
        ),
    },
    "help": {
        "keywords": ["help", "commands", "what can you do", "options"],
        "answer": (
            "Here's what I can do:\n\n"
            "- `/obfuscate` — Obfuscate Luau code with preset or custom settings\n"
            "- `/deobfuscate` — Reverse custom obfuscation layers\n"
            "- `/status` — Check bot status\n"
            "- `/help` — Show all obfuscation options\n\n"
            "You can also DM me a `.lua` file to start an interactive session!"
        ),
    },
    "var_renamer": {
        "keywords": ["var renamer", "variable rename", "rename variables", "varrenamer"],
        "answer": (
            "**VarRenamer** replaces local variable names with confusing lookalike characters "
            "(I, l, 1, O, o, 0). This makes the code nearly impossible to read manually.\n\n"
            "Performance cost: **Low**. No runtime impact — only affects source readability."
        ),
    },
    "dead_code": {
        "keywords": ["dead code", "deadcode", "fake code", "unreachable"],
        "answer": (
            "**DeadCode** injects random unreachable code blocks (if false, while false, etc.) "
            "throughout the script. This confuses static analysis tools and human readers.\n\n"
            "Performance cost: **Low**. Dead code is never executed."
        ),
    },
    "control_flow": {
        "keywords": ["control flow", "controlflow", "flatten", "flattening"],
        "answer": (
            "**ControlFlow** wraps code sections in numeric switch dispatchers. Instead of "
            "linear code, execution follows a randomized dispatch table.\n\n"
            "Performance cost: **Medium**."
        ),
    },
    "string_encoder": {
        "keywords": ["string encoder", "stringencoder", "decimal escapes", "wearedevs"],
        "answer": (
            "**StringEncoder** converts string literals to `\\ddd` decimal escape sequences "
            "(WeAreDevs style). E.g., `\"hello\"` becomes `\"\\104\\101\\108\\108\\111\"`.\n\n"
            "Performance cost: **Low**. Strings are decoded at runtime."
        ),
    },
    "luau": {
        "keywords": ["luau", "roblox", "lua"],
        "answer": (
            "shesfuscator targets **Luau**, Roblox's variant of Lua. It supports both Lua 5.1 "
            "and Luau syntax. The Prometheus engine handles parsing and transformation.\n\n"
            "You can obfuscate any `.lua` or `.luau` file."
        ),
    },
    "layers": {
        "keywords": ["layers", "how many layers", "steps", "methods"],
        "answer": (
            "shesfuscator has two types of obfuscation layers:\n\n"
            "**Engine steps** (Prometheus — Lua-based):\n"
            "Vmify, EncryptStrings, AntiTamper, ConstantArray, NumbersToExpressions, "
            "WrapInFunction, SplitStrings, ProxifyLocals, AddVararg\n\n"
            "**Custom methods** (Python post-processing):\n"
            "StringEncoder, VarRenamer, DeadCode, HexNumbers, Watermark, "
            "BoolWrap, NegateBools, NoiseVars\n\n"
            "Total: 9 engine steps + 8 custom methods = 17 available layers."
        ),
    },
    "watermark": {
        "keywords": ["watermark", "branding", "tag"],
        "answer": (
            "**Watermark** embeds a `--[[ shesfuscator v1.0 ]]` comment at the top of the "
            "obfuscated output. Useful for branding your scripts.\n\n"
            "Performance cost: **None**. It's just a comment."
        ),
    },
}


# ─── Pattern Matching ─────────────────────────────────────────────────

def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9\s]", " ", text.lower()).split()


def _score(query_words: list[str], keywords: list[str]) -> int:
    score = 0
    kw_set = set(keywords)
    for w in query_words:
        if w in kw_set:
            score += 2
        for kw in keywords:
            if w in kw or kw in w:
                score += 1
    return score


def answer_question(question: str) -> str:
    """Match a question against the knowledge base and return the best answer."""
    words = _normalize(question)

    best_key = None
    best_score = 0

    for key, entry in KNOWLEDGE.items():
        s = _score(words, entry["keywords"])
        if s > best_score:
            best_score = s
            best_key = key

    if best_key and best_score >= 2:
        return KNOWLEDGE[best_key]["answer"]

    fallbacks = [
        "I'm not sure about that. Try asking about obfuscation, specific steps (Vmify, EncryptStrings, etc.), presets, or how to use the bot.",
        "Hmm, I don't have an answer for that. Ask me about obfuscation techniques, bot usage, or specific obfuscation steps!",
        "I don't know that one yet. Try `/help` to see available commands, or ask about topics like 'Vmify', 'presets', 'performance', or 'how to use'.",
    ]
    return random.choice(fallbacks)


# ─── Quick Facts ──────────────────────────────────────────────────────

QUICK_FACTS = [
    "The Prometheus engine was created by levno-710 and supports both Lua 5.1 and Luau.",
    "Vmify compiles your code into a custom bytecode VM — the output isn't even valid Lua anymore!",
    "shesfuscator can reverse its own custom layers but NOT Prometheus engine steps.",
    "The Strong preset runs Vmify twice for maximum protection.",
    "VarRenamer uses lookalike characters (I, l, 1, O, o, 0) to make code unreadable.",
    "Dead code injection adds unreachable blocks that confuse static analyzers.",
    "ConstantArray extracts all constants into an encoded table with rotation.",
    "AntiTamper breaks the script if anyone tries to beautify or modify it.",
    "You can customize every step individually in the DM interactive flow.",
    "Hex numbers (0x4F) are harder to read than decimal (79) — that's the point.",
    "StringEncoder turns \"hello\" into \"\\104\\101\\108\\108\\111\".",
    "ControlFlow flattening makes code execution follow a randomized dispatch table.",
    "The bot supports files up to 300KB for obfuscation.",
    "shesfuscator is written in Python with the discord.py library.",
    "LuaJIT is required to run the Prometheus Lua obfuscator engine.",
]


def random_fact() -> str:
    return random.choice(QUICK_FACTS)
