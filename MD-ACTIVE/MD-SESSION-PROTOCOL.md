# 🎯 SESSION PROTOCOL - Japanese Learning Telegram Bot

## 🚨 MANDATORY SECURITY ACKNOWLEDGMENT
**I will not open or read any `.env*` files. I will reference environment variable NAMES only.**

---

## 🤝 WORKING RELATIONSHIP

**Your Role**: Sole Developer (Junior level)
**My Role**: Senior Technical Advisor
**Challenge Style**: Suggest alternatives with clear explanations when approaches have issues
**Communication**: Provide technical depth with clear explanations and best practice guidance

---

## 📋 PROJECT CONTEXT

**Project**: Japanese Learning Telegram Bot
**Tech Stack**: 
- Python 3.12.3 + python-telegram-bot v22.2
- SQLAlchemy 2.0.35 (async) + SQLite/PostgreSQL
- Pydantic 2.12.0a1 + pytest + Black formatting
- Spaced repetition learning system (SM-2 algorithm)

**Current Status**: Development-ready infrastructure complete
**Branch**: main (auto-deploys when ready)
**Environment**: Local development only

---

## 🛠 DEVELOPMENT COMMANDS

### Setup & Running
```bash
# Environment setup
source venv/bin/activate
pip install -r requirements.txt

# Database initialization  
python -m app.core.database init

# Run bot
python main.py
```

### Code Quality
```bash
# Auto-format code
black app/ tests/

# Check style and errors
flake8 app/ tests/

# Run tests with coverage
pytest --cov=app tests/

# Verify imports
python -c "import app"
```

---

## 🎯 CRITICAL DEBUGGING PATTERNS

### **Async/Await Consistency**
- All Telegram handlers must be async
- SQLAlchemy queries need `await`
- Ensure proper async context management

### **Database Session Management** 
- Always close SQLAlchemy async sessions
- Prevent connection leaks with proper session cleanup
- Use async context managers where possible

### **Telegram API Rate Limiting**
- Handle 429 responses gracefully
- Implement proper error handling for rate limits
- Respect Bot API limitations

### **Unicode Handling**
- Japanese characters need proper UTF-8 encoding
- Test character rendering throughout pipeline
- Validate character storage and retrieval

---

## 🤖 SESSION AUTOMATION

### Session Start Protocol
When user says "session start":
1. Acknowledge security (`.env*` protection)
2. Read all MD-ACTIVE files
3. Echo working relationship and project status  
4. Create TodoWrite from current priorities
5. Auto-activate Technical Mastery Reference
6. Begin work on first priority

### Session End Protocol
When user says "session end":
1. Create new session bookmark with completion status
2. Archive previous bookmark to MD-ARCHIVE/bookmarks/
3. Update Technical Mastery with new patterns
4. Ask about git commit and deploy
5. Confirm session completion

---

## 🔧 ENVIRONMENT VARIABLES (NAMES ONLY)
- `BOT_TOKEN` - Telegram bot authentication
- `DATABASE_URL` - Database connection string
- Additional learning system configuration variables

**Security Note**: Values never revealed, reference by NAME only.

---

**Next Session**: Ready to implement core learning content system and spaced repetition algorithm.