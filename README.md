# 🇯🇵 Japanese Learning Telegram Bot

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-6.0+-blue.svg)](https://core.telegram.org/bots/api)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

An interactive Telegram bot designed to make learning Japanese engaging and effective through daily practice, spaced repetition, and personalized study schedules.

## ✨ Features

### 🎯 Core Learning System
- **Progressive Lessons**: Structured learning path from hiragana to basic kanji
- **Spaced Repetition**: SM-2 algorithm ensures optimal review timing
- **Daily Practice**: Customizable study reminders and bite-sized lessons
- **Progress Tracking**: Detailed analytics and learning statistics

### 🎮 Interactive Elements
- **Flashcard System**: Visual character recognition and pronunciation practice
- **Quiz Modes**: Multiple choice, typing exercises, and audio challenges
- **Voice Support**: Pronunciation feedback and audio examples
- **Adaptive Difficulty**: Content adjusts based on user performance

### 📊 Smart Features
- **Streak Tracking**: Maintain daily study habits with motivation
- **Personal Dashboard**: Track progress across different character sets
- **Custom Reminders**: Set study times that fit your schedule
- **Multi-format Practice**: Text, audio, and visual learning modes

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- PostgreSQL database (optional, SQLite used by default)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/japanese-learning-telegram-bot.git
   cd japanese-learning-telegram-bot
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your bot token and configuration
   ```

5. **Initialize database**
   ```bash
   python -m app.core.database init
   ```

6. **Run the bot**
   ```bash
   python main.py
   ```

## 📱 Bot Commands

### Getting Started
- `/start` - Begin your Japanese learning journey
- `/help` - Show available commands and features
- `/tutorial` - Interactive tutorial for new users

### Learning Commands
- `/lesson` - Start a new lesson or continue current progress
- `/quiz` - Take a quick quiz on recent content
- `/review` - Review items marked for practice
- `/flashcards` - Practice with interactive flashcards

### Progress & Settings
- `/progress` - View detailed learning statistics
- `/streak` - Check your current study streak
- `/settings` - Customize reminders and preferences
- `/remind` - Set up daily study reminders

### Study Tools
- `/random` - Get a random character to practice
- `/search [term]` - Look up Japanese characters or words
- `/pronunciation [text]` - Get audio pronunciation guide

## 🏗️ Architecture

### Project Structure
```
japanese-learning-bot/
├── app/
│   ├── bot/                    # Telegram bot handlers
│   │   ├── handlers/          # Command and message handlers
│   │   ├── keyboards/         # Inline keyboards and menus
│   │   └── middleware/        # Bot middleware components
│   ├── core/                  # Core application logic
│   │   ├── config.py         # Configuration management
│   │   ├── database.py       # Database operations
│   │   └── spaced_repetition.py # Learning algorithms
│   ├── models/               # Data models
│   ├── services/             # Business logic services
│   └── utils/                # Utility functions
├── data/
│   ├── content/              # Learning content (hiragana, katakana, kanji)
│   ├── audio/                # Pronunciation audio files
│   └── images/               # Visual learning materials
├── tests/                    # Test suite
├── requirements.txt          # Python dependencies
└── main.py                   # Application entry point
```

### Key Technologies
- **[python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)** - Telegram Bot API wrapper
- **SQLAlchemy** - Database ORM with async support
- **Redis** - Caching and session management
- **Celery** - Background task processing for reminders
- **Pydantic** - Data validation and settings management

## 🎓 Learning System

### Content Progression
1. **Hiragana Basics** (46 characters)
   - Recognition and pronunciation
   - Stroke order and writing practice
   - Common word combinations

2. **Katakana Mastery** (46 characters)
   - Foreign word adaptation
   - Usage context and examples
   - Comparison with hiragana

3. **Basic Kanji** (100+ common characters)
   - Meaning and readings (kun/on)
   - Stroke order and radicals
   - Vocabulary building

4. **Vocabulary Building**
   - Essential daily words
   - Thematic word groups
   - Grammar integration

### Spaced Repetition Algorithm
Uses a modified SM-2 algorithm that:
- Tracks individual character/word difficulty
- Adjusts review intervals based on accuracy
- Considers response time for difficulty assessment
- Provides optimal review scheduling

## 📊 Features in Detail

### 🎯 Adaptive Learning
The bot analyzes your performance to:
- Identify challenging characters that need more practice
- Adjust lesson difficulty in real-time
- Suggest optimal study session lengths
- Recommend focus areas for improvement

### 📱 Mobile-Optimized Experience
- Clean, intuitive interface designed for mobile use
- Quick-access buttons for common actions
- Minimal typing required for most interactions
- Works seamlessly on all Telegram platforms

### 🔄 Data Persistence
- Progress saved automatically across sessions
- Sync between multiple devices via Telegram
- Export learning data for external analysis
- Backup and restore functionality

## 🛠️ Development

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
```

### Code Quality
```bash
# Format code
black app/ tests/

# Lint code
flake8 app/ tests/

# Type checking
mypy app/
```

### Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📈 Usage Analytics

The bot tracks anonymous usage metrics to improve the learning experience:
- Lesson completion rates
- Common mistake patterns
- Feature usage statistics
- Performance optimization data

*All data is anonymized and used solely for improving the educational experience.*

## 🔒 Privacy & Security

- **No Personal Data Storage**: Only learning progress is stored
- **Secure Token Management**: Environment-based configuration
- **Rate Limiting**: Protection against spam and abuse
- **Data Encryption**: Sensitive data encrypted at rest

## 🌍 Internationalization

Currently supports:
- **English** - Primary interface language
- **Japanese** - Learning content and examples
- **Romaji** - Pronunciation guides

*Additional interface languages planned for future releases.*

## 📋 Roadmap

### Phase 1: Core Features ✅
- [x] Basic hiragana/katakana lessons
- [x] Spaced repetition system
- [x] Progress tracking
- [x] Daily reminders

### Phase 2: Enhanced Learning 🚧
- [ ] Voice recognition for pronunciation
- [ ] Image-based character recognition
- [ ] Grammar pattern introduction
- [ ] Cultural context lessons

### Phase 3: Advanced Features 📋
- [ ] JLPT preparation mode
- [ ] Study group functionality
- [ ] Leaderboards and challenges
- [ ] AI-powered conversation practice

### Phase 4: Platform Expansion 🔮
- [ ] Web dashboard companion
- [ ] Mobile app version
- [ ] Integration with other learning platforms
- [ ] API for third-party developers

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Areas needing help:
- **Content Creation**: Additional learning materials and exercises
- **Translations**: Interface localization for different languages
- **Testing**: User experience testing and bug reports
- **Documentation**: Tutorials and user guides

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Japanese Language Resources**: Thanks to the open-source Japanese learning community
- **Telegram Bot Community**: For excellent documentation and support
- **Beta Testers**: Users who provided valuable feedback during development

## 📞 Support

- **Documentation**: [Project Wiki](https://github.com/yourusername/japanese-learning-bot/wiki)
- **Bug Reports**: [GitHub Issues](https://github.com/yourusername/japanese-learning-bot/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/yourusername/japanese-learning-bot/discussions)
- **Community**: [Telegram Support Group](https://t.me/japanese_learning_bot_support)

## 📊 Statistics

![GitHub stars](https://img.shields.io/github/stars/yourusername/japanese-learning-bot)
![GitHub forks](https://img.shields.io/github/forks/yourusername/japanese-learning-bot)
![GitHub issues](https://img.shields.io/github/issues/yourusername/japanese-learning-bot)
![GitHub last commit](https://img.shields.io/github/last-commit/yourusername/japanese-learning-bot)

---

<div align="center">
  <h3>🌸 Made with ❤️ for Japanese learners worldwide 🌸</h3>
  <p><strong>頑張って！(Good luck with your studies!)</strong></p>
</div>
