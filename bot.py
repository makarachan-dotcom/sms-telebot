#!/usr/bin/env python3
"""
🤖 AI STAND WY2.5 - Advanced Telegram Bot
Based on Claude Code Architecture Port
Created with love by Kimi K2.5 for the community

Features:
- Natural language processing with command/tool routing
- Session management with conversation history
- Admin controls and user statistics
- Cool cyberpunk styling and personality
- Full integration with the ported codebase
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ConversationHandler,
)
from telegram.constants import ParseMode

# Import our ported modules
from commands import get_commands, get_command, execute_command, find_commands
from tools import get_tools, get_tool, execute_tool, find_tools
from query_engine import QueryEnginePort, QueryEngineConfig, TurnResult
from runtime import PortRuntime, RoutedMatch
from session_store import save_session, load_session, StoredSession
from models import UsageSummary
from execution_registry import build_execution_registry
from port_manifest import build_port_manifest

# Import SMS module
from sms_service import get_sms_service, COUNTRY_CODES, SMSResult
from carrier_detector import detect_carrier, validate_phone_number, mask_phone_number

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Configuration
BOT_NAME = "AI STAND WY2.5"
BOT_VERSION = "2.5.0"
BOT_CREATOR = "Kimi K2.5"

# Cyberpunk styling
STYLES = {
    "header": "╔══════════════════════════════════════╗",
    "footer": "╚══════════════════════════════════════╝",
    "divider": "═══════════════════════════════════════",
    "bullet": "▸",
    "arrow": "➤",
    "star": "★",
    "sparkle": "✨",
    "rocket": "🚀",
    "brain": "🧠",
    "chip": "🔷",
    "circuit": "⚡",
    "code": "💻",
    "gear": "⚙️",
    "target": "🎯",
    "fire": "🔥",
    "cool": "😎",
    "think": "🤔",
    "magic": "🪄",
    "crown": "👑",
    "diamond": "💎",
    "crystal": "🔮",
    "sms": "📱",
    "phone": "📞",
    "message": "💬",
    "contact": "👤",
    "send": "📤",
    "receive": "📥",
    "history": "📜",
    "settings": "🔧",
    # Additional style keys
    "chat": "💬",
    "tools": "🛠️",
    "help": "❓",
    "info": "ℹ️",
    "error": "❌",
    "warning": "⚠️",
    "check": "✅",
    "timer": "⏱️",
    "carrier": "📡",
    "confirm": "🔒",
    "cancel": "🚫",
    "sending": "📤",
    "delivered": "✅",
    "pending": "⏳",
    "retry": "🔄",
    "lock": "🔐",
    "key": "🔑",
}

# Conversation states
CHAT_MODE, EXECUTING_COMMAND = range(2)

# Interactive SMS conversation states
(
    SMS_COUNTRY_SELECTION,
    SMS_PHONE_NUMBER_INPUT,
    SMS_WAITING_COUNTDOWN,
    SMS_MESSAGE_INPUT,
    SMS_CONFIRMATION,
) = range(10, 15)


@dataclass
class UserSession:
    """User session data"""
    user_id: int
    username: str
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: datetime = field(default_factory=datetime.now)
    messages_count: int = 0
    commands_used: List[str] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "messages_count": self.messages_count,
            "commands_used": self.commands_used,
            "tools_used": self.tools_used,
            "preferences": self.preferences,
        }


class UserSessionManager:
    """Manages user sessions"""
    
    def __init__(self):
        self.sessions: Dict[int, UserSession] = {}
        self.query_engines: Dict[int, QueryEnginePort] = {}
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
    
    def get_session(self, user_id: int, username: str = "") -> UserSession:
        if user_id not in self.sessions:
            self.sessions[user_id] = UserSession(user_id=user_id, username=username)
            self.query_engines[user_id] = QueryEnginePort.from_workspace()
        return self.sessions[user_id]
    
    def get_engine(self, user_id: int, username: str = "") -> QueryEnginePort:
        self.get_session(user_id, username)  # Ensure session exists
        return self.query_engines[user_id]
    
    def save_all(self):
        for session in self.sessions.values():
            filepath = self.data_dir / f"user_{session.user_id}.json"
            with open(filepath, "w") as f:
                json.dump(session.to_dict(), f, indent=2)


# Global session manager
session_manager = UserSessionManager()


def style_text(text: str, style_type: str = "normal") -> str:
    """Apply cyberpunk styling to text"""
    if style_type == "header":
        return f"{STYLES['header']}\n{text}\n{STYLES['footer']}"
    elif style_type == "title":
        return f"{STYLES['circuit']} {text} {STYLES['circuit']}"
    elif style_type == "section":
        return f"\n{STYLES['diamond']} <b>{text}</b>"
    elif style_type == "item":
        return f"  {STYLES['bullet']} {text}"
    elif style_type == "code":
        return f"<code>{text}</code>"
    elif style_type == "success":
        return f"{STYLES['sparkle']} {text}"
    elif style_type == "warning":
        return f"⚠️ {text}"
    elif style_type == "error":
        return f"❌ {text}"
    elif style_type == "info":
        return f"ℹ️ {text}"
    return text


def get_welcome_message() -> str:
    """Generate the welcome message"""
    return f"""
{STYLES['header']}

{STYLES['crystal']} <b>Welcome to {BOT_NAME}</b> {STYLES['crystal']}

<i>"The future of AI assistance is here"</i>

{STYLES['brain']} Powered by Claude Code Architecture
{STYLES['chip']} Engineered by {BOT_CREATOR}
{STYLES['rocket']} Version {BOT_VERSION}

{STYLES['divider']}

<b>What I can do:</b>
{STYLES['bullet']} Process natural language queries
{STYLES['bullet']} Route to appropriate commands & tools
{STYLES['bullet']} Maintain conversation context
{STYLES['bullet']} Execute code operations
{STYLES['bullet']} Provide intelligent responses

{STYLES['divider']}

Use /help to see all commands
Use /chat to start a conversation

{STYLES['footer']}
"""


def get_help_message() -> str:
    """Generate the help message"""
    return f"""
{STYLES['header']}

{STYLES['gear']} <b>{BOT_NAME} Commands</b>

{STYLES['diamond']} <b>Core Commands</b>
/chat - Start interactive chat mode
/clear - Clear conversation history
/session - Show session information
/stats - Show your usage statistics

{STYLES['diamond']} <b>SMS Commands {STYLES['sms']}</b>
/sms - SMS service menu
/sms_send_interactive - Interactive SMS send (guided)
/sms_send &lt;phone&gt; &lt;msg&gt; - Send SMS
/sms_contact &lt;name&gt; &lt;msg&gt; - Send to contact
/sms_contacts - List contacts
/sms_add &lt;name&gt; &lt;phone&gt; - Add contact
/sms_remove &lt;name&gt; - Remove contact
/sms_history - SMS history
/sms_stats - SMS statistics
/sms_setkey &lt;key&gt; - Set API key
/sms_setcountry &lt;code&gt; - Set country

{STYLES['diamond']} <b>System Commands</b>
/commands - List available commands
/tools - List available tools
/search - Search commands and tools
/manifest - Show system manifest

{STYLES['diamond']} <b>Execution Commands</b>
/exec &lt;command&gt; - Execute a command
/tool &lt;tool&gt; [payload] - Execute a tool
/route &lt;query&gt; - Route a query

{STYLES['diamond']} <b>Admin Commands</b>
/status - Bot system status

{STYLES['diamond']} <b>Other Commands</b>
/start - Start the bot
/help - Show this help message
/about - About this bot

{STYLES['footer']}
"""


# Command Handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    user = update.effective_user
    session = session_manager.get_session(user.id, user.username or user.first_name)
    
    welcome_msg = get_welcome_message()
    
    # Create inline keyboard
    keyboard = [
        [
            InlineKeyboardButton(f"{STYLES['chat']} Start Chat", callback_data="start_chat"),
            InlineKeyboardButton(f"{STYLES['gear']} Commands", callback_data="show_commands"),
        ],
        [
            InlineKeyboardButton(f"{STYLES['tools']} Tools", callback_data="show_tools"),
            InlineKeyboardButton(f"{STYLES['help']} Help", callback_data="show_help"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_msg,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    help_msg = get_help_message()
    await update.message.reply_text(help_msg, parse_mode=ParseMode.HTML)


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /about command"""
    about_msg = f"""
{STYLES['header']}

{STYLES['crown']} <b>About {BOT_NAME}</b>

<i>"Standing at the frontier of AI assistance"</i>

{STYLES['divider']}

<b>Version:</b> {BOT_VERSION}
<b>Creator:</b> {BOT_CREATOR}
<b>Architecture:</b> Claude Code Python Port

{STYLES['divider']}

<b>Features:</b>
{STYLES['bullet']} 400+ Mirrored Commands
{STYLES['bullet']} 300+ Integrated Tools
{STYLES['bullet']} Advanced Query Routing
{STYLES['bullet']} Session Persistence
{STYLES['bullet']} Natural Language Processing

{STYLES['divider']}

Built with {STYLES['fire']} Python + python-telegram-bot
Powered by the Claude Code architecture

{STYLES['footer']}
"""
    await update.message.reply_text(about_msg, parse_mode=ParseMode.HTML)


async def chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /chat command - Enter chat mode"""
    user = update.effective_user
    session = session_manager.get_session(user.id, user.username or user.first_name)
    
    chat_msg = f"""
{STYLES['sparkle']} <b>Chat Mode Activated!</b>

Session ID: <code>{session.session_id}</code>

You can now chat with me naturally. I'll:
{STYLES['bullet']} Understand your intent
{STYLES['bullet']} Route to appropriate tools
{STYLES['bullet']} Remember our conversation

{STYLES['info']} Type /exit to exit chat mode
{STYLES['info']} Type /clear to clear history

{STYLES['think']} What would you like to discuss?
"""
    await update.message.reply_text(chat_msg, parse_mode=ParseMode.HTML)
    return CHAT_MODE


async def chat_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle messages in chat mode"""
    user = update.effective_user
    message_text = update.message.text
    
    # Check for exit command
    if message_text.lower() in ['/exit', '/quit', '/bye']:
        exit_msg = f"""
{STYLES['sparkle']} <b>Chat Mode Exited</b>

Thanks for chatting! Your session has been saved.
Use /chat to start again anytime.
"""
        await update.message.reply_text(exit_msg, parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    # Process the message
    session = session_manager.get_session(user.id, user.username or user.first_name)
    engine = session_manager.get_engine(user.id, user.username or user.first_name)
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Use the runtime to route and process
        runtime = PortRuntime()
        matches = runtime.route_prompt(message_text, limit=5)
        
        # Build response
        response_lines = [f"{STYLES['brain']} <b>Processing your request...</b>\n"]
        
        if matches:
            response_lines.append(f"{STYLES['target']} <b>Matched:</b>")
            for match in matches[:3]:
                icon = STYLES['gear'] if match.kind == 'command' else STYLES['tools']
                response_lines.append(f"  {icon} <code>{match.name}</code> ({match.score})")
            response_lines.append("")
        
        # Submit to query engine
        result = engine.submit_message(
            message_text,
            matched_commands=tuple(m.name for m in matches if m.kind == 'command'),
            matched_tools=tuple(m.name for m in matches if m.kind == 'tool'),
            denied_tools=()
        )
        
        # Add AI response
        response_lines.append(f"{STYLES['circuit']} <b>Response:</b>")
        response_lines.append(f"<blockquote>{result.output}</blockquote>")
        
        # Add usage info
        response_lines.append(f"\n{STYLES['chip']} <i>Tokens: {result.usage.input_tokens} in / {result.usage.output_tokens} out</i>")
        
        # Update session
        session.messages_count += 1
        session.conversation_history.append({"user": message_text, "bot": result.output})
        
        response_text = "\n".join(response_lines)
        
        # Split if too long
        if len(response_text) > 4000:
            response_text = response_text[:4000] + "\n\n<i>(Message truncated)</i>"
        
        await update.message.reply_text(response_text, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        error_msg = f"{STYLES['error']} <b>Sorry, I encountered an error:</b>\n<code>{str(e)}</code>"
        await update.message.reply_text(error_msg, parse_mode=ParseMode.HTML)
    
    return CHAT_MODE


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /clear command"""
    user = update.effective_user
    
    # Reset the query engine for this user
    session_manager.query_engines[user.id] = QueryEnginePort.from_workspace()
    session = session_manager.get_session(user.id)
    session.conversation_history.clear()
    
    clear_msg = f"{STYLES['sparkle']} <b>Conversation history cleared!</b>\n\nYour session is fresh and ready."
    await update.message.reply_text(clear_msg, parse_mode=ParseMode.HTML)


async def session_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /session command"""
    user = update.effective_user
    session = session_manager.get_session(user.id, user.username or user.first_name)
    engine = session_manager.get_engine(user.id, user.username or user.first_name)
    
    session_msg = f"""
{STYLES['header']}

{STYLES['crystal']} <b>Session Information</b>

<b>User:</b> @{session.username or 'Unknown'}
<b>User ID:</b> <code>{session.user_id}</code>
<b>Session ID:</b> <code>{session.session_id}</code>
<b>Created:</b> {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}

{STYLES['divider']}

<b>Statistics:</b>
{STYLES['bullet']} Messages: {session.messages_count}
{STYLES['bullet']} Commands Used: {len(session.commands_used)}
{STYLES['bullet']} Tools Used: {len(session.tools_used)}
{STYLES['bullet']} Conversation Turns: {len(session.conversation_history)}

{STYLES['divider']}

<b>Engine Status:</b>
{STYLES['bullet']} Session: <code>{engine.session_id[:12]}...</code>
{STYLES['bullet']} Messages: {len(engine.mutable_messages)}
{STYLES['bullet']} Transcript Flushed: {engine.transcript_store.flushed}

{STYLES['footer']}
"""
    await update.message.reply_text(session_msg, parse_mode=ParseMode.HTML)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command"""
    user = update.effective_user
    session = session_manager.get_session(user.id, user.username or user.first_name)
    engine = session_manager.get_engine(user.id, user.username or user.first_name)
    
    stats_msg = f"""
{STYLES['header']}

{STYLES['diamond']} <b>Your Statistics</b>

<b>Session Activity:</b>
{STYLES['bullet']} Total Messages: {session.messages_count}
{STYLES['bullet']} Session Started: {session.created_at.strftime('%Y-%m-%d')}

<b>Usage:</b>
{STYLES['bullet']} Input Tokens: {engine.total_usage.input_tokens}
{STYLES['bullet']} Output Tokens: {engine.total_usage.output_tokens}
{STYLES['bullet']} Total Tokens: {engine.total_usage.input_tokens + engine.total_usage.output_tokens}

<b>Commands Used:</b>
"""
    if session.commands_used:
        for cmd in session.commands_used[-5:]:
            stats_msg += f"{STYLES['bullet']} {cmd}\n"
    else:
        stats_msg += f"{STYLES['bullet']} None yet\n"
    
    stats_msg += f"""
<b>Tools Used:</b>
"""
    if session.tools_used:
        for tool in session.tools_used[-5:]:
            stats_msg += f"{STYLES['bullet']} {tool}\n"
    else:
        stats_msg += f"{STYLES['bullet']} None yet\n"
    
    stats_msg += f"\n{STYLES['footer']}"
    
    await update.message.reply_text(stats_msg, parse_mode=ParseMode.HTML)


async def commands_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /commands command"""
    commands = get_commands()
    
    # Get first 20 commands
    display_commands = list(commands)[:20]
    
    commands_msg = f"""
{STYLES['header']}

{STYLES['gear']} <b>Available Commands</b>

<i>Showing {len(display_commands)} of {len(commands)} commands</i>

"""
    for cmd in display_commands:
        commands_msg += f"{STYLES['bullet']} <code>{cmd.name}</code> - <i>{cmd.responsibility[:50]}...</i>\n"
    
    commands_msg += f"""

{STYLES['info']} Use /search &lt;query&gt; to find specific commands

{STYLES['footer']}
"""
    await update.message.reply_text(commands_msg, parse_mode=ParseMode.HTML)


async def tools_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /tools command"""
    tools = get_tools()
    
    # Get first 20 tools
    display_tools = list(tools)[:20]
    
    tools_msg = f"""
{STYLES['header']}

{STYLES['tools']} <b>Available Tools</b>

<i>Showing {len(display_tools)} of {len(tools)} tools</i>

"""
    for tool in display_tools:
        tools_msg += f"{STYLES['bullet']} <code>{tool.name}</code> - <i>{tool.responsibility[:50]}...</i>\n"
    
    tools_msg += f"""

{STYLES['info']} Use /search &lt;query&gt; to find specific tools

{STYLES['footer']}
"""
    await update.message.reply_text(tools_msg, parse_mode=ParseMode.HTML)


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /search command"""
    query = " ".join(context.args)
    
    if not query:
        await update.message.reply_text(
            f"{STYLES['warning']} Please provide a search query.\nExample: <code>/search git</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Search commands and tools
    cmd_matches = find_commands(query, limit=10)
    tool_matches = find_tools(query, limit=10)
    
    search_msg = f"""
{STYLES['header']}

{STYLES['target']} <b>Search Results for "{query}"</b>

"""
    if cmd_matches:
        search_msg += f"{STYLES['gear']} <b>Commands ({len(cmd_matches)}):</b>\n"
        for cmd in cmd_matches[:5]:
            search_msg += f"  {STYLES['bullet']} <code>{cmd.name}</code>\n"
        search_msg += "\n"
    
    if tool_matches:
        search_msg += f"{STYLES['tools']} <b>Tools ({len(tool_matches)}):</b>\n"
        for tool in tool_matches[:5]:
            search_msg += f"  {STYLES['bullet']} <code>{tool.name}</code>\n"
        search_msg += "\n"
    
    if not cmd_matches and not tool_matches:
        search_msg += f"{STYLES['info']} No results found.\n"
    
    search_msg += f"\n{STYLES['footer']}"
    
    await update.message.reply_text(search_msg, parse_mode=ParseMode.HTML)


async def manifest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /manifest command"""
    manifest = build_port_manifest()
    
    manifest_msg = f"""
{STYLES['header']}

{STYLES['crystal']} <b>System Manifest</b>

<b>Workspace:</b> {manifest.workspace_name}
<b>Python Files:</b> {manifest.python_file_count}
<b>Test Files:</b> {manifest.test_file_count}

<b>Top Level Modules:</b>
"""
    for module in manifest.top_level_modules[:10]:
        manifest_msg += f"{STYLES['bullet']} {module.name} ({module.file_count} files)\n"
    
    manifest_msg += f"""

<b>Commands:</b> {len(get_commands())}
<b>Tools:</b> {len(get_tools())}

{STYLES['footer']}
"""
    await update.message.reply_text(manifest_msg, parse_mode=ParseMode.HTML)


async def exec_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /exec command"""
    if not context.args:
        await update.message.reply_text(
            f"{STYLES['warning']} Usage: <code>/exec &lt;command_name&gt;</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    command_name = context.args[0]
    prompt = " ".join(context.args[1:]) if len(context.args) > 1 else ""
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    result = execute_command(command_name, prompt)
    
    if result.handled:
        exec_msg = f"""
{STYLES['sparkle']} <b>Command Executed</b>

<b>Command:</b> <code>{result.name}</code>
<b>Source:</b> <code>{result.source_hint}</code>

<b>Result:</b>
<blockquote>{result.message}</blockquote>
"""
        # Track command usage
        user = update.effective_user
        session = session_manager.get_session(user.id)
        session.commands_used.append(command_name)
    else:
        exec_msg = f"{STYLES['error']} <b>Command failed:</b>\n{result.message}"
    
    await update.message.reply_text(exec_msg, parse_mode=ParseMode.HTML)


async def tool_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /tool command"""
    if not context.args:
        await update.message.reply_text(
            f"{STYLES['warning']} Usage: <code>/tool &lt;tool_name&gt; [payload]</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    tool_name = context.args[0]
    payload = " ".join(context.args[1:]) if len(context.args) > 1 else ""
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    result = execute_tool(tool_name, payload)
    
    if result.handled:
        tool_msg = f"""
{STYLES['sparkle']} <b>Tool Executed</b>

<b>Tool:</b> <code>{result.name}</code>
<b>Source:</b> <code>{result.source_hint}</code>

<b>Result:</b>
<blockquote>{result.message}</blockquote>
"""
        # Track tool usage
        user = update.effective_user
        session = session_manager.get_session(user.id)
        session.tools_used.append(tool_name)
    else:
        tool_msg = f"{STYLES['error']} <b>Tool execution failed:</b>\n{result.message}"
    
    await update.message.reply_text(tool_msg, parse_mode=ParseMode.HTML)


async def route_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /route command"""
    query = " ".join(context.args)
    
    if not query:
        await update.message.reply_text(
            f"{STYLES['warning']} Usage: <code>/route &lt;query&gt;</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    runtime = PortRuntime()
    matches = runtime.route_prompt(query, limit=5)
    
    route_msg = f"""
{STYLES['header']}

{STYLES['target']} <b>Routing Results for "{query}"</b>

"""
    if matches:
        for i, match in enumerate(matches, 1):
            icon = STYLES['gear'] if match.kind == 'command' else STYLES['tools']
            route_msg += f"{i}. {icon} <code>{match.name}</code>\n"
            route_msg += f"   Score: {match.score} | Source: <code>{match.source_hint}</code>\n\n"
    else:
        route_msg += f"{STYLES['info']} No matches found.\n"
    
    route_msg += f"\n{STYLES['footer']}"
    
    await update.message.reply_text(route_msg, parse_mode=ParseMode.HTML)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command"""
    import platform
    
    status_msg = f"""
{STYLES['header']}

{STYLES['chip']} <b>Bot System Status</b>

<b>Bot Information:</b>
{STYLES['bullet']} Name: {BOT_NAME}
{STYLES['bullet']} Version: {BOT_VERSION}
{STYLES['bullet']} Creator: {BOT_CREATOR}

<b>System:</b>
{STYLES['bullet']} Python: {platform.python_version()}
{STYLES['bullet']} Platform: {platform.system()} {platform.release()}

<b>Loaded Modules:</b>
{STYLES['bullet']} Commands: {len(get_commands())}
{STYLES['bullet']} Tools: {len(get_tools())}

<b>Active Sessions:</b>
{STYLES['bullet']} Users: {len(session_manager.sessions)}

<b>Status:</b> {STYLES['sparkle']} Operational

{STYLES['footer']}
"""
    await update.message.reply_text(status_msg, parse_mode=ParseMode.HTML)


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /cancel command"""
    cancel_msg = f"{STYLES['info']} Operation cancelled."
    await update.message.reply_text(cancel_msg, parse_mode=ParseMode.HTML)
    return ConversationHandler.END


# ==================== SMS HANDLERS ====================

async def sms_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /sms command - Show SMS menu"""
    user = update.effective_user
    sms_service = get_sms_service()
    stats = sms_service.get_stats(user.id)
    
    sms_menu = f"""
{STYLES['header']}

{STYLES['sms']} <b>SMS Service</b> {STYLES['message']}

<b>Your Statistics:</b>
{STYLES['bullet']} Total Sent: {stats['total_sent']}
{STYLES['bullet']} Contacts: {stats['contacts_count']}
{STYLES['bullet']} Quota Remaining: {stats['quota_remaining']}
{STYLES['bullet']} Default Country: {stats['default_country']['flag']} {stats['default_country']['name']}

<b>SMS Commands:</b>
{STYLES['bullet']} /sms_send_interactive - Guided SMS wizard 🧙
{STYLES['bullet']} /sms_send &lt;phone&gt; &lt;message&gt; - Quick send SMS
{STYLES['bullet']} /sms_contact &lt;name&gt; &lt;message&gt; - Send to contact
{STYLES['bullet']} /sms_contacts - List your contacts
{STYLES['bullet']} /sms_add &lt;name&gt; &lt;phone&gt; - Add contact
{STYLES['bullet']} /sms_remove &lt;name&gt; - Remove contact
{STYLES['bullet']} /sms_history - View SMS history
{STYLES['bullet']} /sms_stats - Detailed stats

<b>Settings:</b>
{STYLES['bullet']} /sms_setkey &lt;api_key&gt; - Set TextBelt API key
{STYLES['bullet']} /sms_setcountry &lt;code&gt; - Set default country

{STYLES['footer']}
"""
    await update.message.reply_text(sms_menu, parse_mode=ParseMode.HTML)


async def sms_send_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /sms_send command - Send SMS to phone number"""
    if len(context.args) < 2:
        await update.message.reply_text(
            f"{STYLES['warning']} <b>Usage:</b>\n"
            f"<code>/sms_send &lt;phone_number&gt; &lt;message&gt;</code>\n\n"
            f"<b>Examples:</b>\n"
            f"<code>/sms_send +85512345678 Hello!</code>\n"
            f"<code>/sms_send 012345678 សួស្តី!</code> (Khmer number)",
            parse_mode=ParseMode.HTML
        )
        return
    
    phone = context.args[0]
    message = " ".join(context.args[1:])
    user = update.effective_user
    
    # Show sending indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    sms_service = get_sms_service()
    result = sms_service.send_sms(user.id, phone, message)
    
    if result.success:
        response = f"""
{STYLES['sparkle']} <b>SMS Sent Successfully!</b>

{STYLES['phone']} <b>To:</b> <code>{phone}</code>
{STYLES['message']} <b>Message:</b> <blockquote>{message[:100]}{'...' if len(message) > 100 else ''}</blockquote>

{STYLES['chip']} <b>Text ID:</b> <code>{result.text_id}</code>
{STYLES['diamond']} <b>Quota Remaining:</b> {result.quota_remaining}

{STYLES['info']} Use <code>/sms_status {result.text_id}</code> to check delivery
"""
    else:
        response = f"""
{STYLES['error']} <b>SMS Failed to Send</b>

{STYLES['phone']} <b>To:</b> <code>{phone}</code>
{STYLES['message']} <b>Message:</b> <blockquote>{message[:100]}{'...' if len(message) > 100 else ''}</blockquote>

{STYLES['error']} <b>Error:</b> {result.error or 'Unknown error'}

{STYLES['info']} Check your quota with <code>/sms_stats</code>
"""
    
    await update.message.reply_text(response, parse_mode=ParseMode.HTML)


async def sms_contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /sms_contact command - Send SMS to saved contact"""
    if len(context.args) < 2:
        await update.message.reply_text(
            f"{STYLES['warning']} <b>Usage:</b>\n"
            f"<code>/sms_contact &lt;contact_name&gt; &lt;message&gt;</code>\n\n"
            f"<b>Example:</b>\n"
            f"<code>/sms_contact John Hello friend!</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    contact_name = context.args[0]
    message = " ".join(context.args[1:])
    user = update.effective_user
    
    # Show sending indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    sms_service = get_sms_service()
    result, contact = sms_service.send_sms_to_contact(user.id, contact_name, message)
    
    if result.success:
        response = f"""
{STYLES['sparkle']} <b>SMS Sent to Contact!</b>

{STYLES['contact']} <b>Name:</b> {contact.name if contact else contact_name}
{STYLES['phone']} <b>Phone:</b> <code>{contact.get_formatted_number() if contact else 'N/A'}</code>
{STYLES['message']} <b>Message:</b> <blockquote>{message[:100]}{'...' if len(message) > 100 else ''}</blockquote>

{STYLES['chip']} <b>Text ID:</b> <code>{result.text_id}</code>
{STYLES['diamond']} <b>Quota Remaining:</b> {result.quota_remaining}
"""
    else:
        response = f"""
{STYLES['error']} <b>Failed to Send SMS</b>

{STYLES['contact']} <b>Contact:</b> {contact_name}
{STYLES['error']} <b>Error:</b> {result.error or 'Unknown error'}

{STYLES['info']} Check contacts with <code>/sms_contacts</code>
"""
    
    await update.message.reply_text(response, parse_mode=ParseMode.HTML)


async def sms_contacts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /sms_contacts command - List saved contacts"""
    user = update.effective_user
    sms_service = get_sms_service()
    contacts = sms_service.get_contacts(user.id)
    
    if not contacts:
        contacts_msg = f"""
{STYLES['info']} <b>No contacts saved yet!</b>

Use <code>/sms_add &lt;name&gt; &lt;phone&gt;</code> to add contacts.

<b>Examples:</b>
<code>/sms_add Sophea 012345678</code>
<code>/sms_add John +85512345678</code>
"""
        await update.message.reply_text(contacts_msg, parse_mode=ParseMode.HTML)
        return
    
    contacts_msg = f"""
{STYLES['header']}

{STYLES['contact']} <b>Your Contacts ({len(contacts)})</b>

"""
    for contact in contacts:
        country = COUNTRY_CODES.get(contact.country_code, COUNTRY_CODES['kh'])
        contacts_msg += f"{country['flag']} <b>{contact.name}</b>\n"
        contacts_msg += f"   {STYLES['phone']} <code>{contact.get_formatted_number()}</code>\n"
        if contact.notes:
            contacts_msg += f"   {STYLES['bullet']} <i>{contact.notes}</i>\n"
        contacts_msg += "\n"
    
    contacts_msg += f"""
{STYLES['info']} Send SMS: <code>/sms_contact &lt;name&gt; &lt;message&gt;</code>

{STYLES['footer']}
"""
    await update.message.reply_text(contacts_msg, parse_mode=ParseMode.HTML)


async def sms_add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /sms_add command - Add a contact"""
    if len(context.args) < 2:
        await update.message.reply_text(
            f"{STYLES['warning']} <b>Usage:</b>\n"
            f"<code>/sms_add &lt;name&gt; &lt;phone&gt; [notes]</code>\n\n"
            f"<b>Examples:</b>\n"
            f"<code>/sms_add Sophea 012345678</code>\n"
            f"<code>/sms_add John +85512345678 Work colleague</code>\n"
            f"<code>/sms_add Mom 098765432 Family</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    name = context.args[0]
    phone = context.args[1]
    notes = " ".join(context.args[2:]) if len(context.args) > 2 else ""
    user = update.effective_user
    
    sms_service = get_sms_service()
    contact = sms_service.add_contact(user.id, name, phone, notes=notes)
    
    country = COUNTRY_CODES.get(contact.country_code, COUNTRY_CODES['kh'])
    
    response = f"""
{STYLES['sparkle']} <b>Contact Added!</b>

{STYLES['contact']} <b>Name:</b> {contact.name}
{STYLES['phone']} <b>Phone:</b> <code>{contact.get_formatted_number()}</code>
{country['flag']} <b>Country:</b> {country['name']}
{STYLES['bullet']} <b>Notes:</b> {contact.notes or 'None'}

{STYLES['info']} Send SMS: <code>/sms_contact {name} Hello!</code>
"""
    await update.message.reply_text(response, parse_mode=ParseMode.HTML)


async def sms_remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /sms_remove command - Remove a contact"""
    if not context.args:
        await update.message.reply_text(
            f"{STYLES['warning']} <b>Usage:</b> <code>/sms_remove &lt;name&gt;</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    name = context.args[0]
    user = update.effective_user
    
    sms_service = get_sms_service()
    result = sms_service.remove_contact(user.id, name)
    
    if result:
        response = f"{STYLES['sparkle']} Contact '<b>{name}</b>' removed successfully!"
    else:
        response = f"{STYLES['error']} Contact '<b>{name}</b>' not found!"
    
    await update.message.reply_text(response, parse_mode=ParseMode.HTML)


async def sms_history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /sms_history command - Show SMS history"""
    user = update.effective_user
    sms_service = get_sms_service()
    history = sms_service.get_history(user.id, limit=10)
    
    if not history:
        await update.message.reply_text(
            f"{STYLES['info']} No SMS history yet!\n\nSend your first SMS with <code>/sms_send</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    history_msg = f"""
{STYLES['header']}

{STYLES['history']} <b>SMS History (Last {len(history)})</b>

"""
    for entry in reversed(history):
        status_icon = STYLES['sparkle'] if entry.result.success else STYLES['error']
        history_msg += f"{status_icon} <b>{entry.to_name}</b>\n"
        history_msg += f"   {STYLES['phone']} <code>{entry.to_phone}</code>\n"
        history_msg += f"   {STYLES['message']} <i>{entry.message[:50]}{'...' if len(entry.message) > 50 else ''}</i>\n"
        history_msg += f"   {STYLES['chip']} {entry.sent_at.strftime('%Y-%m-%d %H:%M')}\n\n"
    
    history_msg += STYLES['footer']
    await update.message.reply_text(history_msg, parse_mode=ParseMode.HTML)


async def sms_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /sms_stats command - Show SMS statistics"""
    user = update.effective_user
    sms_service = get_sms_service()
    stats = sms_service.get_stats(user.id)
    
    stats_msg = f"""
{STYLES['header']}

{STYLES['sms']} <b>SMS Statistics</b>

<b>Usage:</b>
{STYLES['bullet']} Total SMS Sent: {stats['total_sent']}
{STYLES['bullet']} Contacts Saved: {stats['contacts_count']}
{STYLES['bullet']} History Entries: {stats['history_count']}

<b>Settings:</b>
{STYLES['bullet']} API Key: {stats['api_key']}
{STYLES['bullet']} Default Country: {stats['default_country']['flag']} {stats['default_country']['name']}

<b>Quota:</b>
{STYLES['bullet']} Remaining: {stats['quota_remaining']}

{STYLES['info']} Get your own API key at https://textbelt.com

{STYLES['footer']}
"""
    await update.message.reply_text(stats_msg, parse_mode=ParseMode.HTML)


async def sms_setkey_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /sms_setkey command - Set TextBelt API key"""
    if not context.args:
        await update.message.reply_text(
            f"{STYLES['warning']} <b>Usage:</b> <code>/sms_setkey &lt;api_key&gt;</code>\n\n"
            f"<b>Get your API key:</b> https://textbelt.com\n\n"
            f"{STYLES['info']} Use <code>textbelt</code> for 1 free SMS per day",
            parse_mode=ParseMode.HTML
        )
        return
    
    api_key = context.args[0]
    user = update.effective_user
    
    sms_service = get_sms_service()
    sms_service.set_api_key(user.id, api_key)
    
    masked_key = api_key[:4] + "****" if len(api_key) > 4 else "****"
    
    response = f"""
{STYLES['sparkle']} <b>API Key Updated!</b>

{STYLES['chip']} Key: <code>{masked_key}</code>

{STYLES['info']} Check quota with <code>/sms_stats</code>
"""
    await update.message.reply_text(response, parse_mode=ParseMode.HTML)


async def sms_setcountry_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /sms_setcountry command - Set default country"""
    if not context.args:
        countries_list = "\n".join([f"<code>{k}</code> - {v['flag']} {v['name']}" for k, v in list(COUNTRY_CODES.items())[:15]])
        await update.message.reply_text(
            f"{STYLES['warning']} <b>Usage:</b> <code>/sms_setcountry &lt;country_code&gt;</code>\n\n"
            f"<b>Available Countries:</b>\n{countries_list}\n...",
            parse_mode=ParseMode.HTML
        )
        return
    
    country_code = context.args[0].lower()
    user = update.effective_user
    
    sms_service = get_sms_service()
    result = sms_service.set_default_country(user.id, country_code)
    
    if result:
        country = COUNTRY_CODES[country_code]
        response = f"""
{STYLES['sparkle']} <b>Default Country Updated!</b>

{country['flag']} {country['name']} ({country['code']})

{STYLES['info']} Phone numbers without + will use this country code
"""
    else:
        response = f"{STYLES['error']} Invalid country code! Use <code>/sms_setcountry</code> to see options."
    
    await update.message.reply_text(response, parse_mode=ParseMode.HTML)


async def sms_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /sms_status command - Check SMS delivery status"""
    if not context.args:
        await update.message.reply_text(
            f"{STYLES['warning']} <b>Usage:</b> <code>/sms_status &lt;text_id&gt;</code>\n\n"
            f"{STYLES['info']} Get text ID from <code>/sms_history</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    text_id = context.args[0]
    sms_service = get_sms_service()
    status = sms_service.check_status(text_id)
    
    if status.get('success'):
        delivery_status = status.get('status', 'Unknown')
        status_icon = {
            'DELIVERED': STYLES['sparkle'],
            'SENT': STYLES['sms'],
            'SENDING': '⏳',
            'FAILED': STYLES['error'],
        }.get(delivery_status, '❓')
        
        response = f"""
{STYLES['sms']} <b>SMS Delivery Status</b>

{STYLES['chip']} <b>Text ID:</b> <code>{text_id}</code>
{status_icon} <b>Status:</b> {delivery_status}
"""
    else:
        response = f"""
{STYLES['error']} <b>Failed to Check Status</b>

{STYLES['chip']} <b>Text ID:</b> <code>{text_id}</code>
{STYLES['error']} Error: {status.get('error', 'Unknown error')}
"""
    
    await update.message.reply_text(response, parse_mode=ParseMode.HTML)


# ==================== INTERACTIVE SMS FLOW ====================

def _build_country_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard with country selection buttons."""
    buttons = []
    country_items = list(COUNTRY_CODES.items())
    # Two countries per row
    for i in range(0, len(country_items), 2):
        row = []
        for code, info in country_items[i:i + 2]:
            label = f"{info['flag']} {info['name']} ({info['code']})"
            row.append(InlineKeyboardButton(label, callback_data=f"sms_country:{code}"))
        buttons.append(row)
    buttons.append([InlineKeyboardButton(f"{STYLES['cancel']} Cancel", callback_data="sms_cancel")])
    return InlineKeyboardMarkup(buttons)


async def sms_send_interactive_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle /sms_send_interactive - Entry point for guided SMS wizard."""
    user = update.effective_user

    # Reset any previous interactive SMS state
    context.user_data.pop("sms_country", None)
    context.user_data.pop("sms_phone", None)
    context.user_data.pop("sms_carrier", None)
    context.user_data.pop("sms_message", None)

    intro = (
        f"{STYLES['sms']} <b>Interactive SMS Wizard</b>\n\n"
        f"{STYLES['bullet']} Step 1 of 4: Select your destination country\n\n"
        f"{STYLES['info']} Tap the country flag below to continue:"
    )
    await update.message.reply_text(
        intro,
        parse_mode=ParseMode.HTML,
        reply_markup=_build_country_keyboard(),
    )
    return SMS_COUNTRY_SELECTION


async def sms_country_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle country selection from inline keyboard callback."""
    query = update.callback_query
    await query.answer()

    if query.data == "sms_cancel":
        await query.edit_message_text(
            f"{STYLES['cancel']} <b>SMS Wizard cancelled.</b>",
            parse_mode=ParseMode.HTML,
        )
        return ConversationHandler.END

    # Parse country code from callback data
    _, country_code = query.data.split(":", 1)
    country = COUNTRY_CODES.get(country_code)
    if not country:
        await query.edit_message_text(
            f"{STYLES['error']} Invalid country selection. Please try again.",
            parse_mode=ParseMode.HTML,
        )
        return SMS_COUNTRY_SELECTION

    context.user_data["sms_country"] = country_code

    prompt = (
        f"{country['flag']} <b>Country selected:</b> {country['name']} ({country['code']})\n\n"
        f"{STYLES['phone']} <b>Step 2 of 4: Enter the recipient's phone number</b>\n\n"
        f"{STYLES['info']} Enter the number <b>without</b> the leading 0 or country code.\n"
        f"Example: for <code>012 345 678</code> enter <code>12345678</code>\n\n"
        f"Type /cancel to abort."
    )
    await query.edit_message_text(prompt, parse_mode=ParseMode.HTML)
    return SMS_PHONE_NUMBER_INPUT


async def sms_phone_number_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle phone number input: validate, detect carrier, start countdown."""
    user = update.effective_user
    phone_input = update.message.text.strip()
    country_code = context.user_data.get("sms_country", "kh")
    country = COUNTRY_CODES.get(country_code, COUNTRY_CODES["kh"])

    # Validate phone number
    is_valid, cleaned_phone, error_msg = validate_phone_number(phone_input, country_code)
    if not is_valid:
        await update.message.reply_text(
            f"{STYLES['error']} <b>Invalid phone number</b>\n\n"
            f"{error_msg}\n\n"
            f"{STYLES['info']} Please enter the number without leading 0 or country code.\n"
            f"Example: <code>96123456</code> (for Cambodia)\n\n"
            f"Type /cancel to abort.",
            parse_mode=ParseMode.HTML,
        )
        return SMS_PHONE_NUMBER_INPUT

    # Full E.164 number
    full_phone = f"{country['code']}{cleaned_phone}"
    context.user_data["sms_phone"] = full_phone

    # Detect carrier
    carrier_name, carrier_emoji = detect_carrier(cleaned_phone, country_code)
    context.user_data["sms_carrier"] = f"{carrier_emoji} {carrier_name}"

    # Acknowledgement with carrier info
    ack_msg = (
        f"{STYLES['check']} <b>Phone number accepted!</b>\n\n"
        f"{STYLES['phone']} <b>Number:</b> <code>{mask_phone_number(full_phone)}</code>\n"
        f"{STYLES['carrier']} <b>Carrier:</b> {carrier_emoji} {carrier_name}\n"
        f"{country['flag']} <b>Country:</b> {country['name']}\n\n"
        f"{STYLES['timer']} <b>Please wait 10 seconds before entering your message…</b>"
    )
    status_msg = await update.message.reply_text(ack_msg, parse_mode=ParseMode.HTML)

    # 10-second countdown
    for remaining in range(9, 0, -1):
        await asyncio.sleep(1)
        try:
            await status_msg.edit_text(
                ack_msg + f"\n\n⏳ <b>{remaining}s remaining…</b>",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass  # Message may have been deleted; continue countdown

    await asyncio.sleep(1)

    # Countdown done
    try:
        await status_msg.edit_text(
            f"{STYLES['check']} <b>Ready!</b>\n\n"
            f"{STYLES['phone']} <b>Number:</b> <code>{mask_phone_number(full_phone)}</code>\n"
            f"{STYLES['carrier']} <b>Carrier:</b> {carrier_emoji} {carrier_name}\n\n"
            f"{STYLES['message']} <b>Step 3 of 4: Enter your message</b>\n\n"
            f"Type the SMS text you want to send, then press Send.\n"
            f"Type /cancel to abort.",
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        await update.message.reply_text(
            f"{STYLES['message']} <b>Step 3 of 4: Enter your message</b>\n\n"
            f"Type the SMS text you want to send, then press Send.\n"
            f"Type /cancel to abort.",
            parse_mode=ParseMode.HTML,
        )

    return SMS_MESSAGE_INPUT


async def sms_message_input_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle message text input and show confirmation screen."""
    message_text = update.message.text.strip()
    if not message_text:
        await update.message.reply_text(
            f"{STYLES['error']} Message cannot be empty. Please enter your message.",
            parse_mode=ParseMode.HTML,
        )
        return SMS_MESSAGE_INPUT

    context.user_data["sms_message"] = message_text

    full_phone = context.user_data.get("sms_phone", "")
    carrier_display = context.user_data.get("sms_carrier", "❓ Unknown")
    country_code = context.user_data.get("sms_country", "kh")
    country = COUNTRY_CODES.get(country_code, COUNTRY_CODES["kh"])

    preview = message_text[:200] + ("…" if len(message_text) > 200 else "")

    confirmation_msg = (
        f"{STYLES['confirm']} <b>Step 4 of 4: Confirm and Send</b>\n\n"
        f"{STYLES['divider']}\n"
        f"{STYLES['phone']} <b>Recipient:</b> <code>{mask_phone_number(full_phone)}</code>\n"
        f"{country['flag']} <b>Country:</b> {country['name']}\n"
        f"{STYLES['carrier']} <b>Carrier:</b> {carrier_display}\n"
        f"{STYLES['divider']}\n"
        f"{STYLES['message']} <b>Message Preview:</b>\n"
        f"<blockquote>{preview}</blockquote>\n"
        f"{STYLES['divider']}\n\n"
        f"Tap <b>✅ Send</b> to confirm or <b>🚫 Cancel</b> to abort."
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ Send SMS", callback_data="sms_confirm_send"),
            InlineKeyboardButton("🚫 Cancel", callback_data="sms_confirm_cancel"),
        ]
    ]
    await update.message.reply_text(
        confirmation_msg,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return SMS_CONFIRMATION


async def sms_confirm_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle confirmation or cancellation of the interactive SMS send."""
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if query.data == "sms_confirm_cancel":
        await query.edit_message_text(
            f"{STYLES['cancel']} <b>SMS cancelled.</b>\n\nNo message was sent.",
            parse_mode=ParseMode.HTML,
        )
        _clear_sms_state(context)
        return ConversationHandler.END

    # Retrieve stored data
    full_phone = context.user_data.get("sms_phone", "")
    message_text = context.user_data.get("sms_message", "")
    carrier_display = context.user_data.get("sms_carrier", "❓ Unknown")

    if not full_phone or not message_text:
        await query.edit_message_text(
            f"{STYLES['error']} Session data lost. Please start over with /sms_send_interactive.",
            parse_mode=ParseMode.HTML,
        )
        _clear_sms_state(context)
        return ConversationHandler.END

    # Show "sending" status
    sending_msg = (
        f"{STYLES['sending']} <b>Sending SMS…</b>\n\n"
        f"{STYLES['phone']} <b>To:</b> <code>{mask_phone_number(full_phone)}</code>\n"
        f"{STYLES['carrier']} <b>Carrier:</b> {carrier_display}\n\n"
        f"⏳ <i>Please wait…</i>"
    )
    await query.edit_message_text(sending_msg, parse_mode=ParseMode.HTML)

    # Send the SMS
    sms_service = get_sms_service()
    result = sms_service.send_sms(user.id, full_phone, message_text)

    # Build real-time status message
    if result.success:
        status_msg = (
            f"{STYLES['check']} <b>SMS Sent Successfully!</b>\n\n"
            f"{STYLES['phone']} <b>To:</b> <code>{mask_phone_number(full_phone)}</code>\n"
            f"{STYLES['carrier']} <b>Carrier:</b> {carrier_display}\n"
            f"{STYLES['message']} <b>Message:</b>\n"
            f"<blockquote>{message_text[:100]}{'…' if len(message_text) > 100 else ''}</blockquote>\n\n"
            f"{STYLES['chip']} <b>Text ID:</b> <code>{result.text_id}</code>\n"
            f"{STYLES['diamond']} <b>Quota Remaining:</b> {result.quota_remaining}\n\n"
            f"{STYLES['pending']} <b>Status:</b> SENT → checking delivery…"
        )
        await query.edit_message_text(status_msg, parse_mode=ParseMode.HTML)

        # Poll delivery status a few times
        if result.text_id:
            await _poll_delivery_status(query, result, full_phone, carrier_display, message_text, sms_service)
    else:
        error_detail = result.error or "Unknown error"
        fail_msg = (
            f"{STYLES['error']} <b>SMS Failed to Send</b>\n\n"
            f"{STYLES['phone']} <b>To:</b> <code>{mask_phone_number(full_phone)}</code>\n"
            f"{STYLES['carrier']} <b>Carrier:</b> {carrier_display}\n\n"
            f"{STYLES['error']} <b>Error:</b> {error_detail}\n\n"
            f"{STYLES['retry']} <b>Suggestions:</b>\n"
            f"▸ Check your API key with /sms_setkey\n"
            f"▸ Verify quota with /sms_stats\n"
            f"▸ Confirm the phone number format\n"
            f"▸ Try again with /sms_send_interactive"
        )
        await query.edit_message_text(fail_msg, parse_mode=ParseMode.HTML)

    _clear_sms_state(context)
    return ConversationHandler.END


async def _poll_delivery_status(
    query,
    result: SMSResult,
    full_phone: str,
    carrier_display: str,
    message_text: str,
    sms_service,
    polls: int = 3,
    interval: float = 3.0,
) -> None:
    """Poll delivery status and update message in real-time."""
    status_icons = {
        "DELIVERED": (STYLES["delivered"], "DELIVERED ✅"),
        "SENT": (STYLES["sms"], "SENT 📱"),
        "SENDING": (STYLES["sending"], "SENDING ⏳"),
        "FAILED": (STYLES["error"], "FAILED ❌"),
        "PENDING": (STYLES["pending"], "PENDING ⏳"),
        "UNKNOWN": ("❓", "UNKNOWN ❓"),
    }

    for _ in range(polls):
        await asyncio.sleep(interval)
        status_data = sms_service.check_status(result.text_id)
        delivery_status = status_data.get("status", "UNKNOWN").upper()
        icon, label = status_icons.get(delivery_status, ("❓", delivery_status))

        updated_msg = (
            f"{STYLES['check']} <b>SMS Status Update</b>\n\n"
            f"{STYLES['phone']} <b>To:</b> <code>{mask_phone_number(full_phone)}</code>\n"
            f"{STYLES['carrier']} <b>Carrier:</b> {carrier_display}\n"
            f"{STYLES['message']} <b>Message:</b>\n"
            f"<blockquote>{message_text[:100]}{'…' if len(message_text) > 100 else ''}</blockquote>\n\n"
            f"{STYLES['chip']} <b>Text ID:</b> <code>{result.text_id}</code>\n"
            f"{icon} <b>Status:</b> {label}"
        )
        try:
            await query.edit_message_text(updated_msg, parse_mode=ParseMode.HTML)
        except Exception:
            break  # Message no longer editable

        if delivery_status in ("DELIVERED", "FAILED"):
            break


def _clear_sms_state(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear interactive SMS wizard state from user_data."""
    for key in ("sms_country", "sms_phone", "sms_carrier", "sms_message"):
        context.user_data.pop(key, None)


# Callback query handlers
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "start_chat":
        await query.edit_message_text(
            text=f"{STYLES['sparkle']} Chat mode ready! Type /chat to begin.",
            parse_mode=ParseMode.HTML
        )
    elif query.data == "show_commands":
        commands = get_commands()
        cmd_list = "\n".join([f"{STYLES['bullet']} <code>{c.name}</code>" for c in list(commands)[:15]])
        await query.edit_message_text(
            text=f"{STYLES['gear']} <b>Available Commands</b>\n\n{cmd_list}\n\n<i>Use /commands for full list</i>",
            parse_mode=ParseMode.HTML
        )
    elif query.data == "show_tools":
        tools = get_tools()
        tool_list = "\n".join([f"{STYLES['bullet']} <code>{t.name}</code>" for t in list(tools)[:15]])
        await query.edit_message_text(
            text=f"{STYLES['tools']} <b>Available Tools</b>\n\n{tool_list}\n\n<i>Use /tools for full list</i>",
            parse_mode=ParseMode.HTML
        )
    elif query.data == "show_help":
        await query.edit_message_text(
            text=get_help_message(),
            parse_mode=ParseMode.HTML
        )


# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        error_msg = f"""
{STYLES['error']} <b>An error occurred!</b>

<code>{str(context.error)}</code>

Please try again or contact support.
"""
        await update.effective_message.reply_text(error_msg, parse_mode=ParseMode.HTML)


def main() -> None:
    """Start the bot"""
    # Get token from environment
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    if not token:
        print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║  🤖 AI STAND WY2.5 - Telegram Bot                           ║
║                                                              ║
║  Error: TELEGRAM_BOT_TOKEN not found!                        ║
║                                                              ║
║  Please set your bot token:                                  ║
║  export TELEGRAM_BOT_TOKEN="your_bot_token_here"            ║
║                                                              ║
║  Get your token from @BotFather on Telegram                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        sys.exit(1)
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║  🤖 AI STAND WY2.5 - Starting up...                          ║
║                                                              ║
║  Version: {BOT_VERSION:<48}║
║  Creator: {BOT_CREATOR:<48}║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Create application
    application = Application.builder().token(token).build()

    # Add conversation handler for chat mode
    chat_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("chat", chat_command)],
        states={
            CHAT_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, chat_message_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
    )

    # Interactive SMS wizard conversation handler
    sms_interactive_handler = ConversationHandler(
        entry_points=[CommandHandler("sms_send_interactive", sms_send_interactive_command)],
        states={
            SMS_COUNTRY_SELECTION: [
                CallbackQueryHandler(sms_country_callback, pattern=r"^sms_country:"),
                CallbackQueryHandler(sms_country_callback, pattern=r"^sms_cancel$"),
            ],
            SMS_PHONE_NUMBER_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, sms_phone_number_handler),
            ],
            SMS_MESSAGE_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, sms_message_input_handler),
            ],
            SMS_CONFIRMATION: [
                CallbackQueryHandler(sms_confirm_callback, pattern=r"^sms_confirm_"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
        allow_reentry=True,
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(chat_conv_handler)
    application.add_handler(sms_interactive_handler)
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(CommandHandler("session", session_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("commands", commands_command))
    application.add_handler(CommandHandler("tools", tools_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("manifest", manifest_command))
    application.add_handler(CommandHandler("exec", exec_command))
    application.add_handler(CommandHandler("tool", tool_command))
    application.add_handler(CommandHandler("route", route_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # SMS handlers
    application.add_handler(CommandHandler("sms", sms_command))
    application.add_handler(CommandHandler("sms_send", sms_send_command))
    application.add_handler(CommandHandler("sms_contact", sms_contact_command))
    application.add_handler(CommandHandler("sms_contacts", sms_contacts_command))
    application.add_handler(CommandHandler("sms_add", sms_add_command))
    application.add_handler(CommandHandler("sms_remove", sms_remove_command))
    application.add_handler(CommandHandler("sms_history", sms_history_command))
    application.add_handler(CommandHandler("sms_stats", sms_stats_command))
    application.add_handler(CommandHandler("sms_setkey", sms_setkey_command))
    application.add_handler(CommandHandler("sms_setcountry", sms_setcountry_command))
    application.add_handler(CommandHandler("sms_status", sms_status_command))
    
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    print("✅ Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
