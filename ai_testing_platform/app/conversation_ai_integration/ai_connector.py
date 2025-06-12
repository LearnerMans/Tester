import logging
import os
import json
import openai
from openai import OpenAI
import google.generativeai as genai # Added
import uuid # Added

# Configure a simple logger for this module
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO)

INSTANCE_FOLDER_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'instance')
CONFIG_FILE_PATH = os.path.join(INSTANCE_FOLDER_PATH, 'config.json')


class AIConnector:
    """
    Handles the connection and communication with various conversational AI providers,
    including loading and saving configuration, and managing provider-specific clients.
    """

    def __init__(self):
        os.makedirs(INSTANCE_FOLDER_PATH, exist_ok=True)
        self.config = self.load_config() # Load config on init
        self.provider = self.config.get('llm_provider', 'openai') # Default to openai

        self.openai_client = None
        self.gemini_model = None # For Gemini, this will be the GenerativeModel instance

        logger.info(f"AIConnector initialized with provider: {self.provider}")

        if self.provider == 'openai':
            openai_api_key = self.config.get('openai_api_key')
            openai_base_url = self.config.get('openai_api_endpoint') # Custom base URL
            if openai_api_key:
                try:
                    self.openai_client = OpenAI(
                        api_key=openai_api_key,
                        base_url=openai_base_url if openai_base_url else None # Pass None if empty to use default
                    )
                    logger.info("OpenAI client configured.")
                except Exception as e:
                    logger.error(f"Error initializing OpenAI client: {e}")
            else:
                logger.warning("OpenAI API key not found in config. OpenAI client not configured.")

        elif self.provider == 'google_gemini':
            gemini_api_key = self.config.get('gemini_api_key')
            if gemini_api_key:
                try:
                    genai.configure(api_key=gemini_api_key)
                    configured_gemini_model = self.config.get('gemini_model_name', 'gemini-pro')
                    self.gemini_model = genai.GenerativeModel(configured_gemini_model)
                    logger.info(f"Google Gemini client configured with model {configured_gemini_model}.")
                except Exception as e:
                    logger.error(f"Error configuring Google Gemini client: {e}")
                    self.gemini_model = None # Ensure it's None on error
            else:
                logger.warning("Google Gemini API key not found in config. Gemini client not configured.")
        else:
            logger.warning(f"Unsupported LLM provider selected: {self.provider}")

    def load_config(self) -> dict:
        """
        Loads AI configuration from a JSON file in the instance folder.
        Includes LLM provider, OpenAI keys/endpoint, and Gemini keys.

        Returns:
            dict: Loaded configuration. Defaults are provided for missing keys.
        """
        default_config = {
            'llm_provider': 'openai',
            'openai_api_key': '',
            'openai_api_endpoint': '',
            'gemini_api_key': '',
            'openai_model_name': 'gpt-4o', # Default OpenAI model
            'gemini_model_name': 'gemini-pro'  # Default Gemini model
        }
        try:
            if os.path.exists(CONFIG_FILE_PATH):
                with open(CONFIG_FILE_PATH, 'r') as f:
                    config = json.load(f)
                    # Ensure all expected keys are present, merging with defaults
                    # This preserves existing keys while adding new ones if they are missing.
                    final_config = default_config.copy()
                    final_config.update(config) # Overwrite defaults with loaded values

                    # Specific handling for renamed keys for backward compatibility
                    if 'api_key' in config and 'openai_api_key' not in config:
                        final_config['openai_api_key'] = config['api_key']
                    if 'api_endpoint' in config and 'openai_api_endpoint' not in config:
                        final_config['openai_api_endpoint'] = config['api_endpoint']

                    return final_config
            else:
                logger.info(f"Config file not found at {CONFIG_FILE_PATH}. Returning default config.")
                return default_config
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading or parsing config file {CONFIG_FILE_PATH}: {e}")
            return default_config # Return default on error

    def save_config(self, llm_provider: str, openai_api_key: str, openai_api_endpoint: str, gemini_api_key: str, openai_model_name: str, gemini_model_name: str) -> bool:
        """
        Saves AI configuration to a JSON file in the instance folder.

        Args:
            llm_provider (str): The selected LLM provider.
            openai_api_key (str): The API key for OpenAI.
            openai_api_endpoint (str): The custom base URL for OpenAI.
            gemini_api_key (str): The API key for Google Gemini.
            openai_model_name (str): The model name for OpenAI.
            gemini_model_name (str): The model name for Gemini.

        Returns:
            bool: True if saving was successful, False otherwise.
        """
        config_data = {
            'llm_provider': llm_provider,
            'openai_api_key': openai_api_key,
            'openai_api_endpoint': openai_api_endpoint,
            'gemini_api_key': gemini_api_key,
            'openai_model_name': openai_model_name,
            'gemini_model_name': gemini_model_name
        }
        try:
            # Ensure instance directory exists (should be by __init__, but good to double check)
            os.makedirs(INSTANCE_FOLDER_PATH, exist_ok=True)
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
        if not messages:
            logger.warning("No messages provided to send_messages_to_llm.")
            return {"status": "error", "message": "No messages provided."}

        if self.provider == 'openai':
            if not self.openai_client:
                logger.error("OpenAI client not configured (API key missing or invalid in __init__).")
                return {"status": "error", "message": "OpenAI client not configured. Please check API key and configuration."}

            openai_model_to_use = self.config.get('openai_model_name', 'gpt-4o')
            logger.info(f"Sending {len(messages)} messages to OpenAI model {openai_model_to_use}.")
            if messages:
                 logger.info(f"Last message role: {messages[-1].get('role')}, content snippet: '{str(messages[-1].get('content'))[:100]}...'")

            try:
                completion = self.openai_client.chat.completions.create(
                    model=openai_model_to_use,
                    messages=messages
                )
                llm_response_content = completion.choices[0].message.content
                interaction_id = completion.id
                logger.info(f"OpenAI response received. Interaction ID: {interaction_id}")
                return {
                    "status": "success",
                    "message_from_ai": llm_response_content,
                    "interaction_id": interaction_id,
                    "raw_response": completion.model_dump_json(indent=2),
                    "api_endpoint_used": str(self.openai_client.base_url)
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

        elif self.provider == 'google_gemini':
            if not self.gemini_model:
                logger.error("Google Gemini client not configured (API key missing or configuration error in __init__).")
                return {"status": "error", "message": "Google Gemini client not configured. Please check API key and configuration."}

            gemini_history = []
            last_user_message_content = ""

            if messages:
                processed_messages = []
                # Gemini prefers strict user/model alternation. Consolidate consecutive messages.
                for msg in messages:
                    role = 'model' if msg['role'] == 'assistant' else msg['role']
                    if role not in ['user', 'model']: # Skip system or other roles for now
                        continue
                    if processed_messages and processed_messages[-1]['role'] == role:
                        processed_messages[-1]['parts'][0]['text'] += "\n" + msg['content'] # Append content
                    else:
                        processed_messages.append({'role': role, 'parts': [{'text': msg['content']}]})

                # Separate last user message from history for send_message method
                if processed_messages and processed_messages[-1]['role'] == 'user':
                    last_user_message_content = processed_messages[-1]['parts'][0]['text']
                    gemini_history = processed_messages[:-1]
                elif processed_messages: # Last message is 'model', just pass all as history and send empty user message (or specific prompt)
                     gemini_history = processed_messages
                     # This scenario might need a specific "continue" prompt for Gemini if last was model.
                     # For now, if last is model, we'll send a generic "continue" or expect user to provide next input.
                     # Let's assume for now that the very last message in `messages` list is always the one to send.
                     # The problem description implies `messages` is the full history *including* the latest user message.
                     return {"status": "error", "message": "Last message to send to Gemini must be from a user role for this flow."}


            if not last_user_message_content: # This implies `messages` was empty or ended with assistant.
                 return {"status": "error", "message": "No user message found as the last message to send to Gemini."}

            logger.info(f"Sending message to Google Gemini ({self.gemini_model.model_name}). History length: {len(gemini_history)}.")
            logger.info(f"Last user message content snippet: '{last_user_message_content[:100]}...'")

            try:
                chat = self.gemini_model.start_chat(history=gemini_history)
                gemini_response = chat.send_message(last_user_message_content)

                message_content = ""
                if gemini_response.parts:
                    message_content = ''.join(part.text for part in gemini_response.parts if hasattr(part, 'text'))
                elif hasattr(gemini_response, 'text'):
                    message_content = gemini_response.text

                if not message_content and gemini_response.candidates and hasattr(gemini_response.candidates[0], 'finish_reason') and str(gemini_response.candidates[0].finish_reason) != "STOP":
                    # Check for safety reasons if content is empty
                    reason_str = str(gemini_response.candidates[0].finish_reason)
                    # Safety ratings can be checked here: gemini_response.candidates[0].safety_ratings
                    categories_blocked = [rating.category for rating in gemini_response.candidates[0].safety_ratings if str(rating.probability) not in ["NEGLIGIBLE", "LOW"]]
                    if categories_blocked:
                         message_content = f"Response blocked due to safety reasons: {reason_str} (Categories: {', '.join(map(str,categories_blocked))}). Content may be incomplete or unavailable."
                    else:
                         message_content = f"Response stopped due to: {reason_str}. Content may be incomplete or unavailable."


                interaction_id = "gemini_interaction_" + str(uuid.uuid4())
                # Use configured model name for api_info
                gemini_model_to_use = self.config.get('gemini_model_name', 'gemini-pro')
                api_info = f"Google Gemini ({gemini_model_to_use})"

                return {
                    "status": "success",
                    "message_from_ai": message_content,
                    "interaction_id": interaction_id,
                    "raw_response": str(gemini_response),
                    "api_endpoint_used": api_info
                }
            except Exception as e:
                logger.error(f"Google Gemini API Error: {e}")
                return {"status": "error", "message": f"Google Gemini API Error: {str(e)}"}

        else:
            logger.error(f"Unsupported LLM provider: {self.provider}")
            return {"status": "error", "message": f"Unsupported LLM provider: {self.provider}"}


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
        llm_raw_response_content = ""
        api_info_for_eval = ""

        logger.info(f"Sending conversation for evaluation using provider: {self.provider}. Prompt snippet: {evaluation_prompt_content[:200]}...")

        if self.provider == 'openai':
            if not self.openai_client:
                return {"status": "error", "message": "OpenAI client not configured for evaluation."}
            try:
                openai_model_to_use = self.config.get('openai_model_name', 'gpt-4o')
                logger.info(f"Using OpenAI model for evaluation: {openai_model_to_use}")
                completion = self.openai_client.chat.completions.create(
                    model=openai_model_to_use,
                    messages=messages_for_eval_llm,
                    temperature=0.2
                )
                llm_raw_response_content = completion.choices[0].message.content
                api_info_for_eval = f"OpenAI ({openai_model_to_use}) via {str(self.openai_client.base_url)}"
            except openai.APIConnectionError as e: return {"status": "error", "message": f"OpenAI API Connection Error during evaluation: {str(e)}"}
            except openai.RateLimitError as e: return {"status": "error", "message": f"OpenAI API Rate Limit Error during evaluation: {str(e)}"}
            except openai.APIStatusError as e: return {"status": "error", "message": f"OpenAI API Status Error during evaluation: {e.status_code} - {str(e.response)}"}
            except Exception as e: return {"status": "error", "message": f"An unexpected error with OpenAI during evaluation: {str(e)}"}

        elif self.provider == 'google_gemini':
            if not self.gemini_model:
                return {"status": "error", "message": "Google Gemini client not configured for evaluation."}
            try:
                # For evaluation, Gemini's chat history isn't strictly needed if the prompt is self-contained.
                # We send the single detailed prompt as the first user message.
                gemini_response = self.gemini_model.generate_content(evaluation_prompt_content) # Simpler API for single-turn

                if gemini_response.parts:
                    llm_raw_response_content = ''.join(part.text for part in gemini_response.parts if hasattr(part, 'text'))
                elif hasattr(gemini_response, 'text'):
                     llm_raw_response_content = gemini_response.text

                if not llm_raw_response_content and gemini_response.candidates and hasattr(gemini_response.candidates[0], 'finish_reason') and str(gemini_response.candidates[0].finish_reason) != "STOP":
                    reason_str = str(gemini_response.candidates[0].finish_reason)
                    categories_blocked = [rating.category for rating in gemini_response.candidates[0].safety_ratings if str(rating.probability) not in ["NEGLIGIBLE", "LOW"]]
                    if categories_blocked:
                        llm_raw_response_content = f"Response blocked due to safety reasons: {reason_str} (Categories: {', '.join(map(str,categories_blocked))}). Content may be incomplete or unavailable."
                    else:
                        llm_raw_response_content = f"Response stopped due to: {reason_str}. Content may be incomplete or unavailable."

                gemini_model_to_use = self.config.get('gemini_model_name', 'gemini-pro')
                api_info_for_eval = f"Google Gemini ({gemini_model_to_use})"
            except Exception as e:
                return {"status": "error", "message": f"Google Gemini API Error during evaluation: {str(e)}"}

        else:
            return {"status": "error", "message": f"Unsupported LLM provider for evaluation: {self.provider}"}

        logger.info(f"Raw evaluation response from LLM ({self.provider}): {llm_raw_response_content}")
        # Parse the LLM's response string (common logic for both providers)
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
            extracted_reasoning = f"LLM did not follow formatting instructions. Raw response: {llm_raw_response_content}"

        return {
            "status": "success", # Status of the evaluation *attempt*
            "verdict": extracted_verdict,
            "reasoning": extracted_reasoning,
            "raw_eval_response": llm_raw_response_content,
            "api_endpoint_used": api_info_for_eval
        }
