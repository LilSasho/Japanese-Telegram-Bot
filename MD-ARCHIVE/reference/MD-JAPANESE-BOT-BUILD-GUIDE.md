# 🏗 JAPANESE TELEGRAM BOT - BUILD GUIDE

## 🚀 QUICK START

### Prerequisites
- Python 3.12.3+ 
- Virtual environment support
- Git for version control

### Initial Setup
```bash
# Clone and enter project
git clone <repository-url>
cd Japanese-Telegram-Bot

# Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dependencies
pip install -r requirements.txt

# Database setup
python -m app.core.database init
```

### Development Workflow
```bash
# Start development session
source venv/bin/activate

# Before coding (code quality check)
black app/ tests/
flake8 app/ tests/

# Run bot locally
python main.py

# Testing
pytest --cov=app tests/

# Import verification
python -c "import app"
```

---

## 🏛 ARCHITECTURE OVERVIEW

### Layer Structure
```
app/
├── bot/           # Telegram bot interaction layer
├── core/          # System infrastructure  
├── services/      # Business logic orchestration
├── models/        # Data structures & database entities
└── utils/         # Reusable utility functions
```

### Key Design Patterns
- **Async/Await**: All Telegram handlers and database operations
- **Service Layer**: Business logic separated from bot handlers
- **Repository Pattern**: Data access abstraction through SQLAlchemy
- **Dependency Injection**: Clean separation of concerns

---

## 🗄 DATABASE ARCHITECTURE

### SQLAlchemy Async Configuration
- **Engine**: Async SQLAlchemy 2.0.35
- **Database**: SQLite (development) / PostgreSQL (production)
- **Sessions**: Async context managers for proper cleanup

### Core Models
- **User**: Telegram user data and learning preferences
- **Lesson**: Learning content structure (hiragana, katakana, kanji)
- **Progress**: Spaced repetition tracking and user performance

---

## 🧠 LEARNING SYSTEM DESIGN

### Spaced Repetition (SM-2 Algorithm)
```python
# Core algorithm components
- Ease Factor: Character difficulty adjustment
- Interval: Time between reviews
- Repetition Count: Number of successful reviews
- Quality: User response quality (0-5 scale)
```

### Content Organization
```
data/content/
├── hiragana/basic.json      # 46 basic characters
├── katakana/basic.json      # 46 basic characters  
├── vocabulary/beginner.json # Common words
└── cultural_notes/         # Context and usage
```

---

## 🤖 TELEGRAM BOT INTEGRATION

### Bot Configuration
- **Framework**: python-telegram-bot v22.2
- **Update Mode**: Polling (development) / Webhooks (production)
- **Rate Limiting**: Built-in handling for API limits
- **Error Handling**: Comprehensive async error management

### Handler Architecture
```python
# Handler pattern
async def lesson_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1. Extract user intent
    # 2. Call service layer
    # 3. Format response
    # 4. Send to user
```

---

## 🧪 TESTING STRATEGY

### Testing Pyramid
- **Unit Tests**: Individual component testing (`tests/unit/`)
- **Integration Tests**: Service interaction testing (`tests/integration/`) 
- **E2E Tests**: Full user journey testing (`tests/e2e/`)

### Test Configuration
```bash
# Test execution
pytest                    # All tests
pytest tests/unit/       # Unit tests only
pytest --cov=app tests/  # With coverage report
```

---

## 📊 MONITORING & OBSERVABILITY

### Development Monitoring
- **Logs**: Structured logging with appropriate levels
- **Metrics**: User engagement and learning effectiveness
- **Health Checks**: Database connectivity and bot responsiveness

### Production Setup (Future)
```
monitoring/
├── prometheus/    # Metrics collection
├── grafana/      # Visualization dashboards  
└── alerts/       # Alerting rules
```

---

## 🚀 DEPLOYMENT PIPELINE

### Current: Local Development
```bash
# Development server
python main.py
```

### Future: Production Deployment
```bash
# Docker containerization
docker build -t japanese-bot .
docker run -d japanese-bot

# Kubernetes deployment
kubectl apply -f deployment/kubernetes/
```

---

## 🔧 TROUBLESHOOTING

### Common Issues

**Import Errors**
- Verify virtual environment activation
- Check requirements.txt installation
- Validate Python path configuration

**Database Connection Issues**
- Ensure database initialization: `python -m app.core.database init`
- Check DATABASE_URL environment variable
- Verify SQLAlchemy async session management

**Telegram Bot Issues**
- Validate BOT_TOKEN environment variable
- Check internet connectivity
- Verify Telegram API rate limiting compliance

**Unicode/Japanese Character Issues**
- Ensure UTF-8 encoding throughout pipeline
- Test character storage and retrieval
- Validate font support in target environment

---

## 📚 DEVELOPMENT RESOURCES

### Key Documentation
- [python-telegram-bot Documentation](https://python-telegram-bot.readthedocs.io/)
- [SQLAlchemy 2.0 Async Guide](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [SM-2 Spaced Repetition Algorithm](https://www.supermemo.com/en/archives1990-2015/english/ol/sm2)

### Code Quality Tools
- **Black**: Code formatting (automatic)
- **flake8**: Style and error checking
- **pytest**: Testing framework with async support
- **mypy**: Static type checking (optional)

---

This guide provides the foundation for building and maintaining the Japanese Learning Telegram Bot with proper architecture, testing, and deployment practices.