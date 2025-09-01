"""
Debug script to find the actual import errors
"""

import sys
import os
from pathlib import Path

print("=" * 60)
print("IMPORT DEBUG")
print("=" * 60)

# Add parent directory to path (so we can import as src.core.xxx)
parent_dir = Path.cwd().parent
sys.path.insert(0, str(parent_dir))
print(f"Added to path: {parent_dir}")

# Try importing each module and show the actual error
print("\n1. Testing SharedBrain import:")
try:
    from src.core.shared_brain import SharedBrain
    print("✅ SharedBrain imported successfully!")
except ImportError as e:
    print(f"❌ Import Error: {e}")
except Exception as e:
    print(f"❌ Other Error: {e}")
    import traceback
    traceback.print_exc()

print("\n2. Testing SmartEmailGenerator import:")
try:
    from src.core.smart_email_generator import SmartEmailGenerator
    print("✅ SmartEmailGenerator imported successfully!")
except ImportError as e:
    print(f"❌ Import Error: {e}")
except Exception as e:
    print(f"❌ Other Error: {e}")
    import traceback
    traceback.print_exc()

print("\n3. Testing SmartSMSGenerator import:")
try:
    from src.core.smart_sms_generator import SmartSMSGenerator
    print("✅ SmartSMSGenerator imported successfully!")
except ImportError as e:
    print(f"❌ Import Error: {e}")
except Exception as e:
    print(f"❌ Other Error: {e}")
    import traceback
    traceback.print_exc()

print("\n4. Testing dependencies:")
# Check if anthropic is installed
try:
    import anthropic
    print("✅ anthropic is installed")
except ImportError:
    print("❌ anthropic NOT installed - Run: pip install anthropic")

# Check if dotenv is installed
try:
    from dotenv import load_dotenv
    print("✅ python-dotenv is installed")
except ImportError:
    print("❌ python-dotenv NOT installed - Run: pip install python-dotenv")

# Check if streamlit is installed
try:
    import streamlit
    print("✅ streamlit is installed")
except ImportError:
    print("❌ streamlit NOT installed - Run: pip install streamlit")

print("\n5. Checking __init__.py:")
init_path = Path("core/__init__.py")
if init_path.exists():
    print(f"✅ __init__.py exists (size: {init_path.stat().st_size} bytes)")
    # Try importing from __init__
    try:
        from src.core import SharedBrain
        print("✅ Can import SharedBrain from __init__.py")
    except ImportError as e:
        print(f"❌ Cannot import from __init__.py: {e}")
else:
    print("❌ __init__.py NOT found")

print("\n" + "=" * 60)
print("If you see import errors above, that's the problem!")
print("=" * 60)