"""
Search Manager for TaskTitan.

Provides centralized search functionality across activities, goals, and categories.
"""
from typing import List, Dict, Any
from datetime import datetime


class SearchResult:
    """Represents a single search result."""
    
    def __init__(self, item_type: str, item_id: int, title: str, 
                 description: str = "", metadata: Dict[str, Any] = None):
        """
        Initialize a search result.
        
        Args:
            item_type: Type of item ('task', 'event', 'habit', 'goal', 'category')
            item_id: ID of the item
            title: Title/name of the item
            description: Optional description
            metadata: Additional metadata (date, priority, etc.)
        """
        self.item_type = item_type
        self.item_id = item_id
        self.title = title
        self.description = description
        self.metadata = metadata or {}
    
    def __repr__(self):
        return f"SearchResult(type={self.item_type}, id={self.item_id}, title={self.title})"


class SearchManager:
    """Manages search functionality across all content types."""
    
    def __init__(self, db_manager=None, activities_manager=None):
        """
        Initialize the search manager.
        
        Args:
            db_manager: Database manager instance
            activities_manager: Activities manager instance
        """
        self.db_manager = db_manager
        self.activities_manager = activities_manager
    
    def search(self, query: str, limit: int = 50) -> List[SearchResult]:
        """
        Search across all content types.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of SearchResult objects
        """
        if not query or len(query.strip()) < 2:
            return []
        
        query_lower = query.lower().strip()
        results = []
        
        # Search activities (tasks, events, habits)
        if self.activities_manager:
            results.extend(self._search_activities(query_lower, limit))
        
        # Search goals
        if self.db_manager:
            results.extend(self._search_goals(query_lower, limit))
        
        # Search categories
        if self.db_manager:
            results.extend(self._search_categories(query_lower, limit))
        
        # Sort by relevance (exact matches first, then partial matches)
        results.sort(key=lambda r: (
            0 if query_lower in r.title.lower() else 1,
            -len(r.title)  # Shorter titles first for exact matches
        ))
        
        return results[:limit]
    
    def _search_activities(self, query: str, limit: int) -> List[SearchResult]:
        """Search in activities (tasks, events, habits)."""
        results = []
        
        if not self.activities_manager:
            return results
        
        try:
            # Get all activities from database
            cursor = self.activities_manager.cursor
            if not cursor:
                return results
            
            # Search in activities table
            cursor.execute("""
                SELECT id, title, description, type, date, start_time, end_time, 
                       category, priority, completed
                FROM activities
                WHERE title LIKE ? OR description LIKE ?
                ORDER BY date DESC, priority DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit))
            
            activities = cursor.fetchall()
            
            for activity in activities:
                activity_id, title, description, activity_type, date, \
                start_time, end_time, category, priority, completed = activity
                
                # Format description
                desc_parts = []
                if date:
                    desc_parts.append(f"Date: {date}")
                if start_time and end_time:
                    desc_parts.append(f"Time: {start_time}-{end_time}")
                if category:
                    desc_parts.append(f"Category: {category}")
                
                formatted_desc = " • ".join(desc_parts) if desc_parts else description or ""
                
                result = SearchResult(
                    item_type=activity_type,
                    item_id=activity_id,
                    title=title,
                    description=formatted_desc,
                    metadata={
                        'date': date,
                        'start_time': start_time,
                        'end_time': end_time,
                        'category': category,
                        'priority': priority,
                        'completed': completed == 1
                    }
                )
                results.append(result)
        
        except Exception as e:
            print(f"Error searching activities: {e}")
        
        return results
    
    def _search_goals(self, query: str, limit: int) -> List[SearchResult]:
        """Search in goals."""
        results = []
        
        if not self.db_manager:
            return results
        
        try:
            cursor = self.db_manager.cursor
            if not cursor:
                return results
            
            # Search in goals table
            cursor.execute("""
                SELECT id, title, due_date, created_date, priority, completed, parent_id
                FROM goals
                WHERE title LIKE ?
                ORDER BY priority DESC, due_date ASC
                LIMIT ?
            """, (f"%{query}%", limit))
            
            goals = cursor.fetchall()
            
            for goal in goals:
                goal_id, title, due_date, created_date, priority, completed, parent_id = goal
                
                # Format description
                desc_parts = []
                if due_date:
                    desc_parts.append(f"Due: {due_date}")
                if parent_id:
                    desc_parts.append("Subgoal")
                else:
                    desc_parts.append("Parent goal")
                
                formatted_desc = " • ".join(desc_parts) if desc_parts else ""
                
                result = SearchResult(
                    item_type='goal',
                    item_id=goal_id,
                    title=title,
                    description=formatted_desc,
                    metadata={
                        'due_date': due_date,
                        'created_date': created_date,
                        'priority': priority,
                        'completed': completed == 1,
                        'parent_id': parent_id
                    }
                )
                results.append(result)
        
        except Exception as e:
            print(f"Error searching goals: {e}")
        
        return results
    
    def _search_categories(self, query: str, limit: int) -> List[SearchResult]:
        """Search in categories."""
        results = []
        
        if not self.db_manager:
            return results
        
        try:
            cursor = self.db_manager.cursor
            if not cursor:
                return results
            
            # Search in categories table (if it exists)
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='categories'
            """)
            
            if not cursor.fetchone():
                return results  # Categories table doesn't exist
            
            cursor.execute("""
                SELECT id, name, color
                FROM categories
                WHERE name LIKE ?
                LIMIT ?
            """, (f"%{query}%", limit))
            
            categories = cursor.fetchall()
            
            for category in categories:
                cat_id, name, color = category
                
                result = SearchResult(
                    item_type='category',
                    item_id=cat_id,
                    title=name,
                    description=f"Category • Color: {color}" if color else "Category",
                    metadata={'color': color}
                )
                results.append(result)
        
        except Exception as e:
            print(f"Error searching categories: {e}")
        
        return results
    
    def highlight_match(self, text: str, query: str) -> str:
        """
        Highlight matching text in search results.
        
        Args:
            text: Text to highlight
            query: Search query
            
        Returns:
            HTML-formatted string with highlighted matches
        """
        if not query or not text:
            return text
        
        query_lower = query.lower()
        text_lower = text.lower()
        
        if query_lower not in text_lower:
            return text
        
        # Find all occurrences (case-insensitive)
        start_idx = 0
        highlighted = []
        query_len = len(query)
        
        while True:
            idx = text_lower.find(query_lower, start_idx)
            if idx == -1:
                break
            
            # Add text before match
            highlighted.append(text[start_idx:idx])
            
            # Add highlighted match
            highlighted.append(f"<b>{text[idx:idx+query_len]}</b>")
            
            start_idx = idx + query_len
        
        # Add remaining text
        highlighted.append(text[start_idx:])
        
        return "".join(highlighted)

