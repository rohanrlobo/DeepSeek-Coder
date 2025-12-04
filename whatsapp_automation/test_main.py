import unittest
from unittest.mock import MagicMock, patch, call
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
import pandas as pd

# This is a bit of a hack to make the import work without changing the project structure
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import main

class TestSendMessage(unittest.TestCase):

    @patch('main.WebDriverWait')
    def test_send_whatsapp_message_sends_keys_and_clicks_send(self, mock_wait):
        # Arrange
        mock_driver = MagicMock()
        mock_message_box = MagicMock()
        mock_send_button = MagicMock()

        # Configure the mock_wait to return the mock elements for each of the 3 waits.
        mock_wait.return_value.until.side_effect = [
            MagicMock(),      # For the initial chat-list-search wait
            mock_message_box, # For the conversation-compose-box wait
            mock_send_button  # For the send button wait
        ]

        phone_number = "1234567890"
        message = "Hello, this is a test message."

        # Act
        success, status_message = main.send_whatsapp_message(mock_driver, phone_number, message)

        # Assert
        mock_message_box.send_keys.assert_called_once_with(message)
        mock_send_button.click.assert_called_once()
        self.assertTrue(success)
        self.assertEqual(status_message, "Message sent successfully.")

    @patch('main.WebDriverWait')
    def test_send_whatsapp_message_handles_timeout(self, mock_wait):
        # Arrange
        mock_driver = MagicMock()

        # Simulate a TimeoutException when waiting for an element
        mock_wait.return_value.until.side_effect = [
            MagicMock(), # For the initial chat-list-search wait
            TimeoutException()
        ]

        phone_number = "1234567890"
        message = "This message will fail."

        # Act
        success, status_message = main.send_whatsapp_message(mock_driver, phone_number, message)

        # Assert
        self.assertFalse(success)
        self.assertIn("Timed out", status_message)
        self.assertIn(phone_number, status_message)

if __name__ == '__main__':
    unittest.main()
