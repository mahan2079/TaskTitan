# TaskTitan

<img src="Logo.png" alt="TaskTitan Logo" width="300">

TaskTitan is a feature-rich and modern task management application designed to help users organize their goals, habits, routines, and productivity sessions effectively. With a sleek interface, advanced features, and customization options, TaskTitan ensures a seamless experience for planning and managing your time.

## Features

### Core Features

- **Goal Management**: 
  - Add, edit, delete, and organize hierarchical goals
  - Set due dates, priorities, and tags
  - Track progress visually

- **Activity Management**:
  - Unified system for tasks, events, and habits
  - Daily, weekly, and recurring activities
  - Categories and priorities

- **Habit Tracking**: 
  - Create recurring habits with time and day specifications
  - Integrated habit progress into the daily planner
  - Streak tracking

- **Daily Planner**: 
  - Populate tasks, habits, routines, and goals for each day
  - Integrated calendar view for efficient planning
  - Time blocking

- **Pomodoro Timer**: 
  - Focus timer with customizable work and break intervals
  - Distraction tracking for improved productivity insights
  - Session history

- **Productivity Tracking**:
  - Daily time tracking
  - Energy and mood logging
  - Journal entries
  - Analytics and reports

### Advanced Features

- **Auto-Backup**: Scheduled automatic backups with retention policies
- **Data Validation**: Integrity checks and recovery mechanisms
- **Update Notifications**: Automatic update checking
- **System Notifications**: Reminders and alerts
- **Keyboard Shortcuts**: Comprehensive shortcut system
- **Search**: Powerful search across all data
- **Themes**: Multiple themes with dark/light modes

### Customization

- **Color Themes**: Elegant dark mode with customizable colors
- **Customizable Goals and Events**: Attach files, assign tags, and organize by priority
- **Export and Import**: JSON and CSV formats
- **Visualization**: Charts and visual breakdowns

## Installation

### From Source

1. Clone the repository:
```bash
git clone https://github.com/mahan2079/TaskTitan.git
cd TaskTitan
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python TaskTitan/run.py
```

### Building Executable

See [BUILD.md](TaskTitan/BUILD.md) for detailed instructions.

```bash
pip install pyinstaller
pyinstaller tasktitan.spec
```

## Requirements

- Python 3.8 or later
- PyQt6
- Matplotlib
- SQLite3
- darkdetect
- qasync
- pyqtgraph

See `requirements.txt` for complete list.

## Documentation

- [User Guide](TaskTitan/docs/USER_GUIDE.md) - Complete user manual
- [Developer Guide](TaskTitan/docs/DEVELOPMENT.md) - Setup and contribution guide
- [API Documentation](TaskTitan/docs/API.md) - API reference
- [Architecture](TaskTitan/docs/ARCHITECTURE.md) - System architecture overview

## Usage

### Quick Start

1. Launch TaskTitan
2. Create your first goal or activity
3. Set up daily habits
4. Use the Pomodoro timer for focused work
5. Track your productivity in the Daily Tracker

### Keyboard Shortcuts

- `Ctrl+K`: Search
- `Ctrl+1-6`: Switch views
- `Ctrl+,`: Settings
- `Ctrl+B`: Toggle sidebar

See [User Guide](TaskTitan/docs/USER_GUIDE.md) for complete list.

## Data Management

### Backup

- Manual: `File > Backup Data`
- Automatic: Configure in Settings
- Location: `data/backups/`

### Restore

- `File > Restore Data`
- Select backup file
- Confirm restore

### Export/Import

- Export: `File > Export` (JSON/CSV)
- Import: `File > Import`

## Configuration

Configuration is stored in `data/config.json`. Key settings:

- Window preferences
- Theme selection
- Backup settings
- Notification preferences
- Performance options

## Troubleshooting

### Common Issues

1. **Application won't start**:
   - Check logs: `data/logs/tasktitan.log`
   - Verify Python version: `python --version`
   - Reinstall dependencies

2. **Database errors**:
   - Check disk space
   - Verify file permissions
   - Restore from backup

3. **Performance issues**:
   - Reduce cache size in Settings
   - Check for large attachments
   - Disable unnecessary features

See [User Guide](TaskTitan/docs/USER_GUIDE.md) for detailed troubleshooting.

## Contributing

We welcome contributions! See [Developer Guide](TaskTitan/docs/DEVELOPMENT.md) for:
- Setup instructions
- Code standards
- Testing guidelines
- Contribution process

## Testing

Run tests:
```bash
pytest tests/
```

With coverage:
```bash
pytest --cov=app --cov-report=html
```

## Code Quality

We use:
- Black for formatting
- Flake8 for linting
- mypy for type checking
- isort for import sorting

See [CODE_QUALITY.md](TaskTitan/CODE_QUALITY.md) for details.

## License

Copyright 2025 Mahan Dashti Gohari

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## Support

For help or feedback:
- Email: mahan.dashiti.gohari@gmail.com
- GitHub Issues: [Report Issues](https://github.com/mahan2079/TaskTitan/issues)

## Credits

Built with:
- PyQt6
- Matplotlib
- SQLite3
- Material Design Icons

## Changelog

### Version 1.0.0

- Initial production release
- Comprehensive error handling and logging
- Security features
- Testing infrastructure
- Documentation
- Performance optimizations
- Data reliability features
- Essential production features
