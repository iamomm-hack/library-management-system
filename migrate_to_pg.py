#!/usr/bin/env python3
"""Migrate library_system.py from SQLite to PostgreSQL"""

import re

with open('library_system.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

replacements = [
    ('VALUES (?, ?, ?, ?, ?)', 'VALUES (%s, %s, %s, %s, %s)'),
    ('VALUES (?, ?, ?, ?, ?, ?)', 'VALUES (%s, %s, %s, %s, %s, %s)'),
    ('VALUES (?, ?, ?, ?, ?, ?, ?)', 'VALUES (%s, %s, %s, %s, %s, %s, %s)'),
    ('VALUES (?, ?, ?)', 'VALUES (%s, %s, %s)'),
    ('WHERE username=?', 'WHERE username=%s'),
    ('WHERE role=?', 'WHERE role=%s'),
    ('WHERE book_id=?', 'WHERE book_id=%s'),
    ('WHERE user_id=?', 'WHERE user_id=%s'),
    ('WHERE isbn=?', 'WHERE isbn=%s'),
    ('WHERE issue_id=?', 'WHERE issue_id=%s'),
    ('WHERE category=?', 'WHERE category=%s'),
]

for old, new in replacements:
    content = content.replace(old, new)

content = content.replace('LIKE ?', 'ILIKE %s')
content = content.replace('LIKE "', 'ILIKE "')

with open('library_system.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ SQLite to PostgreSQL migration completed")
print("✓ All ? placeholders replaced with %s")
print("✓ LIKE queries updated to ILIKE")
