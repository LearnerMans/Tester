import logging
import os
import json
import openai # Added
from openai import OpenAI # Added

# Configure a simple logger for this module
logger = logging.getLogger(__name__)
# BasicConfig should ideally be called once, perhaps in app/__init__.py or run.py if more modules use logging.
# For simplicity in this module, we'll leave it, but be mindful of multiple calls in larger apps.
if not logger.hasHandlers(): # Avoid adding multiple handlers if this module is reloaded
    logging.basicConfig(level=logging.INFO)

# Define the path to the instance folder and the config file within it.
# This assumes run.py is in 'ai_testing_platform/', so 'instance/' is at the same level.
INSTANCE_FOLDER_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'instance')
CONFIG_FILE_PATH = os.path.join(INSTANCE_FOLDER_PATH, 'config.json')


class AIConnector:
    """
    Handles the connection and communication with the target conversational AI product,
    including loading and saving configuration.
    """

    def __init__(self):
        # Ensure instance directory exists when an AIConnector is initialized
        os.makedirs(INSTANCE_FOLDER_PATH, exist_ok=True)

    def load_config(self) -> dict:
        """
        Loads AI configuration (API endpoint and key) from a JSON file in the instance folder.

        Returns:
            dict: Loaded configuration, e.g., {'api_endpoint': '...', 'api_key': '...'}.
                  Returns a default dict with empty strings if the file doesn't exist or is invalid.
        """
        try:
            if os.path.exists(CONFIG_FILE_PATH):
                with open(CONFIG_FILE_PATH, 'r') as f:
                    config = json.load(f)
                    # Ensure essential keys are present, defaulting if not
                    config.setdefault('api_endpoint', '')
                    config.setdefault('api_key', '')
                    return config
            else:
                logger.info(f"Config file not found at {CONFIG_FILE_PATH}. Returning default empty config.")
                return {'api_endpoint': '', 'api_key': ''}
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading or parsing config file {CONFIG_FILE_PATH}: {e}")
            return {'api_endpoint': '', 'api_key': ''} # Return default on error

    def save_config(self, api_endpoint: str, api_key: str) -> bool:
        """
        Saves AI configuration (API endpoint and key) to a JSON file in the instance folder.

        Args:
            api_endpoint (str): The API endpoint URL.
            api_key (str): The API key.

        Returns:
            bool: True if saving was successful, False otherwise.
        """
        config_data = {
            'api_endpoint': api_endpoint,
            'api_key': api_key  # Storing API key directly; consider encryption for production
        }
        try:
            with open(CONFIG_FILE_PATH, 'w') as f:
                json.dump(config_data, f, indent=4)
            logger.info(f"Configuration saved successfully to {CONFIG_FILE_PATH}")
            return True
        except IOError as e:
            logger.error(f"Error saving config file {CONFIG_FILE_PATH}: {e}")
            return False

    def check_connection(self, api_endpoint: str, api_key: str) -> bool:
        """
        Checks if a connection to the AI product can be established using the provided credentials.
        For now, this is a mock validation.

        Args:
            api_endpoint (str): The API endpoint URL of the conversational AI.
            api_key (str): The API key for authentication.

        Returns:
            bool: True if credentials seem valid (non-empty), False otherwise.
        """
        """
        Checks if the provided API endpoint and key are non-empty.
        This method is primarily for validating form input before saving.
        The actual connection test against the live AI service would be more complex.
        """
        masked_api_key = ""
        if api_key and len(api_key) > 4:
            masked_api_key = "****" + api_key[-4:]
        elif api_key:
            masked_api_key = "****" # Mask entirely if too short to show last 4
        else:
            masked_api_key = "Not provided"

        logger.info(f"Performing input validation check for endpoint: {api_endpoint}")
        logger.info(f"API Key for validation (partially masked): {masked_api_key}")

        if api_endpoint and api_key:
            logger.info("Input validation successful: API endpoint and key are present.")
            return True
        else:
            logger.warning("Input validation failed: API endpoint or API key is missing.")
            return False

    def start_conversation(self, test_case_description: str) -> dict:
        """
        Starts a new conversation with the (mock) AI using the test case description.

        Args:
            test_case_description (str): The description of the test case to initiate conversation.

        Returns:
            dict: A dictionary containing the status of the operation and AI's response.
        """
        config = self.load_config()
        api_key = config.get('api_key')
        # The `api_endpoint` from config might be used as `base_url` if provided for OpenAI,
        # or it could be intended for a different AI type entirely.
        # For this specific OpenAI integration, we'll prioritize the api_key.
        # If a custom base_url is needed for OpenAI (e.g. proxy), it should be handled here.
        configured_base_url = config.get('api_endpoint') # User-defined base URL from config

        if not api_key:
            logger.warning("OpenAI API key not configured. Cannot start conversation.")
            return {"status": "error", "message": "OpenAI API key not configured. Please configure API key first."}

        try:
            logger.info(f"Attempting to start conversation with OpenAI model gpt-3.5-turbo.")
            logger.info(f"Test case description: '{test_case_description}'")
            if configured_base_url:
                logger.info(f"Using custom base URL: {configured_base_url}")
                client = OpenAI(api_key=api_key, base_url=configured_base_url)
            else:
                client = OpenAI(api_key=api_key)


            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",  # Or another suitable model like gpt-4
                messages=[
                    {"role": "user", "content": test_case_description}
                ]
            )

            llm_response_content = completion.choices[0].message.content
            conversation_id = completion.id  # The ID of the completion object

            logger.info(f"OpenAI response received. Conversation ID: {conversation_id}")

            return {
                "status": "success",
                "message_from_ai": llm_response_content,
                "conversation_id": conversation_id,
                "raw_response": completion.model_dump_json(indent=2), # For debugging
                "api_endpoint_used": client.base_url # Show actual base URL used
            }
        except openai.APIConnectionError as e:
            logger.error(f"OpenAI API Connection Error: {e}")
            return {"status": "error", "message": f"OpenAI API Connection Error: {e}"}
        except openai.RateLimitError as e:
            logger.error(f"OpenAI API Rate Limit Error: {e}")
            return {"status": "error", "message": f"OpenAI API Rate Limit Error: {e}"}
        except openai.APIStatusError as e:
            logger.error(f"OpenAI API Status Error: {e.status_code} - {e.response}")
            return {"status": "error", "message": f"OpenAI API Status Error: {e.status_code} - {e.response}"}
        except Exception as e:
            logger.error(f"An unexpected error occurred with OpenAI: {e}")
            return {"status": "error", "message": f"An unexpected error occurred with OpenAI: {e}"}


if __name__ == '__main__':
    # Example Usage (demonstrates save and load AND actual API call if key is configured)
    connector = AIConnector() # This will create ../../instance if it doesn't exist

    print("--- Initial: Load config (file might not exist yet) ---")
    initial_config = connector.load_config()
    print(f"Loaded config: {initial_config}")

    print("\n--- Test Case 1: Save and Load Valid Credentials ---")
    test_endpoint = "https://api.example.ai/v1/test"
    test_key = "test_api_key_123456789_xyz"
    print(f"Saving: Endpoint='{test_endpoint}', Key='{test_key}'")
    save_status = connector.save_config(test_endpoint, test_key)
    print(f"Save status: {save_status}")

    loaded_config = connector.load_config()
    print(f"Loaded config after save: {loaded_config}")
    assert loaded_config.get('api_endpoint') == test_endpoint
    assert loaded_config.get('api_key') == test_key

    print("\n--- Test Case 2: Check Connection (Input Validation) ---")
    # This uses the check_connection method which is for form input validation
    check_result = connector.check_connection(test_endpoint, test_key)
    print(f"Input validation check result (valid): {check_result}")
    check_result_invalid = connector.check_connection(test_endpoint, "")
    print(f"Input validation check result (invalid key): {check_result_invalid}")

    print("\n--- Test Case 3: Overwrite config with new values ---")
    new_endpoint = "https://api.new.ai/v2"
    new_key = "new_key_for_testing_000"
    print(f"Saving: Endpoint='{new_endpoint}', Key='{new_key}'")
    connector.save_config(new_endpoint, new_key)
    loaded_config_new = connector.load_config()
    print(f"Loaded config after new save: {loaded_config_new}")
    assert loaded_config_new.get('api_endpoint') == new_endpoint
    assert loaded_config_new.get('api_key') == new_key

    print("\n--- Test Case 4: Start Conversation (Live OpenAI Call if configured) ---")
    # Ensure your instance/config.json has a valid api_key (and optionally api_endpoint for base_url)
    # For example:
    # {
    #    "api_endpoint": "https://api.openai.com/v1", // or your proxy
    #    "api_key": "sk-YOUR_REAL_API_KEY_HERE"
    # }
    # If you haven't run the save config tests above, create instance/config.json manually for this test.

    # First, ensure there's some config (even if it's from previous test runs)
    if not os.path.exists(CONFIG_FILE_PATH) or not connector.load_config().get('api_key'):
        print("Config file or API key is missing. Attempting to save a placeholder.")
        print("Please edit instance/config.json with your actual OpenAI API key to test live calls.")
        connector.save_config("https_api.openai.com_v1_placeholder", "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx") # Replace with your actual endpoint and key in the file

    desc1 = "Tell me a short, funny joke about programming."
    print(f"\nStarting conversation with description: '{desc1}'")
    conv_response1 = connector.start_conversation(desc1)
    print(f"Conversation 1 response status: {conv_response1.get('status')}")
    print(f"Message from AI: {conv_response1.get('message_from_ai')}")
    if conv_response1.get('status') == 'error':
        print(f"Error details: {conv_response1.get('message')}")
    # Basic assertion: if successful, there should be a message.
    # assert conv_response1.get('status') != 'error' or (conv_response1.get('status') == 'error' and "key not configured" in conv_response1.get('message',''))


    print("\n--- Test Case 5: Start Conversation with explicitly Unconfigured API Key ---")
    current_config = connector.load_config() # Save current config
    connector.save_config(current_config.get("api_endpoint",""), "") # Save empty API key
    unconfigured_response = connector.start_conversation("Hello AI, are you there?")
    print(f"Unconfigured AI response status: {unconfigured_response.get('status')}")
    print(f"Message: {unconfigured_response.get('message')}")
    assert unconfigured_response['status'] == 'error'
    assert "API key not configured" in unconfigured_response['message']

    # Restore previous config if it existed
    if current_config.get("api_key"):
         connector.save_config(current_config.get("api_endpoint",""), current_config.get("api_key",""))

    print("\nTesting complete. Check 'instance/config.json'.")
