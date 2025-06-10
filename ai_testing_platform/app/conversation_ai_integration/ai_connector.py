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

    def send_messages_to_llm(self, messages: list) -> dict:
        """
        Sends a list of messages (representing conversation history) to the LLM.

        Args:
            messages (list): A list of message dictionaries, e.g.,
                             [{"role": "user", "content": "Hello"},
                              {"role": "assistant", "content": "Hi there!"}]

        Returns:
            dict: A dictionary containing the status of the operation and AI's response.
        """
        config = self.load_config()
        api_key = config.get('api_key')
        configured_base_url = config.get('api_endpoint')

        if not api_key:
            logger.warning("OpenAI API key not configured. Cannot send messages.")
            return {"status": "error", "message": "OpenAI API key not configured. Please configure API key first."}

        if not messages:
            logger.warning("No messages provided to send_messages_to_llm.")
            return {"status": "error", "message": "No messages provided."}

        try:
            logger.info(f"Sending {len(messages)} messages to OpenAI model gpt-3.5-turbo.")
            # Log the last message content for context, or a summary
            if messages:
                 logger.info(f"Last message role: {messages[-1].get('role')}, content snippet: '{str(messages[-1].get('content'))[:100]}...'")

            if configured_base_url:
                logger.info(f"Using custom base URL: {configured_base_url}")
                client = OpenAI(api_key=api_key, base_url=configured_base_url)
            else:
                client = OpenAI(api_key=api_key)

            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages # Pass the whole conversation history
            )

            llm_response_content = completion.choices[0].message.content
            # The 'id' of the completion can serve as a general interaction ID,
            # but a true 'conversation_id' might need to be managed externally if not part of the completion object for multi-turn.
            # For now, using completion.id is fine for identifying this specific exchange.
            interaction_id = completion.id

            logger.info(f"OpenAI response received. Interaction ID: {interaction_id}")

            return {
                "status": "success",
                "message_from_ai": llm_response_content,
                "interaction_id": interaction_id, # Renamed from conversation_id for clarity this is for one exchange
                "raw_response": completion.model_dump_json(indent=2),
                "api_endpoint_used": str(client.base_url) # Ensure it's a string
            }
        except openai.APIConnectionError as e:
            logger.error(f"OpenAI API Connection Error: {e}")
            return {"status": "error", "message": f"OpenAI API Connection Error: {str(e)}"}
        except openai.RateLimitError as e:
            logger.error(f"OpenAI API Rate Limit Error: {e}")
            return {"status": "error", "message": f"OpenAI API Rate Limit Error: {str(e)}"}
        except openai.APIStatusError as e:
            logger.error(f"OpenAI API Status Error: {e.status_code} - {e.response}")
            return {"status": "error", "message": f"OpenAI API Status Error: {e.status_code} - {str(e.response)}"}
        except Exception as e:
            logger.error(f"An unexpected error occurred with OpenAI: {e}")
            return {"status": "error", "message": f"An unexpected error occurred with OpenAI: {str(e)}"}


if __name__ == '__main__':
    # Example Usage
    connector = AIConnector()
    print("--- Initial: Load config (file might not exist yet) ---")
    # Ensure config.json exists and has a valid API key for testing
    # You might need to create/update instance/config.json manually with your OpenAI key
    # e.g., {"api_endpoint": "https://api.openai.com/v1", "api_key": "sk-YOUR_KEY_HERE"}

    if not os.path.exists(CONFIG_FILE_PATH) or not connector.load_config().get('api_key'):
        print("Config file or API key is missing. Saving a placeholder.")
        print("Please edit instance/config.json with your actual OpenAI API key to test live calls.")
        connector.save_config("https://api.openai.com/v1", "sk-YOUR_OPENAI_API_KEY_HERE")


    print("\n--- Test: Send single message ---")
    messages1 = [{"role": "user", "content": "What's the weather like in London today?"}]
    response1 = connector.send_messages_to_llm(messages1)
    print(f"Response 1 Status: {response1.get('status')}")
    if response1.get('status') == 'success':
        print(f"AI Message: {response1.get('message_from_ai')}")
    else:
        print(f"Error: {response1.get('message')}")

    print("\n--- Test: Send conversation history ---")
    messages2 = [
        {"role": "user", "content": "What is the capital of France?"},
        {"role": "assistant", "content": "The capital of France is Paris."},
        {"role": "user", "content": "What is a famous landmark there?"}
    ]
    response2 = connector.send_messages_to_llm(messages2)
    print(f"Response 2 Status: {response2.get('status')}")
    if response2.get('status') == 'success':
        print(f"AI Message: {response2.get('message_from_ai')}")
    else:
        print(f"Error: {response2.get('message')}")

    print("\n--- Test: Send with unconfigured API key ---")
    # Temporarily save an empty API key
    original_config = connector.load_config()
    connector.save_config(original_config.get('api_endpoint', ''), '') # Empty key

    response_unconfigured = connector.send_messages_to_llm([{"role": "user", "content": "Test"}])
    print(f"Unconfigured Response Status: {response_unconfigured.get('status')}")
    print(f"Message: {response_unconfigured.get('message')}")
    assert response_unconfigured.get('status') == 'error'

    # Restore original config
    if 'original_config' in locals() and original_config.get('api_key'): # ensure original_config was defined
        connector.save_config(original_config.get('api_endpoint', ''), original_config.get('api_key', ''))
    print("\nTesting complete. Check 'instance/config.json'.")


    def evaluate_conversation(self, conversation_history: list, expected_outcome: str, test_case_description: str) -> dict:
        """
        Evaluates a conversation against an expected outcome using an LLM.

        Args:
            conversation_history (list): The history of the conversation.
            expected_outcome (str): The expected outcome of the test case.
            test_case_description (str): The original description of the test case.

        Returns:
            dict: A dictionary containing the evaluation status, verdict, reasoning, and raw response.
        """
        config = self.load_config()
        api_key = config.get('api_key')
        configured_base_url = config.get('api_endpoint')

        if not api_key:
            logger.warning("OpenAI API key not configured. Cannot perform evaluation.")
            return {"status": "error", "message": "OpenAI API key not configured. Please configure API key first."}

        if not conversation_history:
            logger.warning("Conversation history is empty. Cannot perform evaluation.")
            return {"status": "error", "message": "Conversation history is empty."}

        # Construct the prompt for the LLM evaluator
        formatted_history = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in conversation_history])

        evaluation_prompt_content = (
            f"You are an AI Test Evaluator. Based on the provided information, please evaluate the conversation.\n\n"
            f"Test Case Description:\n{test_case_description}\n\n"
            f"Expected Outcome:\n{expected_outcome}\n\n"
            f"Conversation History:\n{formatted_history}\n\n"
            f"Instructions: Provide a verdict ('Pass', 'Fail', or 'Inconclusive') and a concise reasoning for this verdict. "
            f"Structure your response *exactly* as follows, with each part on a new line:\n"
            f"Verdict: [Your Verdict Here]\n"
            f"Reasoning: [Your Reasoning Here]"
        )

        messages_for_eval_llm = [{"role": "user", "content": evaluation_prompt_content}]

        try:
            logger.info(f"Sending conversation for evaluation with prompt: {evaluation_prompt_content[:200]}...") # Log snippet

            if configured_base_url:
                client = OpenAI(api_key=api_key, base_url=configured_base_url)
            else:
                client = OpenAI(api_key=api_key)

            completion = client.chat.completions.create(
                model="gpt-3.5-turbo", # Or a more capable model if needed for better evaluation
                messages=messages_for_eval_llm,
                temperature=0.2 # Lower temperature for more deterministic evaluation
            )

            llm_raw_response_content = completion.choices[0].message.content
            logger.info(f"Raw evaluation response from LLM: {llm_raw_response_content}")

            # Parse the LLM's response string
            extracted_verdict = "Inconclusive (Parsing Failed)"
            extracted_reasoning = "Could not parse verdict and reasoning from LLM response."

            verdict_found = False
            reasoning_found = False

            lines = llm_raw_response_content.strip().split('\n')
            for line in lines:
                if line.lower().startswith("verdict:"):
                    extracted_verdict = line.split(":", 1)[1].strip()
                    verdict_found = True
                elif line.lower().startswith("reasoning:"):
                    extracted_reasoning = line.split(":", 1)[1].strip()
                    reasoning_found = True

            if not verdict_found and not reasoning_found and llm_raw_response_content:
                # If keywords aren't found but there's content, use the whole content as reasoning.
                # This can happen if the LLM doesn't follow formatting instructions perfectly.
                extracted_reasoning = f"LLM did not follow formatting. Raw response: {llm_raw_response_content}"


            return {
                "status": "success",
                "verdict": extracted_verdict,
                "reasoning": extracted_reasoning,
                "raw_eval_response": llm_raw_response_content,
                "api_endpoint_used": str(client.base_url)
            }
        except openai.APIConnectionError as e:
            return {"status": "error", "message": f"OpenAI API Connection Error during evaluation: {str(e)}"}
        except openai.RateLimitError as e:
            return {"status": "error", "message": f"OpenAI API Rate Limit Error during evaluation: {str(e)}"}
        except openai.APIStatusError as e:
            return {"status": "error", "message": f"OpenAI API Status Error during evaluation: {e.status_code} - {str(e.response)}"}
        except Exception as e:
            return {"status": "error", "message": f"An unexpected error occurred during LLM evaluation: {str(e)}"}
