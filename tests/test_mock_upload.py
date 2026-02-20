#!/usr/bin/env python3
"""Test upload step with mocked YouTube API."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


class TestMockUpload(unittest.TestCase):
    def test_step_upload_returns_none_when_token_missing(self):
        """step_upload should return None when youtube-oauth.json does not exist."""
        from scripts import run_pipeline

        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp) / "config"
            config_dir.mkdir()
            # No youtube-oauth.json
            orig = run_pipeline.CONFIG_DIR
            run_pipeline.CONFIG_DIR = config_dir
            try:
                video_path = Path(tmp) / "test.mp4"
                video_path.write_bytes(b"fake video")
                result = run_pipeline.step_upload(
                    video_path, "Test Title", "Test description"
                )
                self.assertIsNone(result)
            finally:
                run_pipeline.CONFIG_DIR = orig

    @patch("googleapiclient.discovery.build")
    def test_step_upload_returns_video_id_on_success(self, mock_build):
        """step_upload should return video_id when API upload succeeds."""
        from scripts import run_pipeline

        mock_youtube = MagicMock()
        mock_request = MagicMock()
        mock_request.execute.return_value = {"id": "abc123"}
        mock_youtube.videos.return_value.insert.return_value.execute = (
            mock_request.execute
        )
        mock_build.return_value = mock_youtube

        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp) / "config"
            config_dir.mkdir()
            token_path = config_dir / "youtube-oauth.json"
            token_path.write_text(
                '{"token": "x", "refresh_token": "y", "client_id": "z", '
                '"client_secret": "w", "scopes": ["https://www.googleapis.com/auth/youtube.upload"]}'
            )
            video_path = Path(tmp) / "test.mp4"
            video_path.write_bytes(b"fake video")

            orig = run_pipeline.CONFIG_DIR
            run_pipeline.CONFIG_DIR = config_dir
            try:
                with patch("google.oauth2.credentials.Credentials") as mock_creds:
                    mock_creds.from_authorized_user_file.return_value = MagicMock(
                        valid=True
                    )
                    result = run_pipeline.step_upload(
                        video_path, "Test Title", "Test description"
                    )
                    self.assertEqual(result, "abc123")
            finally:
                run_pipeline.CONFIG_DIR = orig


if __name__ == "__main__":
    unittest.main()
