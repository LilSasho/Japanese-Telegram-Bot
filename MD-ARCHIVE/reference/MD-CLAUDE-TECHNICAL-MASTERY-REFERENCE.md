# CLAUDE TECHNICAL MASTERY REFERENCE

**Purpose**: Searchable institutional memory for debugging patterns and solutions

---

## 🎯 **CRITICAL: SESSION START CHECKLIST**

### **Working Relationship & Role Dynamics**
- **Developer Role**: Sole developer (Junior level)
- **My Advisory Role**: Senior technical advisor with clear explanations
- **Challenge Style**: Suggest alternatives with explanations when approaches have issues
- **Communication**: Provide technical depth with best practice guidance

---

## 🚨 **DATABASE SAFETY PROTOCOLS**

### **SQLAlchemy Async Session Management**
**Problem**: Connection leaks in async SQLAlchemy operations
**Solution**: Always use async context managers
```python
# Correct pattern
async with AsyncSession() as session:
    result = await session.execute(query)
    await session.commit()
# Session automatically closed

# Avoid: Manual session management without proper cleanup
```

### **Database Initialization**
**Problem**: Database not initialized before first run
**Solution**: Always run initialization command
```bash
python -m app.core.database init
```

*Additional patterns will be added as they are discovered during development*

---

## 🧠 **AUTHENTICATION & SESSION MANAGEMENT** 

### **Telegram Bot Token Security**
**Problem**: Bot token exposure in logs or code
**Solution**: Always use environment variables, never hardcode
```python
# Correct
bot_token = os.getenv("BOT_TOKEN")

# Never do this
bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
```

*Additional authentication patterns will be added as they are discovered*

---

## 🎨 **UI/MODAL PATTERNS & CONFLICTS**

### **Telegram Keyboard Management**
**Problem**: Keyboard state conflicts between different bot interactions
**Solution**: Clear keyboard state appropriately between interactions

*Additional UI patterns will be added as they are discovered*

---

## 🔍 **INFINITE LOOP DEBUGGING**

### **Async/Await Loop Prevention**
**Problem**: Infinite loops in async functions
**Investigation**: Check for missing `await` keywords
**Solution**: Ensure all async calls are properly awaited
```python
# Correct
result = await async_function()

# Problematic - missing await can cause loops
result = async_function()  # Returns coroutine, not result
```

*Additional loop debugging patterns will be added as they are discovered*

---

## 🤖 **API & DATA FETCHING PATTERNS**

### **Telegram API Rate Limiting**
**Problem**: 429 Too Many Requests errors from Telegram API
**Solution**: Implement exponential backoff and respect rate limits
```python
import asyncio
from telegram.error import RetryAfter

try:
    await bot.send_message(chat_id, text)
except RetryAfter as e:
    await asyncio.sleep(e.retry_after)
    await bot.send_message(chat_id, text)
```

*Additional API patterns will be added as they are discovered*

---

## 📱 **MOBILE & CROSS-PLATFORM ISSUES**

### **Unicode Character Rendering**
**Problem**: Japanese characters not displaying correctly
**Investigation**: Check UTF-8 encoding throughout pipeline
**Solution**: Ensure proper encoding at database and message levels
```python
# Ensure UTF-8 encoding
text = "こんにちは"  # Should render correctly
await bot.send_message(chat_id, text, parse_mode=None)
```

*Additional mobile patterns will be added as they are discovered*

---

## 🚀 **BUILD & DEPLOYMENT DEBUGGING**

### **Virtual Environment Issues**
**Problem**: Import errors or missing dependencies
**Solution**: Verify virtual environment activation and requirements installation
```bash
# Always activate first
source venv/bin/activate

# Verify activation
which python  # Should point to venv/bin/python

# Install dependencies
pip install -r requirements.txt
```

### **Code Quality Pipeline**
**Problem**: Black formatting or flake8 issues blocking development
**Solution**: Run code quality tools before committing
```bash
# Auto-fix formatting
black app/ tests/

# Check for issues
flake8 app/ tests/

# Verify imports work
python -c "import app"
```

*Additional build patterns will be added as they are discovered*

---

## 🎯 **PROJECT-SPECIFIC PATTERNS**

### **Japanese Learning Content Management**
**Pattern**: Structured JSON data for character learning
```json
{
  "character": "あ",
  "romaji": "a",
  "meaning": "vowel sound 'ah'",
  "difficulty": 1,
  "examples": ["あした (ashita) - tomorrow"]
}
```

### **Spaced Repetition Algorithm Implementation**
**Pattern**: SM-2 algorithm with proper interval calculation
```python
def calculate_next_interval(previous_interval, ease_factor, quality):
    if quality >= 3:
        if previous_interval == 0:
            return 1
        elif previous_interval == 1:
            return 6
        else:
            return int(previous_interval * ease_factor)
    else:
        return 1
```

---

*This file grows over time as you encounter and solve technical challenges. Each pattern should include: Problem, Investigation, Solution, and Reusable Code Examples.*