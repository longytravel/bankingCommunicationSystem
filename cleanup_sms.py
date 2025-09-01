@'
import os
import re
from pathlib import Path

def cleanup_sms_legacy():
    print("🧹 Starting SMS Legacy Cleanup...")
    print("=" * 50)
    
    # 1. Remove SimpleSMSOrchestrator file if it exists
    sms_orchestrator_file = Path("src/core/simple_sms_orchestrator.py")
    if sms_orchestrator_file.exists():
        print(f"🗑️  Removing {sms_orchestrator_file}")
        sms_orchestrator_file.unlink()
        print("   ✅ SimpleSMSOrchestrator file deleted")
    else:
        print("   ⚠️  SimpleSMSOrchestrator file not found")
    
    # 2. Update Config.py SMS settings
    config_file = Path("src/config.py")
    if config_file.exists():
        print(f"🔧 Updating SMS config in {config_file.name}")
        
        with open(config_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Update SMS max_length from 160 to 480
        if "max_length': 160" in content:
            content = content.replace("max_length': 160", "max_length': 480")
            print("   ✅ Updated SMS limit from 160 to 480 characters")
        
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(content)
    
    print("=" * 50)
    print("✅ SMS Legacy Cleanup Complete!")

if __name__ == "__main__":
    cleanup_sms_legacy()
'@ | Out-File -FilePath "cleanup_sms.py" -Encoding UTF8