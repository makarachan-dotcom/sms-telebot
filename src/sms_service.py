"""
AI STAND WY2.5 - SMS Service Module
TextBelt API Integration with Khmer Phone Number Support
Created by Kimi K2.5
"""

from __future__ import annotations

import json
import re
import requests
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# TextBelt API Configuration
TEXTBELT_API_URL = "https://textbelt.com/text"
TEXTBELT_STATUS_URL = "https://textbelt.com/status"
TEXTBELT_QUOTA_URL = "https://textbelt.com/quota"

# Country codes - Cambodia/Khmer
COUNTRY_CODES = {
    "kh": {"code": "+855", "name": "Cambodia (ខ្មែរ)", "flag": "🇰🇭"},
    "us": {"code": "+1", "name": "United States", "flag": "🇺🇸"},
    "uk": {"code": "+44", "name": "United Kingdom", "flag": "🇬🇧"},
    "ca": {"code": "+1", "name": "Canada", "flag": "🇨🇦"},
    "au": {"code": "+61", "name": "Australia", "flag": "🇦🇺"},
    "sg": {"code": "+65", "name": "Singapore", "flag": "🇸🇬"},
    "th": {"code": "+66", "name": "Thailand", "flag": "🇹🇭"},
    "vn": {"code": "+84", "name": "Vietnam", "flag": "🇻🇳"},
    "ph": {"code": "+63", "name": "Philippines", "flag": "🇵🇭"},
    "my": {"code": "+60", "name": "Malaysia", "flag": "🇲🇾"},
    "id": {"code": "+62", "name": "Indonesia", "flag": "🇮🇩"},
    "jp": {"code": "+81", "name": "Japan", "flag": "🇯🇵"},
    "kr": {"code": "+82", "name": "South Korea", "flag": "🇰🇷"},
    "cn": {"code": "+86", "name": "China", "flag": "🇨🇳"},
    "in": {"code": "+91", "name": "India", "flag": "🇮🇳"},
}


@dataclass
class SMSResult:
    """SMS sending result"""
    success: bool
    message: str
    quota_remaining: int = 0
    text_id: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "message": self.message,
            "quota_remaining": self.quota_remaining,
            "text_id": self.text_id,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Contact:
    """Phone contact"""
    name: str
    phone: str
    country_code: str = "kh"  # Default to Cambodia
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "phone": self.phone,
            "country_code": self.country_code,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Contact":
        return cls(
            name=data.get("name", ""),
            phone=data.get("phone", ""),
            country_code=data.get("country_code", "kh"),
            notes=data.get("notes", ""),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
        )
    
    def get_formatted_number(self) -> str:
        """Get phone number in E.164 format"""
        phone = self.phone.strip()
        
        # Remove any non-digit characters except +
        phone = re.sub(r"[^\d+]", "", phone)
        
        # If already has +, return as is
        if phone.startswith("+"):
            return phone
        
        # Get country code
        country = COUNTRY_CODES.get(self.country_code, COUNTRY_CODES["kh"])
        country_prefix = country["code"]
        
        # Remove leading 0 if present (common in local formats)
        if phone.startswith("0"):
            phone = phone[1:]
        
        # Add country code
        return f"{country_prefix}{phone}"


@dataclass
class SMSHistory:
    """SMS history entry"""
    to_name: str
    to_phone: str
    message: str
    result: SMSResult
    api_key_used: str  # 'textbelt' or user's key
    sent_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "to_name": self.to_name,
            "to_phone": self.to_phone,
            "message": self.message,
            "result": self.result.to_dict(),
            "api_key_used": self.api_key_used,
            "sent_at": self.sent_at.isoformat(),
        }


@dataclass
class UserSMSConfig:
    """User SMS configuration"""
    user_id: int
    api_key: str = "textbelt"  # Default to free key
    default_country: str = "kh"  # Default to Cambodia
    sender_name: str = ""
    contacts: List[Contact] = field(default_factory=list)
    history: List[SMSHistory] = field(default_factory=list)
    total_sent: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "api_key": self.api_key,
            "default_country": self.default_country,
            "sender_name": self.sender_name,
            "contacts": [c.to_dict() for c in self.contacts],
            "history": [h.to_dict() for h in self.history],
            "total_sent": self.total_sent,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "UserSMSConfig":
        return cls(
            user_id=data.get("user_id", 0),
            api_key=data.get("api_key", "textbelt"),
            default_country=data.get("default_country", "kh"),
            sender_name=data.get("sender_name", ""),
            contacts=[Contact.from_dict(c) for c in data.get("contacts", [])],
            history=[],  # History loaded separately
            total_sent=data.get("total_sent", 0),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
        )
    
    def add_contact(self, name: str, phone: str, country_code: str = None, notes: str = "") -> Contact:
        """Add a new contact"""
        contact = Contact(
            name=name,
            phone=phone,
            country_code=country_code or self.default_country,
            notes=notes
        )
        self.contacts.append(contact)
        return contact
    
    def remove_contact(self, name: str) -> bool:
        """Remove a contact by name"""
        for i, contact in enumerate(self.contacts):
            if contact.name.lower() == name.lower():
                self.contacts.pop(i)
                return True
        return False
    
    def get_contact(self, name: str) -> Optional[Contact]:
        """Get contact by name"""
        for contact in self.contacts:
            if contact.name.lower() == name.lower():
                return contact
        return None
    
    def add_history(self, history: SMSHistory):
        """Add to history"""
        self.history.append(history)
        if history.result.success:
            self.total_sent += 1
        # Keep only last 100 entries
        if len(self.history) > 100:
            self.history = self.history[-100:]


class SMSService:
    """SMS Service for sending messages via TextBelt API"""
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path("data/sms")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.user_configs: Dict[int, UserSMSConfig] = {}
        self._load_all_configs()
    
    def _get_config_path(self, user_id: int) -> Path:
        """Get config file path for user"""
        return self.data_dir / f"user_{user_id}_sms.json"
    
    def _load_all_configs(self):
        """Load all user configs"""
        for config_file in self.data_dir.glob("user_*_sms.json"):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    config = UserSMSConfig.from_dict(data)
                    self.user_configs[config.user_id] = config
            except Exception as e:
                print(f"Error loading SMS config: {e}")
    
    def get_user_config(self, user_id: int) -> UserSMSConfig:
        """Get or create user SMS config"""
        if user_id not in self.user_configs:
            self.user_configs[user_id] = UserSMSConfig(user_id=user_id)
            self.save_config(user_id)
        return self.user_configs[user_id]
    
    def save_config(self, user_id: int):
        """Save user config to file"""
        if user_id in self.user_configs:
            config_path = self._get_config_path(user_id)
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.user_configs[user_id].to_dict(), f, indent=2, ensure_ascii=False)
    
    def set_api_key(self, user_id: int, api_key: str) -> bool:
        """Set user's TextBelt API key"""
        config = self.get_user_config(user_id)
        config.api_key = api_key.strip()
        self.save_config(user_id)
        return True
    
    def set_default_country(self, user_id: int, country_code: str) -> bool:
        """Set user's default country"""
        if country_code not in COUNTRY_CODES:
            return False
        config = self.get_user_config(user_id)
        config.default_country = country_code
        self.save_config(user_id)
        return True
    
    def send_sms(
        self,
        user_id: int,
        phone: str,
        message: str,
        country_code: str = None,
        use_test_key: bool = False
    ) -> SMSResult:
        """Send SMS via TextBelt API"""
        config = self.get_user_config(user_id)
        
        # Prepare phone number
        phone = phone.strip()
        if not phone.startswith("+"):
            # Use provided country code or default
            cc = country_code or config.default_country
            country = COUNTRY_CODES.get(cc, COUNTRY_CODES["kh"])
            phone_prefix = country["code"]
            
            # Remove leading 0 if present
            if phone.startswith("0"):
                phone = phone[1:]
            
            phone = f"{phone_prefix}{phone}"
        
        # Prepare API key
        api_key = config.api_key
        if use_test_key:
            api_key = f"{api_key}_test"
        
        # Prepare payload
        payload = {
            "phone": phone,
            "message": message,
            "key": api_key,
        }
        
        # Add sender name if set
        if config.sender_name:
            payload["sender"] = config.sender_name
        
        try:
            response = requests.post(
                TEXTBELT_API_URL,
                data=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            result = SMSResult(
                success=data.get("success", False),
                message=message,
                quota_remaining=data.get("quotaRemaining", 0),
                text_id=str(data.get("textId")) if data.get("textId") else None,
                error=data.get("error"),
            )
            
            # Save to history
            history = SMSHistory(
                to_name="Unknown",
                to_phone=phone,
                message=message,
                result=result,
                api_key_used=api_key.replace("_test", ""),
            )
            config.add_history(history)
            self.save_config(user_id)
            
            return result
            
        except requests.exceptions.RequestException as e:
            return SMSResult(
                success=False,
                message=message,
                error=f"Network error: {str(e)}"
            )
        except Exception as e:
            return SMSResult(
                success=False,
                message=message,
                error=f"Error: {str(e)}"
            )
    
    def send_sms_to_contact(
        self,
        user_id: int,
        contact_name: str,
        message: str,
        use_test_key: bool = False
    ) -> Tuple[SMSResult, Optional[Contact]]:
        """Send SMS to a saved contact"""
        config = self.get_user_config(user_id)
        contact = config.get_contact(contact_name)
        
        if not contact:
            return SMSResult(
                success=False,
                message=message,
                error=f"Contact '{contact_name}' not found"
            ), None
        
        phone = contact.get_formatted_number()
        result = self.send_sms(user_id, phone, message, use_test_key=use_test_key)
        
        # Update history with contact name
        if config.history:
            config.history[-1].to_name = contact.name
            self.save_config(user_id)
        
        return result, contact
    
    def check_quota(self, user_id: int) -> Dict:
        """Check remaining quota for user's API key"""
        config = self.get_user_config(user_id)
        
        try:
            response = requests.get(
                f"{TEXTBELT_QUOTA_URL}/{config.api_key}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def check_status(self, text_id: str) -> Dict:
        """Check delivery status of a sent message"""
        try:
            response = requests.get(
                f"{TEXTBELT_STATUS_URL}/{text_id}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def add_contact(
        self,
        user_id: int,
        name: str,
        phone: str,
        country_code: str = None,
        notes: str = ""
    ) -> Contact:
        """Add contact for user"""
        config = self.get_user_config(user_id)
        contact = config.add_contact(name, phone, country_code, notes)
        self.save_config(user_id)
        return contact
    
    def remove_contact(self, user_id: int, name: str) -> bool:
        """Remove contact for user"""
        config = self.get_user_config(user_id)
        result = config.remove_contact(name)
        if result:
            self.save_config(user_id)
        return result
    
    def get_contacts(self, user_id: int) -> List[Contact]:
        """Get all contacts for user"""
        config = self.get_user_config(user_id)
        return config.contacts
    
    def get_history(self, user_id: int, limit: int = 20) -> List[SMSHistory]:
        """Get SMS history for user"""
        config = self.get_user_config(user_id)
        return config.history[-limit:]
    
    def get_stats(self, user_id: int) -> Dict:
        """Get SMS statistics for user"""
        config = self.get_user_config(user_id)
        quota_info = self.check_quota(user_id)
        
        return {
            "total_sent": config.total_sent,
            "contacts_count": len(config.contacts),
            "history_count": len(config.history),
            "api_key": "textbelt (free)" if config.api_key == "textbelt" else "custom",
            "default_country": COUNTRY_CODES.get(config.default_country, COUNTRY_CODES["kh"]),
            "quota_remaining": quota_info.get("quotaRemaining", "Unknown"),
        }


# Global SMS service instance
_sms_service: Optional[SMSService] = None


def get_sms_service(data_dir: Path = None) -> SMSService:
    """Get global SMS service instance"""
    global _sms_service
    if _sms_service is None:
        _sms_service = SMSService(data_dir)
    return _sms_service
