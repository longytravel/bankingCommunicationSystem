"""
Debug script to find why banking sentiment isn't loading
"""

import sys
import os
from pathlib import Path

print("=" * 60)
print("DEBUGGING BANKING SENTIMENT IMPORT")
print("=" * 60)

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print(f"\nPython executable: {sys.executable}")
print(f"Current directory: {os.getcwd()}")

# Check if files exist
print("\n1. CHECKING FILE EXISTENCE:")
files_to_check = [
    "src/core/sentiment_analyzer_banking.py",
    "src/app/displays/sentiment_display_banking.py"
]

for filepath in files_to_check:
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"   ✅ {filepath} exists ({size} bytes)")
    else:
        print(f"   ❌ {filepath} NOT FOUND")

# Try importing step by step
print("\n2. ATTEMPTING IMPORTS:")

try:
    from src.core.sentiment_analyzer_banking import analyze_banking_sentiment
    from src.app.displays.sentiment_display_banking import display_banking_sentiment
    print("   ✅ SUCCESS - Banking sentiment imports work!")
except Exception as e:
    print(f"   ❌ FAILURE - Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
