# TaskTitan User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Features](#features)
3. [Keyboard Shortcuts](#keyboard-shortcuts)
4. [Troubleshooting](#troubleshooting)

## Getting Started

### Installation

1. Download TaskTitan for your operating system
2. Run the installer
3. Launch TaskTitan from your applications menu

### First Launch

On first launch, TaskTitan will:
- Create necessary data directories
- Initialize the database
- Set up default settings

## Features

### Dashboard

The dashboard provides an overview of your tasks, goals, and productivity.

### Activities

Manage tasks, events, and habits in one unified view:
- **Tasks**: One-time or recurring tasks
- **Events**: Scheduled events with specific times
- **Habits**: Daily routines and habits

### Goals

Create and track hierarchical goals:
- Set due dates and priorities
- Organize goals with parent-child relationships
- Track progress

### Daily Tracker

Track your daily activities:
- Time entries
- Energy and mood tracking
- Journal entries
- Analytics and reports

### Pomodoro Timer

Use the Pomodoro Technique for focused work:
- Customizable work and break durations
- Session tracking
- Distraction tracking

### Weekly Planner

Plan your week with:
- Weekly task overview
- Time blocking
- Weekly goals

## Keyboard Shortcuts

### Navigation
- `Ctrl+B`: Toggle Sidebar
- `Ctrl+K`: Focus Search
- `Esc`: Close Dialog/Cancel

### Views
- `Ctrl+1`: Dashboard
- `Ctrl+2`: Activities
- `Ctrl+3`: Goals
- `Ctrl+4`: Daily Tracker
- `Ctrl+5`: Pomodoro
- `Ctrl+6`: Weekly Plan
- `Ctrl+,`: Settings

### Editing
- `Ctrl+S`: Save
- `Ctrl+Z`: Undo
- `Ctrl+Y`: Redo
- `Ctrl+C`: Copy
- `Ctrl+V`: Paste
- `Ctrl+X`: Cut
- `Delete`: Delete Selected

### Pomodoro
- `Space`: Start/Pause Timer
- `R`: Reset Timer
- `S`: Skip Break

See the keyboard shortcuts dialog (`Help > Keyboard Shortcuts`) for complete list.

## Settings

Access settings via `Ctrl+,` or `Help > Settings`.

### Appearance
- Theme selection (Light, Dark, System)
- Font size and family
- Window size and position

### Backup
- Enable automatic backups
- Set backup interval (daily/weekly/monthly)
- Configure retention policy

### Notifications
- Enable/disable notifications
- Task reminders
- Deadline alerts
- Backup notifications

### Updates
- Check for updates automatically
- Update check interval

## Data Management

### Backup

Manual backup:
1. Go to `File > Backup Data`
2. Choose location
3. Backup will be created

Automatic backups:
- Enable in Settings
- Choose interval
- Backups stored in `data/backups/`

### Restore

1. Go to `File > Restore Data`
2. Select backup file
3. Confirm restore

### Export/Import

Export data:
1. Go to `File > Export`
2. Choose format (JSON/CSV)
3. Select items to export
4. Save file

Import data:
1. Go to `File > Import`
2. Select file
3. Confirm import

## Troubleshooting

### Application Won't Start

1. Check logs in `data/logs/tasktitan.log`
2. Ensure Python 3.8+ is installed
3. Reinstall dependencies: `pip install -r requirements.txt`

### Database Errors

1. Check disk space
2. Verify database file permissions
3. Use `File > Restore Data` to restore from backup

### Performance Issues

1. Reduce cache size in Settings
2. Disable lazy loading if enabled
3. Check for large attachments

### Missing Data

1. Check if database file exists: `data/tasktitan.db`
2. Restore from backup if available
3. Check logs for errors

## Tips

### Productivity Tips

1. Use categories to organize activities
2. Set up recurring habits for routines
3. Use Pomodoro timer for focused work
4. Review weekly planner every Sunday

### Keyboard Shortcuts

Learn keyboard shortcuts to work faster:
- Use `Ctrl+K` for quick search
- Use `Ctrl+1-6` to switch views quickly
- Use `Esc` to close dialogs

### Data Organization

1. Use tags for flexible categorization
2. Set priorities for important tasks
3. Use goals to track long-term objectives
4. Regular backups ensure data safety

## Support

For issues or questions:
- Check logs: `data/logs/tasktitan.log`
- Review this guide
- Check GitHub Issues
- Contact: mahan.dashiti.gohari@gmail.com

