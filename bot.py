"""
shesfuscator — Discord bot for obfuscating Luau scripts.

Uses Prometheus Lua obfuscator + custom post-processing layers.

Setup:
  1. pip install -r requirements.txt
  2. Set DISCORD_BOT_TOKEN env var
  3. python3 bot.py

DM the bot a .lua/.luau file to start.
Or use /obfuscate in servers.
"""

import io
import os
import time
import traceback

import discord
from discord import app_commands
from discord.ext import commands

from obfuscator import (
    obfuscate_custom,
    get_preset_steps,
    get_preset_custom,
    PRESETS,
    PRESET_NAMES,
    ALL_PROMETHEUS_STEPS,
    ALL_CUSTOM_METHODS,
    CUSTOM_METHOD_INFO,
)
from deobfuscator import deobfuscate
from ai import answer_question, random_fact
from analyzer import explain

MAX_INPUT_BYTES = 300_000
SESSION_TIMEOUT = 300
EMBED_COLOR = 0x9B59B6

PRESET_COLORS = {
    "Very Light": 0x2ECC71,
    "Light": 0x3498DB,
    "Medium": 0xE67E22,
    "Medium-High": 0xE74C3C,
    "High": 0x9B59B6,
    "Very High": 0x8E44AD,
    "Ultra": 0x2C3E50,
}


# ─── Bot ──────────────────────────────────────────────────────────────

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
dm_sessions: dict[int, dict] = {}


def _steps_text(steps):
    return ", ".join(f"`{s}`" for s in steps) if steps else "_None_"


def _cleanup(uid):
    dm_sessions.pop(uid, None)


def _preset_summary(preset):
    data = PRESETS[preset]
    parts = []
    if data["steps"]:
        parts.append("**Engine:** " + _steps_text(data["steps"]))
    if data["custom"]:
        parts.append("**Extra:** " + _steps_text(data["custom"]))
    return "\n".join(parts) if parts else "_None_"


def _do_obfuscate(source, steps, custom, filename, t0):
    result = obfuscate_custom(source, steps, custom_methods=custom)
    elapsed = time.time() - t0
    out_bytes = result.encode("utf-8")
    out_name = filename.rsplit(".", 1)[0] + ".obfuscated.lua"
    ratio = len(result) / max(len(source), 1) * 100

    embed = discord.Embed(title="shesfuscator", color=EMBED_COLOR)
    embed.add_field(name="Target", value="Luau", inline=True)
    embed.add_field(name="Time", value=f"{elapsed:.1f}s", inline=True)
    embed.add_field(name="Size", value=f"{len(source):,} \u2192 {len(result):,} ({ratio:.0f}%)", inline=True)
    if steps:
        embed.add_field(name="Engine Steps", value=_steps_text(steps), inline=False)
    if custom:
        embed.add_field(name="Extra Methods", value=_steps_text(custom), inline=False)
    embed.set_footer(text="Powered by Prometheus + custom layers")
    return discord.File(io.BytesIO(out_bytes), filename=out_name), embed


def _dm_embed(session):
    preset = session.get("preset") or "Pick a preset"
    src = session.get("source", "")
    snippet = (src[:150] + "...") if len(src) > 150 else src

    embed = discord.Embed(title="shesfuscator", color=EMBED_COLOR)
    if snippet:
        embed.add_field(name="Code", value=f"```lua\n{snippet}\n```", inline=False)
    embed.add_field(name="Preset", value=f"**{preset}**", inline=True)
    if session.get("preset"):
        embed.add_field(name="Layers", value=_preset_summary(session["preset"]), inline=False)

    return embed


def _batch_embed(session):
    preset = session.get("preset") or "Pick a preset"
    files = session.get("batch", [])
    idx = session.get("batch_idx", 0)
    results = session.get("results", [])

    embed = discord.Embed(title="shesfuscator \u2014 Batch Mode", color=EMBED_COLOR)
    embed.add_field(name="Files", value=f"**{len(files)}** total, **{idx}** done", inline=True)
    embed.add_field(name="Preset", value=f"**{preset}**", inline=True)
    if session.get("preset"):
        embed.add_field(name="Layers", value=_preset_summary(session["preset"]), inline=False)
    if results:
        embed.add_field(name="Results", value="\n".join(results[-5:]), inline=False)

    return embed


# ─── DM Flow: Preset Select ───────────────────────────────────────────

class PresetView(discord.ui.View):
    def __init__(self, uid):
        super().__init__(timeout=SESSION_TIMEOUT)
        self.uid = uid

        opts = [
            discord.SelectOption(label=name, value=name, description=f"{len(PRESETS[name]['steps'])} engine + {len(PRESETS[name]['custom'])} extra")
            for name in PRESET_NAMES
        ]
        sel = discord.ui.Select(
            placeholder="Pick an obfuscation level...",
            options=opts,
            min_values=1,
            max_values=1,
        )
        sel.callback = self._on_pick
        self.add_item(sel)

    async def on_timeout(self):
        _cleanup(self.uid)

    async def _on_pick(self, interaction):
        s = dm_sessions.get(self.uid)
        if not s:
            await interaction.response.send_message("Session expired.", ephemeral=True)
            return

        preset = interaction.data["values"][0]
        s["preset"] = preset
        s["steps"] = get_preset_steps(preset)
        s["custom"] = get_preset_custom(preset)

        for child in self.children:
            child.disabled = True

        # Batch mode
        if s.get("mode") == "batch":
            await interaction.response.edit_message(
                embed=discord.Embed(title="shesfuscator \u2014 Batch Mode", description="Obfuscating...", color=EMBED_COLOR),
                view=self,
            )
            files_data = s["batch"]
            results = []
            t0 = time.time()

            for filename, source in files_data:
                try:
                    f, embed = _do_obfuscate(source, s["steps"], s["custom"], filename, t0)
                    await interaction.followup.send(embed=embed, file=f)
                    results.append(f"\u2705 `{filename}` \u2014 done")
                except SyntaxError:
                    results.append(f"\u274c `{filename}` \u2014 parse error")
                except Exception as e:
                    results.append(f"\u274c `{filename}` \u2014 {type(e).__name__}")

            elapsed = time.time() - t0
            summary = discord.Embed(title="shesfuscator \u2014 Batch Complete", color=EMBED_COLOR)
            summary.add_field(name="Files", value="\n".join(results), inline=False)
            summary.add_field(name="Time", value=f"{elapsed:.1f}s total", inline=True)
            await interaction.followup.send(embed=summary)
            _cleanup(self.uid)
            return

        # Single file mode
        await interaction.response.edit_message(
            embed=discord.Embed(title="shesfuscator", description=f"Obfuscating with **{preset}**...", color=EMBED_COLOR),
            view=self,
        )

        t0 = time.time()
        try:
            f, embed = _do_obfuscate(s["source"], s["steps"], s["custom"], s["filename"], t0)
        except SyntaxError as e:
            await interaction.followup.send(f"**Parse error:**\n```\n{e}\n```")
        except Exception as e:
            await interaction.followup.send(f"**Failed:**\n```\n{type(e).__name__}: {e}\n```")
        else:
            await interaction.followup.send(embed=embed, file=f)
        finally:
            _cleanup(self.uid)


# ─── Events ───────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"shesfuscator online as {bot.user} \u2014 synced {len(synced)} command(s)")
    except Exception:
        traceback.print_exc()


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if isinstance(message.channel, discord.DMChannel):
        # Multiple files -> batch obfuscation
        if len(message.attachments) > 1:
            uid = message.author.id
            files_data = []
            errors = []

            for att in message.attachments:
                if att.size > MAX_INPUT_BYTES:
                    errors.append(f"`{att.filename}` \u2014 too large ({att.size:,} bytes)")
                    continue
                raw = await att.read()
                try:
                    source = raw.decode("utf-8")
                except UnicodeDecodeError:
                    errors.append(f"`{att.filename}` \u2014 not valid UTF-8")
                    continue
                files_data.append((att.filename, source))

            if not files_data:
                await message.channel.send("No valid files found.\n" + "\n".join(errors))
                return

            dm_sessions[uid] = {
                "batch": files_data,
                "batch_idx": 0,
                "results": [],
                "preset": None,
                "steps": [],
                "custom": [],
                "mode": "batch",
            }

            status = f"Received **{len(files_data)}** file(s)."
            if errors:
                status += "\nSkipped:\n" + "\n".join(errors)

            embed = discord.Embed(title="shesfuscator \u2014 Batch Mode", description=status, color=EMBED_COLOR)
            embed.add_field(name="Files", value="\n".join(f"`{f}` ({len(s):,} chars)" for f, s in files_data), inline=False)
            await message.channel.send(embed=embed, view=PresetView(uid))

        # Single file -> normal flow
        elif message.attachments:
            uid = message.author.id
            att = message.attachments[0]

            if att.size > MAX_INPUT_BYTES:
                await message.channel.send(f"File too large ({att.size:,} bytes). Max {MAX_INPUT_BYTES:,}.")
                return

            raw = await att.read()
            try:
                source = raw.decode("utf-8")
            except UnicodeDecodeError:
                await message.channel.send("Not valid UTF-8 \u2014 is it a Luau source file?")
                return

            dm_sessions[uid] = {
                "source": source,
                "filename": att.filename,
                "preset": None,
                "steps": [],
                "custom": [],
            }
            await message.channel.send(embed=_dm_embed(dm_sessions[uid]), view=PresetView(uid))

        # Text message -> AI response
        elif message.content and not message.content.startswith("!"):
            response = answer_question(message.content)
            embed = discord.Embed(title="shesfuscator AI", color=EMBED_COLOR)
            embed.add_field(name=f"Q: {message.content}", value=response, inline=False)
            embed.set_footer(text=random_fact())
            await message.channel.send(embed=embed)

    await bot.process_commands(message)


# ─── Slash Commands ───────────────────────────────────────────────────

@bot.tree.command(name="obfuscate", description="Obfuscate a Luau script")
@app_commands.describe(
    preset="Obfuscation level",
    code="Paste Luau code (OR file)",
    file="Upload .lua/.luau file (OR code)",
)
@app_commands.choices(preset=[
    app_commands.Choice(name=name, value=name)
    for name in PRESET_NAMES
])
async def obfuscate_cmd(
    interaction,
    preset: str = "Medium",
    code: str = None,
    file: discord.Attachment = None,
):
    if code is None and file is None:
        await interaction.response.send_message("Provide `code` or `file`.", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    t0 = time.time()

    try:
        if file is not None:
            if file.size > MAX_INPUT_BYTES:
                await interaction.followup.send(f"File too large ({file.size:,} bytes).")
                return
            raw = await file.read()
            try:
                source = raw.decode("utf-8")
            except UnicodeDecodeError:
                await interaction.followup.send("Not valid UTF-8.")
                return
            filename = file.filename
        else:
            source = code
            filename = "script.lua"

        steps = get_preset_steps(preset)
        custom = get_preset_custom(preset)
        result = obfuscate_custom(source, steps, custom_methods=custom)

    except SyntaxError as e:
        await interaction.followup.send(f"**Parse error:**\n```\n{e}\n```")
        return
    except Exception as e:
        await interaction.followup.send(f"**Failed:**\n```\n{type(e).__name__}: {e}\n```")
        return

    elapsed = time.time() - t0
    out_bytes = result.encode("utf-8")
    out_name = filename.rsplit(".", 1)[0] + ".obfuscated.lua"
    ratio = len(result) / max(len(source), 1) * 100

    embed = discord.Embed(title="shesfuscator", color=PRESET_COLORS.get(preset, EMBED_COLOR))
    embed.add_field(name="Preset", value=f"**{preset}**", inline=True)
    embed.add_field(name="Target", value="Luau", inline=True)
    embed.add_field(name="Time", value=f"{elapsed:.1f}s", inline=True)
    embed.add_field(name="Input", value=f"{len(source):,} chars", inline=True)
    embed.add_field(name="Output", value=f"{len(result):,} chars ({ratio:.0f}%)", inline=True)
    if steps:
        embed.add_field(name="Engine Steps", value=_steps_text(steps), inline=False)
    if custom:
        embed.add_field(name="Extra Methods", value=_steps_text(custom), inline=False)
    embed.set_footer(text="Powered by Prometheus + custom layers")

    await interaction.followup.send(
        embed=embed,
        file=discord.File(io.BytesIO(out_bytes), filename=out_name),
    )


@bot.tree.command(name="help", description="Show all obfuscation options")
async def help_cmd(interaction):
    embed = discord.Embed(title="shesfuscator \u2014 Options", color=EMBED_COLOR)

    embed.add_field(
        name="\u2500\u2500 Commands \u2500\u2500",
        value=(
            "`/obfuscate` \u2014 Obfuscate Luau code\n"
            "`/deobfuscate` \u2014 Reverse custom layers\n"
            "`/explain` \u2014 Analyze and explain a script\n"
            "`/status` \u2014 Check bot status\n"
            "`/help` \u2014 This message\n\n"
            "Or DM me a `.lua` file (or multiple!) to start an interactive session!"
        ),
        inline=False,
    )

    embed.add_field(
        name="\u2500\u2500 Presets \u2500\u2500",
        value=(
            "**Very Light** \u2014 Basic constant extraction\n"
            "**Light** \u2014 Constant array + IIFE wrapper\n"
            "**Medium** \u2014 String encryption + constant array + wrapper\n"
            "**Medium-High** \u2014 Adds VM + anti-tamper\n"
            "**High** \u2014 Adds number expressions + var renaming\n"
            "**Very High** \u2014 Adds dead code + bool wrapping + watermark\n"
            "**Ultra** \u2014 Everything: double VM + all 8 custom layers"
        ),
        inline=False,
    )

    embed.set_footer(text=random_fact())
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="deobfuscate", description="Heuristically deobfuscate a script")
@app_commands.describe(
    code="Paste obfuscated code (OR file)",
    file="Upload .lua/.luau file (OR code)",
)
async def deobfuscate_cmd(
    interaction,
    code: str = None,
    file: discord.Attachment = None,
):
    if code is None and file is None:
        await interaction.response.send_message("Provide `code` or `file`.", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    t0 = time.time()

    try:
        if file is not None:
            if file.size > MAX_INPUT_BYTES:
                await interaction.followup.send(f"File too large ({file.size:,} bytes).")
                return
            raw = await file.read()
            try:
                source = raw.decode("utf-8")
            except UnicodeDecodeError:
                await interaction.followup.send("Not valid UTF-8.")
                return
            filename = file.filename
        else:
            source = code
            filename = "script.lua"

        result, layers = deobfuscate(source)

    except Exception as e:
        await interaction.followup.send(f"**Failed:**\n```\n{type(e).__name__}: {e}\n```")
        return

    elapsed = time.time() - t0
    out_bytes = result.encode("utf-8")
    out_name = filename.rsplit(".", 1)[0] + ".deobfuscated.lua"
    ratio = len(result) / max(len(source), 1) * 100

    reversed_layers = []
    if layers.get("watermark"):
        reversed_layers.append("\u2705 Watermark removed")
    if layers.get("dead_code"):
        reversed_layers.append("\u2705 Dead code stripped")
    if layers.get("hex_numbers"):
        reversed_layers.append("\u2705 Hex \u2192 decimal")
    if layers.get("string_escapes"):
        reversed_layers.append("\u2705 String escapes decoded")
    if layers.get("control_flow"):
        reversed_layers.append("\u2705 Control flow reordered")
    if layers.get("wrap_in_function"):
        reversed_layers.append("\u2705 IIFE wrapper removed")

    embed = discord.Embed(title="shesfuscator \u2014 Deobfuscate", color=EMBED_COLOR)
    embed.add_field(name="Target", value="Luau", inline=True)
    embed.add_field(name="Time", value=f"{elapsed:.1f}s", inline=True)
    embed.add_field(name="Size", value=f"{len(source):,} \u2192 {len(result):,} ({ratio:.0f}%)", inline=True)

    if reversed_layers:
        embed.add_field(name="Reversed Layers", value="\n".join(reversed_layers), inline=False)
    else:
        embed.add_field(name="Reversed Layers", value="_No custom layers detected_", inline=False)

    embed.add_field(
        name="Not Reversible",
        value="\n".join([
            "\u274c Vmify (VM bytecode)",
            "\u274c EncryptStrings (encrypted strings)",
            "\u274c AntiTamper (integrity checks)",
            "\u274c ProxifyLocals (proxy indirection)",
        ]),
        inline=False,
    )
    embed.set_footer(text="Heuristic deobfuscator")
    await interaction.followup.send(
        embed=embed,
        file=discord.File(io.BytesIO(out_bytes), filename=out_name),
    )


@bot.tree.command(name="status", description="Check bot status and info")
async def status_cmd(interaction):
    import sys
    embed = discord.Embed(title="shesfuscator \u2014 Status", color=0x2ECC71)
    embed.add_field(name="Status", value="Online", inline=True)
    embed.add_field(name="Python", value=sys.version.split()[0], inline=True)
    embed.add_field(name="Guilds", value=str(len(bot.guilds)), inline=True)
    embed.add_field(name="Users", value=str(len(bot.users)), inline=True)
    embed.add_field(name="Engine", value="Prometheus v0.2 Alpha", inline=True)
    embed.add_field(name="Layers", value=f"{len(ALL_PROMETHEUS_STEPS)} engine + {len(ALL_CUSTOM_METHODS)} custom", inline=True)
    embed.add_field(name="Presets", value=str(len(PRESET_NAMES)), inline=True)
    embed.add_field(name="Uptime", value=f"<t:{int(bot.user.created_at.timestamp())}:R>", inline=True)
    embed.set_footer(text=random_fact())
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="explain", description="Analyze and explain what a Luau script does")
@app_commands.describe(
    code="Paste Luau code (OR file)",
    file="Upload .lua/.luau file (OR code)",
)
async def explain_cmd(
    interaction,
    code: str = None,
    file: discord.Attachment = None,
):
    if code is None and file is None:
        await interaction.response.send_message("Provide `code` or `file`.", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)

    try:
        if file is not None:
            if file.size > MAX_INPUT_BYTES:
                await interaction.followup.send(f"File too large ({file.size:,} bytes).")
                return
            raw = await file.read()
            try:
                source = raw.decode("utf-8")
            except UnicodeDecodeError:
                await interaction.followup.send("Not valid UTF-8.")
                return
        else:
            source = code

        result = explain(source)

    except Exception as e:
        await interaction.followup.send(f"**Failed:**\n```\n{type(e).__name__}: {e}\n```")
        return

    embed = discord.Embed(title="shesfuscator \u2014 Code Analysis", color=EMBED_COLOR)
    embed.add_field(name="Analysis", value=result, inline=False)
    embed.set_footer(text=random_fact())
    await interaction.followup.send(embed=embed)


if __name__ == "__main__":
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        print("No DISCORD_BOT_TOKEN set.\n  export DISCORD_BOT_TOKEN='your-token-here'\n  python3 bot.py")
        raise SystemExit(1)
    bot.run(token)
