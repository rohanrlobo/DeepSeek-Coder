import unittest
from unittest.mock import MagicMock, patch, call
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

        # Configure the mock_wait to return the mock elements.
        # We use side_effect to return different mock objects for different waits.
        mock_wait.return_value.until.side_effect = [
            MagicMock(),      # For the initial chat-list-search wait
            mock_message_box, # For the conversation-compose-box wait
            mock_send_button  # For the send button wait
        ]

        phone_number = "1234567890"
        message = "Hello, this is a test message."

        # Act
        success = main.send_whatsapp_message(mock_driver, phone_number, message)

        # Assert
        # 1. Check if the correct URL was opened
        mock_driver.get.assert_called_once_with(f"https://web.whatsapp.com/send?phone=+{phone_number}")

        # 2. Check the waits for elements
        mock_driver_wait_calls = [
            call(mock_driver, 60),
            call(mock_driver, 30),
            call(mock_driver, 10),
        ]
        self.assertEqual(mock_wait.call_args_list, mock_driver_wait_calls)


        # 3. Check if send_keys was called on the message box
        mock_message_box.send_keys.assert_called_once_with(message)

        # 4. Check if the send button was clicked
        mock_send_button.click.assert_called_once()

        # 5. Check the function's return value
        self.assertTrue(success)

if __name__ == '__main__':
    unittest.main()
