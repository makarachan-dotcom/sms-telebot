# 🤖 AI STAND WY2.5 - Advanced Telegram Bot

<p align="center">
  <img src="https://img.shields.io/badge/Version-2.5.0-blue?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/Python-3.9+-green?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Telegram-Bot-blue?style=for-the-badge&logo=telegram" alt="Telegram">
  <img src="https://img.shields.io/badge/Infobip-SMS-orange?style=for-the-badge" alt="Infobip">
</p>

<p align="center">
  <i>"Standing at the frontier of AI assistance"</i>
</p>

---

## ✨ Features

- **🧠 Natural Language Processing** - Chat naturally with intelligent routing
- **⚡ 400+ Commands** - Full integration with Claude Code architecture
- **🔧 300+ Tools** - Extensive tool library for various operations
- **💬 Session Management** - Persistent conversation history
- **🎯 Smart Routing** - Automatic command/tool matching
- **📊 User Statistics** - Track your usage and activity
- **🔒 Admin Controls** - Ban/unban users, view global stats, list users
- **🎨 Cyberpunk Styling** - Cool visual design
- **📱 Infobip SMS** - Send SMS via Infobip API (Cambodia 🇰🇭 +855 only)
- **🇰🇭 Khmer Support** - Full support for Cambodian phone numbers
- **🗄️ SQLite Database** - Persistent user profiles, SMS logs, rate limiting
- **⛔ Rate Limiting** - Configurable daily SMS quota per user

---

## 🚀 Quick Start

### 1. Get Your Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Start a chat and send `/newbot`
3. Follow the instructions to create your bot
4. Copy the bot token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Get Your Infobip API Key

1. Sign in to [Infobip Portal](https://portal.infobip.com/dev/api-keys)
2. Create a new API key
3. Copy the **API Key** and your personal **Base URL**
   (format: `https://XXXX.api.infobip.com`)

### 3. Install Dependencies

```bash
# Clone or download this repository
cd sms-telebot

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and fill in your values:
# TELEGRAM_BOT_TOKEN=your_bot_token_here
# INFOBIP_API_KEY=your_infobip_api_key
# INFOBIP_BASE_URL=https://XXXX.api.infobip.com
# ADMIN_USER_IDS=your_telegram_id
```

### 5. Run the Bot

```bash
python bot.py
```

Or use the startup script:

```bash
# On Windows:
start_bot.bat

# On macOS/Linux:
./start_bot.sh
```

---

## 📱 Infobip SMS Commands

### Interactive SMS Flow (Recommended)

| Command | Description |
|---------|-------------|
| `/sendsms` | **Start the interactive Infobip SMS wizard** |
| `/ibsmshistory` | View your Infobip SMS send history |

The `/sendsms` command guides you through a **step-by-step flow**:

1. Press **📤 Send SMS** button
2. Enter the Cambodian phone number (see formats below)
3. Type your message
4. Confirm with the **✅ Confirm & Send** button

#### Supported Phone Number Formats (+855 Cambodia only)

| Input | Interpreted as |
|-------|---------------|
| `012345678` | `+85512345678` (leading zero stripped) |
| `12345678` | `+85512345678` (prefix added) |
| `+85512345678` | `+85512345678` (used as-is) |
| `85512345678` | `+85512345678` (plus sign added) |

---

## 🛡️ Admin Commands

> **Note:** Admin access requires your Telegram user ID to be listed in `ADMIN_USER_IDS`.

| Command | Description |
|---------|-------------|
| `/adminstats` | Global platform statistics (users, SMS totals) |
| `/users` | List all registered users with ban status |
| `/ban <user_id>` | Ban a user from the SMS service |
| `/unban <user_id>` | Lift a ban on a user |

---

## 📊 Rate Limiting

Non-admin users are limited to **`MAX_SMS_PER_DAY`** SMS per calendar day (default: 10).

- Configure via the `MAX_SMS_PER_DAY` environment variable in `.env`.
- Admins (listed in `ADMIN_USER_IDS`) bypass rate limits.
- The quota resets at midnight UTC.

---

## 🤖 Bot Commands

### Core Commands
| Command | Description |
|---------|-------------|
| `/start` | Start the bot and show welcome message |
| `/help` | Show all available commands |
| `/about` | About the bot |
| `/chat` | Enter interactive chat mode |
| `/clear` | Clear conversation history |
| `/session` | Show session information |
| `/stats` | Show your usage statistics |

### System Commands
| Command | Description |
|---------|-------------|
| `/commands` | List all available commands |
| `/tools` | List all available tools |
| `/search <query>` | Search commands and tools |
| `/manifest` | Show system manifest |

### Execution Commands
| Command | Description |
|---------|-------------|
| `/exec <command>` | Execute a specific command |
| `/tool <tool> [payload]` | Execute a specific tool |
| `/route <query>` | Route a query and show matches |

### Legacy SMS Commands (TextBelt)
| Command | Description |
|---------|-------------|
| `/sms` | SMS service menu |
| `/sms_send <phone> <msg>` | Send SMS to phone number |
| `/sms_contact <name> <msg>` | Send SMS to saved contact |
| `/sms_contacts` | List saved contacts |
| `/sms_add <name> <phone>` | Add a contact |
| `/sms_remove <name>` | Remove a contact |
| `/sms_history` | View SMS history |
| `/sms_stats` | View SMS statistics |
| `/sms_setkey <key>` | Set TextBelt API key |
| `/sms_setcountry <code>` | Set default country |

---

## 🏗️ Architecture

```
sms-telebot/
├── bot.py                 # Main bot entry point
├── config.py              # Environment / config loader (Infobip + Telegram)
├── database.py            # SQLite3 data-access layer
├── infobip.py             # Infobip REST API client (+855 phone normalisation)
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
├── README.md              # This file
├── src/                   # Core source code (AI routing engine)
│   ├── commands.py        # Command registry (400+)
│   ├── tools.py           # Tool registry (300+)
│   ├── query_engine.py    # Query processing
│   ├── runtime.py         # Execution runtime
│   ├── session_store.py   # Session management
│   ├── sms_service.py     # Legacy SMS service (TextBelt API)
│   └── reference_data/    # Command/tool snapshots
├── config/                # Bot configuration
│   └── bot_config.py      # Bot settings
├── data/                  # Runtime data (created automatically)
│   └── sms_bot.db         # SQLite database
└── logs/                  # Log files (created automatically)
    └── sms_bot.log        # Application log
```

### Key Modules

| Module | Responsibility |
|--------|---------------|
| `config.py` | Load `.env`, expose typed constants (`INFOBIP_API_KEY`, `TELEGRAM_TOKEN`, `MAX_SMS_PER_DAY`, …) |
| `database.py` | SQLite layer: user registration, ban list, daily quota, SMS audit log |
| `infobip.py` | `InfobipClient` wrapper, `format_cambodian_number()` normalisation |
| `bot.py` | Telegram handlers, `ConversationHandler` for interactive SMS flow, admin commands |

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Your bot token from @BotFather | **Required** |
| `INFOBIP_API_KEY` | Infobip App API key | **Required for SMS** |
| `INFOBIP_BASE_URL` | Your Infobip personal base URL | **Required for SMS** |
| `ADMIN_USER_IDS` | Comma-separated admin Telegram IDs | None |
| `MAX_SMS_PER_DAY` | Daily SMS quota per non-admin user | `10` |
| `LOG_LEVEL` | Logging level (`DEBUG`/`INFO`/`WARNING`/`ERROR`) | `INFO` |
| `DATA_DIR` | Directory for SQLite database | `./data` |
| `LOG_DIR` | Directory for log files | `./logs` |
| `SESSION_DIR` | Directory for AI session files | `./sessions` |

---

## 💡 Usage Examples

### Send an SMS (interactive)
```
User: /sendsms
Bot:  📱 Infobip SMS Service
      Cambodia 🇰🇭 (+855) numbers only.
      📊 Today: 0/10 messages sent.
      [📤 Send SMS]  [❌ Cancel]

User: clicks "📤 Send SMS"
Bot:  📞 Step 1/2 — Enter recipient phone number
      ...

User: 012345678
Bot:  ✅ Recipient: +85512345678
      ✍️ Step 2/2 — Type your message

User: Hello from the bot!
Bot:  📋 Confirm your SMS
      📞 To: +85512345678
      💬 Message: Hello from the bot!
      [✅ Confirm & Send]  [❌ Cancel]

User: clicks "✅ Confirm & Send"
Bot:  ✅ SMS Sent Successfully!
      🆔 Message ID: ABC-123
      📊 Status: PENDING_ENROUTE
```

### Admin – Ban a user
```
Admin: /ban 987654321
Bot:   🚫 User 987654321 has been banned.
```

---

## 📝 License

This project is based on the Claude Code Python Port.

---

## 🙏 Credits

- **Created by:** Kimi K2.5
- **Architecture:** Claude Code Python Port
- **SMS API:** [Infobip](https://www.infobip.com/)
- **Framework:** python-telegram-bot

---

<p align="center">
  <i>Made with 💜 and lots of ☕</i>
</p>

<p align="center">
  <b>AI STAND WY2.5</b> - "The future of AI assistance is here"
</p>


<p align="center">
  <img src="https://img.shields.io/badge/Version-2.5.0-blue?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/Python-3.9+-green?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Telegram-Bot-blue?style=for-the-badge&logo=telegram" alt="Telegram">
</p>

<p align="center">
  <i>"Standing at the frontier of AI assistance"</i>
</p>

---

## ✨ Features

- **🧠 Natural Language Processing** - Chat naturally with intelligent routing
- **⚡ 400+ Commands** - Full integration with Claude Code architecture
- **🔧 300+ Tools** - Extensive tool library for various operations
- **💬 Session Management** - Persistent conversation history
- **🎯 Smart Routing** - Automatic command/tool matching
- **📊 User Statistics** - Track your usage and activity
- **🔒 Admin Controls** - Built-in admin features
- **🎨 Cyberpunk Styling** - Cool visual design
- **📱 SMS Service** - Send SMS worldwide via TextBelt API
- **🇰🇭 Khmer Support** - Full support for Cambodian phone numbers

---

## 🚀 Quick Start

### 1. Get Your Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Start a chat and send `/newbot`
3. Follow the instructions to create your bot
4. Copy the bot token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Install Dependencies

```bash
# Clone or download this repository
cd ai_stand_wy25_bot

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your bot token
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### 4. Run the Bot

```bash
python bot.py
```

Or use the startup script:

```bash
# On Windows:
start_bot.bat

# On macOS/Linux:
./start_bot.sh
```

---

## 📱 Bot Commands

### Core Commands
| Command | Description |
|---------|-------------|
| `/start` | Start the bot and show welcome message |
| `/help` | Show all available commands |
| `/about` | About the bot |
| `/chat` | Enter interactive chat mode |
| `/clear` | Clear conversation history |
| `/session` | Show session information |
| `/stats` | Show your usage statistics |

### System Commands
| Command | Description |
|---------|-------------|
| `/commands` | List all available commands |
| `/tools` | List all available tools |
| `/search <query>` | Search commands and tools |
| `/manifest` | Show system manifest |

### Execution Commands
| Command | Description |
|---------|-------------|
| `/exec <command>` | Execute a specific command |
| `/tool <tool> [payload]` | Execute a specific tool |
| `/route <query>` | Route a query and show matches |

### Admin Commands
| Command | Description |
|---------|-------------|
| `/status` | Show bot system status |

### SMS Commands 📱
| Command | Description |
|---------|-------------|
| `/sms` | SMS service menu |
| `/sms_send <phone> <msg>` | Send SMS to phone number |
| `/sms_contact <name> <msg>` | Send SMS to saved contact |
| `/sms_contacts` | List saved contacts |
| `/sms_add <name> <phone>` | Add a contact |
| `/sms_remove <name>` | Remove a contact |
| `/sms_history` | View SMS history |
| `/sms_stats` | View SMS statistics |
| `/sms_setkey <key>` | Set TextBelt API key |
| `/sms_setcountry <code>` | Set default country |

**📖 See [SMS_GUIDE.md](SMS_GUIDE.md) for detailed SMS documentation!**

---

## 🏗️ Architecture

This bot is built on the **Claude Code Python Port** architecture:

```
ai_stand_wy25_bot/
├── bot.py                 # Main bot entry point
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── README.md             # This file
├── SMS_GUIDE.md          # SMS service documentation
├── src/                  # Core source code
│   ├── commands.py       # Command registry (400+)
│   ├── tools.py          # Tool registry (300+)
│   ├── query_engine.py   # Query processing
│   ├── runtime.py        # Execution runtime
│   ├── session_store.py  # Session management
│   ├── sms_service.py    # SMS service (TextBelt API)
│   └── reference_data/   # Command/tool snapshots
├── config/               # Configuration
│   └── bot_config.py     # Bot settings
├── data/                 # User data (created at runtime)
│   └── sms/              # SMS data storage
└── sessions/             # Session storage (created at runtime)
```

---

## 💡 Usage Examples

### Chat Mode
```
User: /chat
Bot: Chat Mode Activated! Session ID: abc123...

User: How do I search for files?
Bot: 🤖 Processing your request...
    🎯 Matched:
      ⚙️ SearchCommand (3)
      🔧 GrepTool (2)
      🔧 FindTool (2)
    
    ⚡ Response:
    You can use the SearchCommand or GrepTool to search for files...
```

### Execute Commands
```
User: /exec GitStatusTool
Bot: ✨ Command Executed
    Command: GitStatusTool
    Result: Git status would be displayed here...
```

### Search
```
User: /search git
Bot: 🎯 Search Results for "git"
    ⚙️ Commands (10):
      • GitStatusCommand
      • GitCommitCommand
      • GitPushCommand
      ...
    
    🔧 Tools (15):
      • GitTool
      • GitStatusTool
      • GitLogTool
      ...
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Your bot token from @BotFather | Required |
| `ADMIN_USER_IDS` | Comma-separated admin Telegram IDs | None |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | INFO |
| `DATA_DIR` | Directory for user data | ./data |
| `SESSION_DIR` | Directory for sessions | ./sessions |

### Bot Settings

Edit `config/bot_config.py` to customize:

- Bot name and version
- Message limits
- Feature toggles
- Query engine settings

---

## 🛠️ Development

### Adding New Commands

1. Add command definition to `src/reference_data/commands_snapshot.json`
2. Implement handler in `bot.py`
3. Register in `main()` function

### Adding New Tools

1. Add tool definition to `src/reference_data/tools_snapshot.json`
2. Implement tool logic in appropriate module

---

## 📝 License

This project is based on the Claude Code Python Port.

---

## 🙏 Credits

- **Created by:** Kimi K2.5
- **Architecture:** Claude Code Python Port
- **Framework:** python-telegram-bot

---

<p align="center">
  <i>Made with 💜 and lots of ☕</i>
</p>

<p align="center">
  <b>AI STAND WY2.5</b> - "The future of AI assistance is here"
</p>
