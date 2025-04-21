import os
import sqlite3
from pathlib import Path

def clear_and_check_activities():
    """Clear activities from database and check if defaults get added."""
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
    
    # Check current activities
    print("Current activities in database:")
    cursor.execute("SELECT id, title, type FROM activities")
    activities = cursor.fetchall()
    
    if not activities:
        print("  No activities found")
    else:
        for activity in activities:
            print(f"  ID {activity[0]}: {activity[1]} (Type: {activity[2]})")
    
    # Ask for confirmation before clearing
    confirm = input("\nDo you want to clear all activities? (y/n): ")
    if confirm.lower() != 'y':
        print("Operation cancelled.")
        conn.close()
        return
    
    # Clear activities
    cursor.execute("DELETE FROM activities")
    conn.commit()
    print("All activities deleted from database.")
    
    # Close connection
    conn.close()
    
    print("\nPlease start the application now and check if any default activities appear.")
    print("After checking, run this script again to verify no activities were added.")

if __name__ == "__main__":
    clear_and_check_activities() 