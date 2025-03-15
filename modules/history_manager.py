import sqlite3
from datetime import datetime
import json
import os


class HistoryManager:
    def __init__(self):
        self.db_file = "posts_history.db"
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    keywords TEXT NOT NULL,
                    image_url TEXT,
                    wordpress_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'published',
                    template_used TEXT
                )
            """)

    def save_post(self, post_data, wordpress_id):
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("""
                INSERT INTO posts (title, content, keywords, image_url, wordpress_id, template_used)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                post_data['title'],
                post_data['content'],
                post_data['keywords'],
                post_data.get('image_url', ''),
                wordpress_id,
                post_data.get('template', 'default')
            ))

    def get_posts_history(self, limit=50):
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM posts 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_post_stats(self):
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_posts,
                    COUNT(DISTINCT DATE(created_at)) as active_days,
                    ROUND(CAST(COUNT(*) AS FLOAT) / NULLIF(COUNT(DISTINCT DATE(created_at)), 0), 1) as avg_posts_per_day
                FROM posts
            """)
            result = cursor.fetchone()
            if result:
                return {
                    'total_posts': result['total_posts'],
                    'active_days': result['active_days'],
                    'avg_posts_per_day': result['avg_posts_per_day'] or 0
                }
            return {
                'total_posts': 0,
                'active_days': 0,
                'avg_posts_per_day': 0
            }

    def delete_post(self, post_id):
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))

    def update_post_status(self, post_id, status):
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("UPDATE posts SET status = ? WHERE id = ?", (status, post_id))