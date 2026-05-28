"""
Firebase Instant Backend for Knowledge Vault Sync

Provides real-time sync between local files and cloud database.
All agents access the same source of truth instantly.

Setup:
1. Install: pip install firebase-admin
2. Create Firebase project at https://console.firebase.google.com
3. Download service account JSON key
4. Set FIREBASE_CREDENTIALS_PATH env var
5. Run: python scripts/init_firebase_sync.py
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

try:
    import firebase_admin
    from firebase_admin import credentials, db
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("[Firebase] firebase-admin not installed. Run: pip install firebase-admin")


class FirebaseKnowledgeSync:
    def __init__(self, company_id: str = "saas-micro-tools"):
        self.company_id = company_id
        self.app = None
        self.enabled = False
        
        if FIREBASE_AVAILABLE:
            self._initialize()
    
    def _initialize(self):
        """Initialize Firebase connection."""
        cred_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")
        db_url = os.environ.get("FIREBASE_DATABASE_URL")
        
        if not cred_path or not db_url:
            print("[Firebase] Missing FIREBASE_CREDENTIALS_PATH or FIREBASE_DATABASE_URL")
            return
        
        try:
            cred = credentials.Certificate(cred_path)
            if not firebase_admin._apps:
                self.app = firebase_admin.initialize_app(cred, {
                    'databaseURL': db_url
                })
            else:
                self.app = firebase_admin.get_app()
            
            self.enabled = True
            print(f"[Firebase] Connected to {db_url}")
        except Exception as e:
            print(f"[Firebase] Initialization failed: {e}")
            self.enabled = False
    
    def upload_company_pack(self, company_path: str):
        """Upload entire company pack to Firebase."""
        if not self.enabled:
            return {"status": "disabled", "reason": "firebase_not_initialized"}
        
        company_dir = Path(company_path)
        if not company_dir.exists():
            return {"status": "error", "reason": "path_not_found"}
        
        data = {
            "company_id": self.company_id,
            "updated_at": datetime.utcnow().isoformat(),
            "files": {}
        }
        
        # Load COMPANY.md
        company_file = company_dir / "COMPANY.md"
        if company_file.exists():
            data["files"]["COMPANY.md"] = company_file.read_text()
        
        # Load policy.json
        policy_file = company_dir / "policy.json"
        if policy_file.exists():
            data["files"]["policy.json"] = json.loads(policy_file.read_text())
        
        # Load services.json
        services_file = company_dir / "services.json"
        if services_file.exists():
            data["files"]["services.json"] = json.loads(services_file.read_text())
        
        # Load pricing.json
        pricing_file = company_dir / "pricing.json"
        if pricing_file.exists():
            data["files"]["pricing.json"] = json.loads(pricing_file.read_text())
        
        # Load skills directory
        skills_dir = company_dir / "skills"
        if skills_dir.exists():
            data["files"]["skills"] = {}
            for skill_file in skills_dir.glob("*.md"):
                data["files"]["skills"][skill_file.stem] = skill_file.read_text()
        
        # Upload to Firebase Realtime Database
        try:
            ref = db.reference(f"/companies/{self.company_id}")
            ref.set(data)
            return {"status": "success", "files_uploaded": len(data["files"])}
        except Exception as e:
            return {"status": "error", "reason": str(e)}
    
    def download_company_pack(self, target_path: str) -> Dict:
        """Download company pack from Firebase to local path."""
        if not self.enabled:
            return {"status": "disabled", "reason": "firebase_not_initialized"}
        
        try:
            ref = db.reference(f"/companies/{self.company_id}")
            data = ref.get()
            
            if not data:
                return {"status": "error", "reason": "company_not_found_in_firebase"}
            
            target_dir = Path(target_path)
            target_dir.mkdir(parents=True, exist_ok=True)
            
            files_written = 0
            
            # Write COMPANY.md
            if "COMPANY.md" in data.get("files", {}):
                (target_dir / "COMPANY.md").write_text(data["files"]["COMPANY.md"])
                files_written += 1
            
            # Write JSON files
            for json_file in ["policy.json", "services.json", "pricing.json"]:
                if json_file in data.get("files", {}):
                    content = data["files"][json_file]
                    if isinstance(content, dict):
                        content = json.dumps(content, indent=2)
                    (target_dir / json_file).write_text(content)
                    files_written += 1
            
            # Write skills directory
            if "skills" in data.get("files", {}):
                skills_dir = target_dir / "skills"
                skills_dir.mkdir(exist_ok=True)
                for skill_name, skill_content in data["files"]["skills"].items():
                    (skills_dir / f"{skill_name}.md").write_text(skill_content)
                    files_written += 1
            
            return {"status": "success", "files_downloaded": files_written}
        except Exception as e:
            return {"status": "error", "reason": str(e)}
    
    def watch_changes(self, callback):
        """Listen for remote changes (real-time sync)."""
        if not self.enabled:
            return
        
        def on_change(event):
            if event.path == "/":
                # Full company pack updated
                callback("full_update", event.data)
            else:
                # Partial update
                callback("partial_update", event.data)
        
        try:
            ref = db.reference(f"/companies/{self.company_id}")
            ref.listen(on_change)
        except Exception as e:
            print(f"[Firebase] Watch error: {e}")
    
    def get_remote_version(self) -> Optional[str]:
        """Get last updated timestamp from Firebase."""
        if not self.enabled:
            return None
        
        try:
            ref = db.reference(f"/companies/{self.company_id}")
            data = ref.get()
            return data.get("updated_at") if data else None
        except Exception:
            return None


# Convenience functions
def sync_to_firebase(company_path: str, company_id: str = "saas-micro-tools") -> Dict:
    """One-line sync to Firebase."""
    sync = FirebaseKnowledgeSync(company_id)
    return sync.upload_company_pack(company_path)


def sync_from_firebase(target_path: str, company_id: str = "saas-micro-tools") -> Dict:
    """One-line sync from Firebase."""
    sync = FirebaseKnowledgeSync(company_id)
    return sync.download_company_pack(target_path)


if __name__ == "__main__":
    # CLI usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python firebase_knowledge_sync.py [upload|download] [path]")
        sys.exit(1)
    
    action = sys.argv[1]
    path = sys.argv[2] if len(sys.argv) > 2 else "."
    
    if action == "upload":
        result = sync_to_firebase(path)
        print(json.dumps(result, indent=2))
    elif action == "download":
        result = sync_from_firebase(path)
        print(json.dumps(result, indent=2))
    else:
        print(f"Unknown action: {action}")
