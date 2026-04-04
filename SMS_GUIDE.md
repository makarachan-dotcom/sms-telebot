# 📱 AI STAND WY2.5 - SMS Service Guide

<p align="center">
  <img src="https://img.shields.io/badge/SMS-TextBelt-blue?style=for-the-badge" alt="SMS">
  <img src="https://img.shields.io/badge/Khmer-🇰🇭-green?style=for-the-badge" alt="Khmer">
</p>

---

## 🎯 Overview

AI STAND WY2.5 includes a powerful **SMS Service** powered by [TextBelt API](https://textbelt.com). Send SMS messages to any phone number worldwide, with special support for **Khmer (Cambodian)** phone numbers!

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📱 **Send SMS** | Send messages to any phone number |
| 👤 **Contacts** | Save and manage phone contacts |
| 🇰🇭 **Khmer Support** | Full support for Cambodian numbers (+855) |
| 🌍 **Multi-Country** | Support for 15+ countries |
| 📜 **History** | Track all sent messages |
| 📊 **Statistics** | Monitor usage and quota |
| 🔑 **API Key** | Use free or your own TextBelt key |

---

## 🚀 Quick Start

### 1. Get TextBelt API Key (Optional)

- **Free**: Use `textbelt` for **1 free SMS per day**
- **Paid**: Get your own key at [textbelt.com](https://textbelt.com) for more messages

### 2. Set Your API Key

```
/sms_setkey textbelt
```

Or use your own key:

```
/sms_setkey your_api_key_here
```

### 3. Set Default Country (Optional)

For Cambodia:
```
/sms_setcountry kh
```

For other countries:
```
/sms_setcountry us  # United States
/sms_setcountry uk  # United Kingdom
/sms_setcountry sg  # Singapore
/sms_setcountry th  # Thailand
```

### 4. Send Your First SMS

```
/sms_send +85512345678 សួស្តី! Hello from AI STAND WY2.5!
```

---

## 📋 SMS Commands

### Main Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/sms` | Show SMS menu and stats | `/sms` |
| `/sms_send` | Send SMS to phone number | `/sms_send +85512345678 Hello!` |
| `/sms_contact` | Send SMS to saved contact | `/sms_contact John Hello!` |
| `/sms_contacts` | List all saved contacts | `/sms_contacts` |
| `/sms_add` | Add a new contact | `/sms_add Sophea 012345678` |
| `/sms_remove` | Remove a contact | `/sms_remove John` |
| `/sms_history` | View sent message history | `/sms_history` |
| `/sms_stats` | View SMS statistics | `/sms_stats` |
| `/sms_setkey` | Set TextBelt API key | `/sms_setkey textbelt` |
| `/sms_setcountry` | Set default country | `/sms_setcountry kh` |
| `/sms_status` | Check delivery status | `/sms_status 12345` |

---

## 📞 Phone Number Formats

### Cambodia (🇰🇭) - Default

The bot automatically handles Khmer phone numbers:

| Input Format | Converted To |
|--------------|--------------|
| `012345678` | `+85512345678` |
| `+85512345678` | `+85512345678` (unchanged) |
| `85512345678` | `+85512345678` |

### Other Countries

Use E.164 format (with + and country code):

| Country | Example |
|---------|---------|
| USA | `+15551234567` |
| UK | `+447712345678` |
| Singapore | `+6591234567` |
| Thailand | `+66812345678` |

---

## 👤 Managing Contacts

### Add a Contact

```
/sms_add Sophea 012345678
```

With notes:
```
/sms_add John +85512345678 Work colleague
```

### List Contacts

```
/sms_contacts
```

Output:
```
🇰🇭 Sophea
   📞 +85512345678

🇺🇸 John
   📞 +15551234567
   Work colleague
```

### Send to Contact

```
/sms_contact Sophea សួស្តី! How are you?
```

### Remove Contact

```
/sms_remove John
```

---

## 📊 Checking Quota

View your remaining SMS quota:

```
/sms_stats
```

Output:
```
📱 SMS Statistics

Usage:
▸ Total SMS Sent: 5
▸ Contacts Saved: 3
▸ History Entries: 5

Settings:
▸ API Key: textbelt (free)
▸ Default Country: 🇰🇭 Cambodia (+855)

Quota:
▸ Remaining: 0 (free daily limit used)
```

---

## 📜 Viewing History

See your sent messages:

```
/sms_history
```

Output:
```
📜 SMS History (Last 10)

✨ Sophea
   📞 +85512345678
   💬 សួស្តី! Hello!
   🔷 2024-01-15 10:30

✨ John
   📞 +15551234567
   💬 Meeting at 3pm
   🔷 2024-01-15 09:15
```

---

## 🔍 Checking Delivery Status

After sending an SMS, check if it was delivered:

```
/sms_status 12345
```

Possible statuses:
- ✅ `DELIVERED` - Message delivered
- 📱 `SENT` - Sent to carrier
- ⏳ `SENDING` - In progress
- ❌ `FAILED` - Delivery failed

---

## 💰 Pricing

### Free Tier
- **1 SMS per day** with key `textbelt`
- No registration required

### Paid Plans
Visit [textbelt.com](https://textbelt.com) for pricing:
- $3 for 50 SMS
- Bulk discounts available

---

## 🛠️ Supported Countries

| Code | Country | Flag | Dial Code |
|------|---------|------|-----------|
| `kh` | Cambodia | 🇰🇭 | +855 |
| `us` | United States | 🇺🇸 | +1 |
| `uk` | United Kingdom | 🇬🇧 | +44 |
| `ca` | Canada | 🇨🇦 | +1 |
| `au` | Australia | 🇦🇺 | +61 |
| `sg` | Singapore | 🇸🇬 | +65 |
| `th` | Thailand | 🇹🇭 | +66 |
| `vn` | Vietnam | 🇻🇳 | +84 |
| `ph` | Philippines | 🇵🇭 | +63 |
| `my` | Malaysia | 🇲🇾 | +60 |
| `id` | Indonesia | 🇮🇩 | +62 |
| `jp` | Japan | 🇯🇵 | +81 |
| `kr` | South Korea | 🇰🇷 | +82 |
| `cn` | China | 🇨🇳 | +86 |
| `in` | India | 🇮🇳 | +91 |

---

## 📝 Examples

### Example 1: Send SMS to Khmer Number

```
User: /sms_send 012345678 សួស្តី! អ្នកសុខសប្បាយទេ?
Bot: ✨ SMS Sent Successfully!

📞 To: +85512345678
💬 Message: សួស្តី! អ្នកសុខសប្បាយទេ?

🔷 Text ID: 12345
💎 Quota Remaining: 0
```

### Example 2: Add Contact and Send

```
User: /sms_add Mom 098765432
Bot: ✨ Contact Added!

👤 Name: Mom
📞 Phone: +85598765432
🇰🇭 Country: Cambodia (+855)

User: /sms_contact Mom សួស្តីម៉ាក់!
Bot: ✨ SMS Sent to Contact!

👤 Name: Mom
📞 Phone: +85598765432
💬 Message: សួស្តីម៉ាក់!
```

### Example 3: Check Stats

```
User: /sms_stats
Bot: 📱 SMS Statistics

Usage:
▸ Total SMS Sent: 10
▸ Contacts Saved: 5
▸ History Entries: 10

Settings:
▸ API Key: custom
▸ Default Country: 🇰🇭 Cambodia (+855)

Quota:
▸ Remaining: 45
```

---

## ⚠️ Important Notes

1. **Phone Format**: Numbers without `+` will use your default country code
2. **Khmer Numbers**: Leading `0` is automatically removed and `+855` added
3. **Message Length**: Long messages may be split into multiple SMS
4. **Delivery**: Not all carriers provide delivery receipts
5. **Quota**: Free tier = 1 SMS/day. Get a paid key for more.

---

## 🔗 Useful Links

- **TextBelt**: https://textbelt.com
- **API Docs**: https://docs.textbelt.com
- **Get API Key**: https://textbelt.com/purchase

---

<p align="center">
  <i>Send SMS worldwide with AI STAND WY2.5! 📱✨</i>
</p>
