# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Japanese Learning Telegram Bot built with Python. The bot helps users learn Japanese through progressive lessons, spaced repetition, flashcards, and interactive quizzes covering hiragana, katakana, and basic kanji.

## Development Commands

### Running the Bot
```bash
# Activate virtual environment (Python 3.12.3)
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (with corrected Pydantic version)
pip install -r requirements.txt

# Initialize database
python -m app.core.database init

# Run the bot
python main.py
```

### Code Quality Tools
```bash
# Format code (auto-fixes formatting issues)
black app/ tests/

# Lint code (check style and errors)
flake8 app/ tests/

# Type checking
mypy app/

# Import validation
python -c "import app; print('Import check: OK')"
```

### Testing Infrastructure
```bash
# Run all tests (when test cases are written)
pytest

# Run with coverage reporting
pytest --cov=app tests/

# Run specific test categories
pytest tests/unit/         # Unit tests
pytest tests/integration/  # Integration tests
pytest tests/e2e/          # End-to-end tests

# Install testing dependencies
pip install pytest pytest-cov pytest-asyncio black flake8 mypy
```

## Architecture

### Production-Ready Structure
The project is designed with enterprise-level architecture including:
- **Modular Application Design**: Clear separation between bot logic, business services, and data models
- **Infrastructure as Code**: Docker, Kubernetes, and CI/CD configurations included
- **Observability**: Built-in monitoring with Prometheus and Grafana
- **Comprehensive Testing**: Unit, integration, and end-to-end test suites ready for development
- **Content Management**: Structured data organization for Japanese learning materials
- **Code Quality**: Black formatting and flake8 linting integrated

### Key Technologies
- **python-telegram-bot v22.2** - Telegram Bot API wrapper
- **SQLAlchemy 2.0.35** - Database ORM with async support
- **SQLite/PostgreSQL** - Database (configurable via DATABASE_URL)
- **aiosqlite 0.20.0** - Async SQLite operations
- **Pydantic 2.12.0a1** - Data validation and serialization
- **pytest 8.4.2** - Testing framework with async support
- **Black 25.1.0** - Code formatter
- **Redis** - Caching and session management (optional)
- **Spaced Repetition Algorithm** - Modified SM-2 for learning optimization

### Configuration
Environment variables are configured via `.env` file (copy from `.env.example`):
- `BOT_TOKEN` - Telegram bot token from @BotFather
- `DATABASE_URL` - Database connection string
- Learning system settings (lesson sizes, intervals, thresholds)
- Feature flags for various bot capabilities

### Learning System
The bot implements a structured progression:
1. Hiragana Basics (46 characters)  
2. Katakana Mastery (46 characters)
3. Basic Kanji (100+ common characters)
4. Vocabulary Building

Uses spaced repetition with SM-2 algorithm that tracks individual character difficulty and adjusts review intervals based on user performance.

## Current Implementation Status

### Implemented Components
- ✅ **Core Application Structure**: Main app modules, handlers, services, models
- ✅ **Virtual Environment**: Python 3.12.3 with all dependencies installed
- ✅ **Testing Infrastructure**: pytest, coverage, and async testing setup complete
- ✅ **Code Quality**: Black formatting applied to all 16 Python files
- ✅ **Dependency Management**: All core dependencies resolved and installed
- ✅ **Project Structure**: Complete directory structure with placeholder files

### Ready for Development
- 📝 **Test Cases**: Test directory structure ready, no test cases written yet
- 📝 **Content Data**: Data directories created, awaiting learning content
- 📝 **Bot Logic**: Handler frameworks in place, business logic to be implemented
- 📝 **Database Schema**: Models defined, database initialization available

## Complete Project Structure

The project follows a production-ready architecture with clear separation of concerns:

### Root Directory Structure
```
japanese_learning_bot/
├── app/                        # Main application code
├── data/                       # Content and media files
├── tests/                      # All test files
├── deployment/                 # Deployment configurations
├── monitoring/                 # Monitoring and observability
├── docs/                       # Documentation
├── .github/                    # GitHub Actions workflows
├── requirements/               # Python dependencies
├── venv/                       # Virtual environment (active)
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── .dockerignore              # Docker ignore rules
├── Makefile                   # Build and deployment commands
├── pyproject.toml             # Python project configuration
└── README.md                  # Project documentation
```

### Detailed Application Structure

**app/** - Main Application Code:
```
app/
├── main.py                    # Application entry point
├── bot/                       # Telegram bot logic
│   ├── handlers/              # Message and command handlers
│   │   ├── start.py           # Welcome and onboarding [implemented]
│   │   ├── lesson.py          # Lesson management [placeholder]
│   │   ├── quiz.py            # Quiz functionality [placeholder]
│   │   ├── progress.py        # Progress tracking [placeholder]
│   │   └── settings.py        # User preferences [placeholder]
│   ├── keyboards/             # Inline keyboard definitions
│   │   └── main_menu.py       # Main menu keyboards [implemented]
│   ├── states.py              # Conversation states [implemented]
│   └── middleware/            # Custom middleware [placeholder]
├── core/                      # Core system components
│   ├── config.py              # Configuration management [implemented]
│   ├── database.py            # Database connection and models [implemented]
│   ├── cache.py               # Redis caching layer [placeholder]
│   └── exceptions.py          # Custom exceptions [placeholder]
├── services/                  # Business logic layer
│   ├── lesson_service.py      # Lesson logic and content delivery [implemented]
│   ├── progress_service.py    # Progress tracking and analytics [placeholder]
│   ├── reminder_service.py    # Reminder scheduling [placeholder]
│   ├── analytics_service.py   # User analytics and metrics [placeholder]
│   └── content_service.py     # Content management [placeholder]
├── models/                    # Data models
│   ├── user.py                # User data models [implemented]
│   ├── lesson.py              # Lesson and content models [implemented]
│   ├── progress.py            # Progress tracking models [implemented]
│   └── analytics.py           # Analytics data models [placeholder]
└── utils/                     # Utility functions
    ├── spaced_repetition.py   # Spaced repetition algorithm [placeholder]
    ├── validators.py          # Input validation [placeholder]
    ├── formatters.py          # Data formatting [placeholder]
    └── helpers.py             # General helper functions [placeholder]
```

**tests/** - Testing Infrastructure Ready:
```
tests/
├── unit/                      # Unit tests [empty, ready for development]
│   ├── test_services/         # Service layer tests
│   ├── test_models/           # Model tests
│   └── test_utils/            # Utility function tests
├── integration/               # Integration tests [empty, ready for development]
│   ├── test_bot_handlers/     # Bot handler tests
│   └── test_database/         # Database integration tests
├── e2e/                       # End-to-end tests [empty, ready for development]
│   └── test_user_flows/       # Complete user journey tests
└── conftest.py                # Pytest configuration [to be created]
```

**data/** - Content and Media Files:
```
data/
├── content/                   # Learning content [directories created]
│   ├── hiragana/
│   │   ├── basic.json         # Basic hiragana characters [to be created]
│   │   ├── combinations.json  # Character combinations [to be created]
│   │   └── advanced.json      # Advanced patterns [to be created]
│   ├── katakana/              # Katakana content files [to be created]
│   ├── vocabulary/            # Vocabulary lessons [to be created]
│   └── cultural_notes/        # Cultural context [to be created]
├── audio/                     # Pronunciation files [to be created]
├── images/                    # Visual aids and mnemonics [to be created]
└── migrations/                # Database migration files [to be created]
```

### Production Infrastructure

**deployment/** - Deployment Configuration:
```
deployment/
├── docker/                    # Docker configurations [created]
│   ├── Dockerfile             # Application container [to be created]
│   ├── docker-compose.yml     # Local development [to be created]
│   └── docker-compose.prod.yml # Production setup [to be created]
├── kubernetes/                # Kubernetes manifests [created]
│   ├── namespace.yaml         # K8s namespace [to be created]
│   ├── deployment.yaml        # Application deployment [to be created]
│   ├── service.yaml           # Service definition [to be created]
│   └── ingress.yaml           # Ingress configuration [to be created]
└── scripts/                   # Deployment scripts [created]
    ├── deploy.sh              # Deployment automation [to be created]
    ├── backup.sh              # Database backup [to be created]
    └── migrate.sh             # Migration runner [to be created]
```

**monitoring/** - Observability Stack:
```
monitoring/
├── prometheus/                # Metrics collection [created]
│   └── config.yml             # Prometheus configuration [to be created]
├── grafana/                   # Visualization [created]
│   └── dashboards/            # Pre-built dashboards [to be created]
└── alerts/                    # Alerting rules [created]
    └── rules.yml              # Alert definitions [to be created]
```

## Development Workflow

### Before ANY File Creation or Modification:

1. **Activate Environment**: Always run `source venv/bin/activate` first
2. **Understand Context**: Review related files and their current implementation
3. **Follow Architecture**: Ensure code aligns with the established project structure
4. **Maintain Consistency**: Follow established patterns and naming conventions
5. **Layer Appropriately**: Place code in the correct architectural layer (handlers, services, models, utils)

### Code Creation Guidelines:

1. **Follow Layer Separation**:
   - **Handlers** (`app/bot/handlers/`) - Telegram bot interaction logic
   - **Services** (`app/services/`) - Business logic and orchestration
   - **Models** (`app/models/`) - Data structures and database entities
   - **Utils** (`app/utils/`) - Reusable utility functions
   - **Core** (`app/core/`) - System-wide infrastructure components

2. **Content Organization**:
   - Learning content in `data/content/` organized by subject
   - Media files in `data/audio/` and `data/images/`
   - Database migrations in `data/migrations/`

3. **Testing Strategy**:
   - Unit tests for individual components (directories ready)
   - Integration tests for system interactions (directories ready)
   - End-to-end tests for complete user flows (directories ready)

4. **Code Quality Workflow**:
   ```bash
   # Before committing any code:
   source venv/bin/activate
   black app/ tests/              # Auto-format code
   flake8 app/ tests/            # Check for style issues
   pytest --cov=app tests/       # Run tests with coverage
   python -c "import app"        # Verify imports work
   ```

## Key Implementation Principles

- **User Privacy**: Handle user data responsibly
- **Internationalization**: Support for different character sets (UTF-8)
- **Scalability**: Design for potential growth in user base
- **Maintenance**: Write maintainable, well-documented code
- **Performance**: Consider response times for interactive bot features
- **Production Ready**: Include monitoring, deployment, and CI/CD from the start
- **Testing**: Comprehensive test coverage across unit, integration, and e2e levels
- **Code Quality**: Consistent formatting with Black, style checking with flake8

## Specialized Agent Usage Guidelines

For optimal development, use these specialized agents for specific project areas:

### Core Development Agents

**python-pro** - Use for all Python development tasks:
- SQLAlchemy async patterns and database operations  
- python-telegram-bot v22.2 implementation
- Async/await patterns for bot handlers
- Type hints and modern Python features
- General Python code optimization and refactoring
- Black formatting and flake8 compliance

**database-optimizer** - Use for database-related work:
- SQLite/PostgreSQL schema optimization
- Spaced repetition algorithm data queries
- User progress tracking queries  
- Performance optimization for character/vocabulary lookups
- Database migration strategies
- SQLAlchemy 2.0.35 async patterns

**backend-architect** - Use for system architecture:
- Bot handler architecture and routing
- Service layer organization
- Database schema design
- API structure for learning progression
- Overall system design decisions

### Specialized Learning System Agents

**ai-engineer** - Use for intelligent learning features:
- SM-2 algorithm implementation and optimization
- Learning analytics and progress tracking
- Adaptive difficulty algorithms
- User performance pattern analysis
- Machine learning integration for personalized learning

**ml-engineer** - Use for production ML deployment:
- Model serving for learning recommendations
- A/B testing for learning algorithms  
- Feature engineering for user progress
- ML pipeline integration

### Quality Assurance Agents

**test-automator** - Use for comprehensive testing:
- Unit tests for learning algorithms
- Integration tests for Telegram bot flows
- Coverage optimization (pytest --cov setup already completed)
- Mock strategies for Telegram API interactions
- Test data generation for Japanese content
- Pytest async testing patterns

**code-reviewer** - Use after implementing features:
- Code quality and Python best practices
- Security review for user data handling
- Performance optimization suggestions
- Architecture consistency checks
- Black formatting compliance
- Type hint validation

**performance-engineer** - Use for optimization:
- Database query optimization
- Redis caching strategies
- Telegram API rate limiting
- Response time optimization for interactive features
- Memory usage optimization
- SQLAlchemy async performance tuning

### Content & Data Management Agents

**data-engineer** - Use for Japanese learning content:
- JSON data pipeline for hiragana/katakana/kanji
- Content validation and processing
- Learning progression data management
- ETL processes for learning analytics

**data-scientist** - Use for learning analytics:
- User progress analysis
- Learning effectiveness metrics
- Spaced repetition optimization through data analysis
- A/B testing statistical analysis

### DevOps & Infrastructure Agents

**deployment-engineer** - Use for bot deployment:
- Docker containerization for the bot
- CI/CD pipeline setup
- Production deployment strategies
- Environment configuration management

**security-auditor** - Use for security reviews:
- User data protection implementation
- Telegram bot security best practices
- Environment variable security
- Input validation and sanitization

### Usage Triggers

**Automatic Agent Selection**: Claude Code will proactively use these agents when:
- Working on database queries → **database-optimizer**
- Implementing learning algorithms → **ai-engineer**  
- Writing Python code → **python-pro**
- After completing features → **code-reviewer**
- Setting up tests → **test-automator**
- Optimizing performance → **performance-engineer**
- Working with Japanese content data → **data-engineer**
- Deployment tasks → **deployment-engineer**
- Security-related code → **security-auditor**
- Code formatting issues → **python-pro** with Black
- Testing infrastructure → **test-automator**

This ensures the most specialized expertise is applied to each aspect of the Japanese Learning Telegram Bot development.

## Project Status Summary

**Current State**: Development-ready with complete infrastructure setup
**Next Steps**: Implement business logic, create test cases, add learning content
**Dependencies**: All installed and verified (requirements.txt with Pydantic 2.12.0a1)
**Testing**: Infrastructure complete, ready for test case development
**Code Quality**: Black formatting applied, flake8 compliance in progress
**Virtual Environment**: Active with Python 3.12.3

The project is well-structured and ready for feature development with comprehensive tooling support.
