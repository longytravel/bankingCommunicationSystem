# Lloyds Banking Communication System

A powerful AI-driven system that transforms generic bank letters into personalized customer communications in any language.

## Features

- Universal Language Support: Personalizes content in ANY language
- Complete Personalization: Tailors every message to individual customer profiles
- Quick Test Mode: Rapid testing with 5-customer samples
- Multi-Channel Output: Email, SMS, Letter, and In-app formats
- Lloyds Branding: Professional UI with corporate design standards

## Quick Start

### Prerequisites
- Python 3.9+
- Windows with PowerShell
- API Key for Claude (Anthropic)

### Installation

1. Clone the repository
2. Run setup_project.ps1
3. Activate virtual environment: .\venv\Scripts\Activate.ps1
4. Install dependencies: pip install -r requirements.txt
5. Run the application: .\run.ps1

## Quick Testing

For rapid development testing:
- Test with 5 customers: .\run.ps1 -TestMode
- Test without API calls: .\run.ps1 -MockMode
- Clear cache: .\run.ps1 -ClearCache

## Support

For issues or questions, please contact the development team or raise an issue on GitHub.


## 🎙️ Voice Note Generation (NEW)

The system now includes AI-powered voice note generation using OpenAI's TTS API.

### Features
- Automatic voice note generation for digitally-active customers
- Multi-language support with appropriate voice selection
- Rules-based eligibility (no hardcoding)
- Real MP3 audio file generation

### Setup
1. Add your OpenAI API key to `.env`
2. Run `.\setup_voice.ps1`
3. Test with `python src\voice_integration.py --test-rules`

See [VOICE_NOTES_README.md](VOICE_NOTES_README.md) for detailed documentation.

---
(C) 2025 Lloyds Banking Group
