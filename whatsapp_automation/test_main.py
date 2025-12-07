import unittest
from unittest.mock import MagicMock, patch, call
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
import pandas as pd
import urllib.parse
import sys
import os

# Adjust path to import main
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import main

class TestSendMessage(unittest.TestCase):

    @patch('main.is_internet_available', return_value=True)
    @patch('main.WebDriverWait')
    def test_tc01_send_whatsapp_message_sends_keys_and_clicks_send(self, mock_wait, mock_internet):
        # Arrange
        mock_driver = MagicMock()
        mock_send_button = MagicMock()

        # Configure driver.find_element to return the mock button
        mock_driver.find_element.return_value = mock_send_button

        # Configure wait
        mock_wait.return_value.until.return_value = True

        phone_number = "1234567890"
        message = "Hello, this is a test message."
        encoded_message = urllib.parse.quote(message)
        expected_url = f"https://web.whatsapp.com/send?phone=+91{phone_number}&text={encoded_message}"

        # Act
        success, status_message = main.send_whatsapp_message(mock_driver, phone_number, message)

        # Assert
        # Check URL navigation
        mock_driver.get.assert_called_once_with(expected_url)

        # Check that we found the button and clicked it
        mock_driver.find_element.assert_called_with(By.XPATH, '//span[@data-icon="send"]')
        mock_send_button.click.assert_called_once()

        self.assertTrue(success)
        self.assertEqual(status_message, "Success")

    @patch('main.is_internet_available', return_value=True)
    @patch('main.WebDriverWait')
    def test_tc02_send_whatsapp_message_handles_timeout(self, mock_wait, mock_internet):
        # Arrange
        mock_driver = MagicMock()

        # Simulate a TimeoutException when waiting for the send button
        mock_wait.return_value.until.side_effect = TimeoutException()

        phone_number = "1234567890"
        message = "This message will fail."

        # Act
        success, status_message = main.send_whatsapp_message(mock_driver, phone_number, message)

        # Assert
        self.assertFalse(success)
        self.assertIn("Chat not loaded", status_message)

    @patch('main.is_internet_available', return_value=True)
    @patch('main.webdriver.Chrome')
    @patch('main.WebDriverWait')
    def test_tc03_phone_number_formatting(self, mock_wait, mock_driver, mock_internet):
        # Arrange
        # Mocking find_element to avoid failures if the code tries to find the button
        mock_driver.find_element.return_value = MagicMock()

        phone_number = "919876543210"
        message = "message"
        encoded_message = urllib.parse.quote(message)
        expected_url = f"https://web.whatsapp.com/send?phone=+{phone_number}&text={encoded_message}"

        # Act
        main.send_whatsapp_message(mock_driver, phone_number, message)

        # Assert
        # Check that the driver was called with the correctly formatted number and message
        mock_driver.get.assert_called_with(expected_url)

class TestDataHandling(unittest.TestCase):

    @patch('pandas.read_excel')
    def test_tc04_valid_excel_file_reading(self, mock_read_excel):
        # Arrange
        # Create a dummy dataframe that looks like the real data
        d = {'First name': ['test'], 'Last name': ['user'], 'Telephone number': [123], 'Message': ['hello']}
        df = pd.DataFrame(data=d)
        mock_read_excel.return_value = df

        # Act
        result = main.read_contacts("dummy_path.xlsx")

        # Assert
        self.assertIsNotNone(result)
        pd.testing.assert_frame_equal(result, df)

    @patch('pandas.read_excel', side_effect=FileNotFoundError)
    def test_tc05_missing_excel_file(self, mock_read_excel):
        # Act
        result = main.read_contacts("non_existent_path.xlsx")

        # Assert
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
