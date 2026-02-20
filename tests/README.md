# Tests

- **test_script_length.py** – Script length constraints (~150 words max for Shorts)
- **test_env_validation.py** – Config/.env presence and required API keys (GEMINI, ElevenLabs)
- **test_mock_upload.py** – Upload step with mocked YouTube API

Run all tests:
```bash
python3 -m unittest discover -s tests -v
```

Run validator: `python scripts/setup.py`
