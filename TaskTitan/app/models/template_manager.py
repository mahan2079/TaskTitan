"""
Template Manager for TaskTitan

Provides the ability to save, list, apply and manage reusable habit systems
as named templates. Applying a template will replace the user's current set of
habits in the unified `activities` table so that all views (Activities,
Weekly Plan, etc.) immediately reflect the chosen habit system.
"""

from __future__ import annotations

from typing import List, Dict, Optional, Tuple
from PyQt6.QtCore import QDate, QTime


class TemplateManager:
    """Manager for habit templates persisted in the same SQLite database.

    Tables
    ------
    - habit_templates(id, name, description, created_at, updated_at)
    - habit_template_items(id, template_id, title, start_time, end_time,
      days_of_week, category, priority, color)
    - app_settings(key PRIMARY KEY, value)
    """

    def __init__(self, conn, cursor):
        self.conn = conn
        self.cursor = cursor

    # ---------- Schema ----------
    def create_tables(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS habit_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS habit_template_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                days_of_week TEXT NOT NULL,
                category TEXT,
                priority INTEGER DEFAULT 0,
                color TEXT,
                FOREIGN KEY (template_id) REFERENCES habit_templates(id) ON DELETE CASCADE
            )
            """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )

        # trigger for updated_at
        self.cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS update_habit_template_ts
            AFTER UPDATE ON habit_templates
            BEGIN
                UPDATE habit_templates SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END;
            """
        )

        self.conn.commit()

    # ---------- Helpers ----------
    def _get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        self.cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
        row = self.cursor.fetchone()
        return row[0] if row else default

    def _set_setting(self, key: str, value: str) -> None:
        self.cursor.execute(
            "INSERT INTO app_settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        self.conn.commit()

    # ---------- Public API ----------
    def list_templates(self) -> List[Tuple[int, str]]:
        self.cursor.execute("SELECT id, name FROM habit_templates ORDER BY name")
        return list(self.cursor.fetchall())

    def get_active_template_id(self) -> Optional[int]:
        val = self._get_setting("active_template_id")
        try:
            return int(val) if val is not None else None
        except Exception:
            return None

    def set_active_template(self, template_id: int, replace_existing: bool = True) -> None:
        """Set and apply an active template, replacing current habits by default."""
        self.apply_template(template_id, replace_existing=replace_existing)
        self._set_setting("active_template_id", str(template_id))

    def save_template_from_current_habits(self, name: str, description: str = "", overwrite: bool = False) -> int:
        """Create or overwrite a template capturing all current habits.

        Habits are rows in `activities` with type='habit' and non-empty days_of_week.
        """
        # Create or fetch template id
        if overwrite:
            existing = self._get_template_id_by_name(name)
            if existing:
                template_id = existing
                self.cursor.execute("DELETE FROM habit_template_items WHERE template_id = ?", (template_id,))
                self.cursor.execute("UPDATE habit_templates SET description = ? WHERE id = ?", (description, template_id))
            else:
                self.cursor.execute(
                    "INSERT INTO habit_templates(name, description) VALUES (?, ?)",
                    (name, description),
                )
                template_id = self.cursor.lastrowid
        else:
            self.cursor.execute(
                "INSERT OR IGNORE INTO habit_templates(name, description) VALUES (?, ?)",
                (name, description),
            )
            # If name existed, fetch id; else use lastrowid
            template_id = self._get_template_id_by_name(name)
            if not template_id:
                template_id = self.cursor.lastrowid

        # Pull habits from activities
        self.cursor.execute(
            """
            SELECT title, start_time, end_time, COALESCE(days_of_week, ''), COALESCE(category, ''), COALESCE(priority, 0), COALESCE(color, '')
            FROM activities
            WHERE type = 'habit'
            """
        )
        items = self.cursor.fetchall()

        for title, start_time, end_time, days_of_week, category, priority, color in items:
            start_s = self._ensure_time_string(start_time)
            end_s = self._ensure_time_string(end_time)
            self.cursor.execute(
                """
                INSERT INTO habit_template_items(template_id, title, start_time, end_time, days_of_week, category, priority, color)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (template_id, title, start_s, end_s, days_of_week, category, priority, color),
            )

        self.conn.commit()
        return int(template_id)

    def overwrite_template_from_current_habits(self, template_id: int) -> None:
        """Overwrite a template with the user's current habit set."""
        self.cursor.execute("DELETE FROM habit_template_items WHERE template_id = ?", (template_id,))
        self.conn.commit()
        # Reuse save flow by name
        self.cursor.execute("SELECT name, COALESCE(description, '') FROM habit_templates WHERE id = ?", (template_id,))
        row = self.cursor.fetchone()
        if not row:
            return
        self.save_template_from_current_habits(row[0], description=row[1], overwrite=True)

    def delete_template(self, template_id: int) -> None:
        self.cursor.execute("DELETE FROM habit_templates WHERE id = ?", (template_id,))
        self.conn.commit()

    def rename_template(self, template_id: int, new_name: str) -> None:
        self.cursor.execute("UPDATE habit_templates SET name = ? WHERE id = ?", (new_name, template_id))
        self.conn.commit()

    def apply_template(self, template_id: int, replace_existing: bool = True) -> None:
        """Apply a template to the activities table.

        If `replace_existing` is True, all current habits in `activities` are removed
        before the template is applied. This makes the template the live habit system.
        """
        if replace_existing:
            self.cursor.execute("DELETE FROM activities WHERE type = 'habit'")

        # Use a stable placeholder date (not used for habits fetching)
        placeholder_date = "1970-01-01"

        self.cursor.execute(
            """
            SELECT title, start_time, end_time, days_of_week, COALESCE(category, ''), COALESCE(priority, 0), COALESCE(color, '')
            FROM habit_template_items WHERE template_id = ?
            """,
            (template_id,),
        )

        rows = self.cursor.fetchall()
        for title, start_time, end_time, days_of_week, category, priority, color in rows:
            start_s = self._ensure_time_string(start_time)
            end_s = self._ensure_time_string(end_time)
            self.cursor.execute(
                """
                INSERT INTO activities (
                    title, date, start_time, end_time, completed, type,
                    priority, category, days_of_week, goal_id, color
                ) VALUES (?, ?, ?, ?, 0, 'habit', ?, ?, ?, NULL, ?)
                """,
                (title, placeholder_date, start_s, end_s, priority, category, days_of_week, color),
            )

        self.conn.commit()

    # ---------- Internal ----------
    def _get_template_id_by_name(self, name: str) -> Optional[int]:
        self.cursor.execute("SELECT id FROM habit_templates WHERE name = ?", (name,))
        row = self.cursor.fetchone()
        return int(row[0]) if row else None

    @staticmethod
    def _ensure_time_string(value) -> str:
        if isinstance(value, QTime):
            return value.toString("HH:mm")
        try:
            # Already like 'HH:MM'
            s = str(value)
            return s if ":" in s else "00:00"
        except Exception:
            return "00:00"


