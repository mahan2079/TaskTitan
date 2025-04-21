import os
import sqlite3
from pathlib import Path

def clean_activities_database():
    """Remove all activities from the database."""
    # Get database path
    app_data_dir = os.path.join(str(Path.home()), '.tasktitan')
    db_path = os.path.join(app_data_dir, 'tasktitan.db')
    
    print(f"Using database at: {db_path}")
    
    if not os.path.exists(db_path):
        print("Database file doesn't exist. Please run the application first.")
        return
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if activities table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activities'")
    if not cursor.fetchone():
        print("Activities table doesn't exist. Please run the application first.")
        conn.close()
        return
    
    # Count current activities
    cursor.execute("SELECT COUNT(*) FROM activities")
    count = cursor.fetchone()[0]
    print(f"Found {count} activities in the database.")
    
    # Delete all activities
    try:
        cursor.execute("DELETE FROM activities")
        conn.commit()
        print("All activities have been removed from the database.")
    except sqlite3.Error as e:
        print(f"Error deleting activities: {e}")
    
    # Verify deletion
    cursor.execute("SELECT COUNT(*) FROM activities")
    count = cursor.fetchone()[0]
    print(f"Activities after cleanup: {count}")
    
    # Close connection
    conn.close()
    
    print("\nCleanup complete! The next time you run TaskTitan, no default activities will appear.")
    print("Only activities that you explicitly create will be shown.")

if __name__ == "__main__":
    print("TaskTitan Activity Cleanup Tool")
    print("-------------------------------")
    choice = input("This will remove ALL activities from your TaskTitan database. Continue? (y/n): ")
    
    if choice.lower() == 'y':
        clean_activities_database()
    else:
        print("Operation cancelled.") 