"""
litellm updater

    update model for an inference endpoint within LiteLLM
    when the model has been changed on the engine side

2025-10-02 v0.2 - version, fix path for api_base

written by Christian Otto Stelter
"""

import os
import sys
import logging
import requests
import time

from pprint import pprint


engine_api_base = os.environ.get("ENGINE_API_BASE", "http://127.0.0.1:8080")
engine_api_key = os.environ.get("ENGINE_API_KEY", "")

litellm_base_url = os.environ.get("LITELLM_BASE_URL", "http://127.0.0.1:4000")
litellm_api_key = os.environ.get("LITELLM_API_KEY", "")

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def do_api_request(api_url_path, action,
                   data=None,
                   headers=None,
                   timeout=None,
                   silent=False):
    """
    Performs an API request to the specified URL path with the given action.
    """

    logging.debug("API Request URL %s", api_url_path)
    response = None  # default

    if action not in ["POST", "PUT", "GET", "DELETE"]:
        logging.error("unknown action %s", action)
        return response

    if action in ["POST", "PUT"] and data is None:
        logging.error("data missing in %s", action)
        return response

    if timeout is None:
        max_timeout = 180
    else:
        max_timeout = timeout

    try:
        if action == "POST":
            response = requests.post(api_url_path, json=data,
                                     headers=headers, timeout=max_timeout)
        elif action == "PUT":
            response = requests.put(api_url_path, json=data, headers=headers,
                                    timeout=max_timeout)
        elif action == "GET":
            response = requests.get(api_url_path, headers=headers,
                                    timeout=max_timeout)
        elif action == "DELETE":
            response = requests.delete(api_url_path, headers=headers,
                                       timeout=max_timeout)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        if not silent:
            logging.error("Request failed: %s", e)
        return response

    return response


def get_models():
    """ get current models """

    headers = {
        "Authorization": f"Bearer {litellm_api_key}",
        "Content-Type": "application/json"
    }
    url = f"{litellm_base_url}/v1/models"

    response = do_api_request(url, action="GET", headers=headers)
    if response is not None:
        return response.json()
    else:
        return None


def get_model_info():
    """ get model details """

    headers = {
        "Authorization": f"Bearer {litellm_api_key}",
        "Content-Type": "application/json"
    }
    url = f"{litellm_base_url}/v1/model/info"

    response = do_api_request(url, action="GET", headers=headers)
    if response is not None:
        return response.json()
    else:
        return None


def get_model_for_endpoint(endpoint):
    """ get registered model for endpoint """

    model_data = get_model_info()
    if len(model_data["data"]) > 0:
        for model in model_data["data"]:
            if model["litellm_params"]["api_base"] == endpoint:
                return {
                    "model_name": model["model_name"],
                    "model_id": model["model_info"]["id"]
                }
    return None


def get_active_model_on_endpoint(endpoint):
    """ get active model on endpoint """

    headers = {
        "Authorization": f"Bearer {engine_api_key}",
        "Content-Type": "application/json"
    }
    url = f"{engine_api_base}/v1/models"

    response = do_api_request(url, action="GET", headers=headers)
    # if response is not None and response.status_code == 200:
    if response.status_code == 200:
        data = response.json()
        for model in data["data"]:
            if model["id"]:
                return model["id"]

        logging.error("Model ID not found")
        return None
    else:
        logging.error("Unable to retrieve models")
        return None


def delete_model(model_id):
    """ delete a model """

    headers = {
        "Authorization": f"Bearer {litellm_api_key}",
        "Content-Type": "application/json"
    }

    body = {
        "id": model_id
    }

    url = f"{litellm_base_url}/model/delete"
    response = do_api_request(url, action="POST", headers=headers, data=body)
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"Error deleting model: {response.text}")
        return response.json()


def update_model(model_data):
    """ update an existing model """

    headers = {
        "Authorization": f"Bearer {litellm_api_key}",
        "Content-Type": "application/json"
    }

    url = f"{litellm_base_url}/model/update"
    response = do_api_request(url, action="POST", headers=headers, data=model_data)
    if response is not None:
        return response.json()
    else:
        logging.error(f"Error updating model: {response.text}")
        return response.json()


def create_model(model_data):
    """ create a new model """

    headers = {
        "Authorization": f"Bearer {litellm_api_key}",
        "Content-Type": "application/json"
    }

    body = model_data
    url = f"{litellm_base_url}/model/new"
    response = do_api_request(url, action="POST", headers=headers, data=body)
    if response is not None:
        return response.json()
    else:
        logging.error(f"Error creating model: {response.text}")
        return response.json()


def wait_for_engine_ready():
    """ wait for the engine to be ready """

    engine_ready = False

    while not engine_ready:
        headers = {
            "Authorization": f"Bearer {engine_api_key}",
            "Content-Type": "application/json"
        }

        url = f"{engine_api_base}/v1/models"
        response = do_api_request(url, action="GET",
                                  headers=headers,
                                  silent=True)
        if response is None:
            logging.info("Engine not ready, waiting for 5 seconds...")
            time.sleep(5)
        else:
            if response.status_code != 200:
                logging.info("Engine not ready (status code %s), waiting for 5 seconds...", response.status_code)
                time.sleep(5)
                continue
            else:
                model_data = response.json()
                if "data" in model_data and model_data["data"][0]["id"]:
                    model_name = model_data["data"][0]["id"]
                    engine_ready = True

    return model_name


def check_litellm():
    """ check if litellm is ready """
    models = get_models()
    if models is None:
        return None
    else:
        return models


def main():
    logging.info("litellm updater v0.1")

    models = check_litellm()
    if models is None:
        logging.error("Unable to retrieve models from LiteLLM")
        sys.exit(1)

    current_model = get_model_for_endpoint(engine_api_base)
    if current_model is None:
        logging.info("No model found for inference endpoint %s", engine_api_base)
    else:
        logging.info("Current model registered in LiteLLM is %s", current_model["model_name"])

    model_name = wait_for_engine_ready()
    logging.info("Engine is READY, proceeding with updates")

    if model_name is not None:
        logging.info("Active model on inference endpoint %s is %s", engine_api_base, model_name)
    else:
        logging.info("No model found on inference endpoint %s", engine_api_base)

    if current_model is not None and current_model["model_name"] == model_name:
        logging.info("Model already up to date, no action needed.")
        sys.exit(0)
    else:
        if current_model is not None:
            logging.info("Removing previous model %s from endpoint %s", current_model["model_name"], engine_api_base)
            # delete the old model first
            response = delete_model(current_model["model_id"])
            if response is None:
                logging.error("Failed to remove previous model.")
                sys.exit(1)
            else:
                logging.info("Previous model removed successfully: %s", response)

        logging.info("Creating endpoint %s with model %s", engine_api_base, model_name)
        # create a new model
        new_model_data = {
            "model_name": model_name,
            "litellm_params": {
                "api_base": f"{engine_api_base}/v1",
                "api_key": engine_api_key,
                "model": f"openai/{model_name}"
            },
            "model_info": {
                "db_model": True,
                "model": "completion"
            }
        }

        pprint(new_model_data)

        response = create_model(new_model_data)
        if response is None:
            logging.error("Failed to create model.")
            sys.exit(1)
        else:
            logging.info("Model created successfully with ID %s", response["model_id"])

if __name__ == "__main__":
    main()
