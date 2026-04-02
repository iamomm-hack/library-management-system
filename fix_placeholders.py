import re

with open('library_system.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Replace all remaining problematic patterns
replacements = [
    ('WHERE i.user_id = ? AND i.status', 'WHERE i.user_id = %s AND i.status'),
    ('VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', 'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'),
    ('WHERE book_id=%s OR isbn=?', 'WHERE book_id=%s OR isbn=%s'),
    ('WHERE book_id = ?', 'WHERE book_id = %s'),
    ('WHERE i.issue_id = ? AND i.status', 'WHERE i.issue_id = %s AND i.status'),
    ('SET return_date = ?, fine_amount = ?, status', 'SET return_date = %s, fine_amount = %s, status'),
    ('WHERE issue_id = ?', 'WHERE issue_id = %s'),
    ('WHERE book_id = ? AND user_id = ?', 'WHERE book_id = %s AND user_id = %s'),
    ('VALUES (?, ?, \'active\')', "VALUES (%s, %s, 'active')"),
]

for old, new in replacements:
    content = content.replace(old, new)

with open('library_system.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ All remaining ? replaced with %s")
