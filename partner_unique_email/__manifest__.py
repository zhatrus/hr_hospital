{
    "name": "Partner Unique Email",
    "summary": "Prevents duplicate partner emails across the system",
    "description": """
Ensure every partner (contacts and companies) has a unique email address.

Features
--------
- Normalizes emails (trim + lowercase) into a stored field.
- Enforces a unique constraint on normalized emails.
- Supports multiple empty emails (NULL-safe).
""",
    "version": "17.0.1.0.0",
    "category": "Contacts",
    "author": "Khatrus Zakhar",
    'website': 'https://github.com/zhatrus/hr_hospital',
    "license": "LGPL-3",
    "depends": ["base"],
    "data": [],
    "images": [
        "static/description/banner.svg",
        "static/description/icon.svg",
    ],
    "installable": True,
    "application": False,
}
