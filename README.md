# litellm-updater

a little helper to update the served model for an endpoint within [LiteLLM proxy](https://github.com/BerriAI/litellm) made by Berri AI

It is intended to run after the shutdown of the endpoint and before the restart of the endpoint. The current version is designed to work with OpenAI compatible endpoints - inference servers like the llama.cpp server, Huggingface TGI or similar.

I use the proxy part of LiteLLM for 2 or 3 endpoints for test purposes - having only one endpoint in my configs with different keys for each application. I change the models frequently as I don't have endless GPU resources in my home lab to test different models depending on the use case. This script helps me to update the models without manually changing the configuration.

## How it works

The script will check the model that is currently registered in the LiteLLM proxy and compare it with the model that the endpoint is serving after restart. If the model is different, it will update the model in the LiteLLM proxy to match the model that the endpoint is serving. Otherwise, it will leave the LiteLLM config untouched.

As long as the endpoint is restarting it will retry every 5 seconds until the endpoint is up and running again.

## Usage

You need to set the following environment variables:

```
ENGINE_API_BASE=http://192.168.0.101:8080/v1
ENGINE_API_KEY=53cr3TenDPo1ntKeY
LITELLM_BASE_URL=http://192.168.0.123:4000
LITELLM_API_KEY=sk-1234
```

You can also put it into a container and run it together with your inference server. For example:

docker-compose.yml for lama.cpp's server (using just a CPU, no GPU)

```
services:
  litellm-updater:
    image: litellm-updater:dev
    env_file: .env
    container_name: litellm-updater
  networks:
    - engine

  llamacpp-server:
    image: ghcr.io/ggerganov/llama.cpp:server
    container_name: llama-cpp
    ports:
      - 8080:8080
    volumes:
      - ./models:/models
    env_file: .env
    networks:
      - engine

networks:
  engine:
    name: engineroom
```

_**NOTE** mind the docker build -t litellm-updater:dev ._

example .env file

```
LLAMA_ARG_MODEL=/models/gemma-2-2b-it-Q4_K_M.gguf
LLAMA_ARG_ALIAS=gemma-2-2b
LLAMA_ARG_CTX_SIZE=32768
LLAMA_ARG_N_PARALLEL=2
LLAMA_ARG_ENDPOINT_METRICS=1
LLAMA_ARG_PORT=8080
LLAMA_API_KEY=53cr3TenDPo1ntKeY
ENGINE_API_BASE=http://192.168.0.101:8080/v1
ENGINE_API_KEY=${LLAMA_API_KEY}
LITELLM_BASE_URL=http://192.168.0.123:4000
LITELLM_API_KEY=sk-1234
```

## Dependencies

For testing LiteLLM v1.76.1-stable was used as last version. As long as the LiteLLM API remains stable, the script should work with any (newer) versions of LiteLLM. ;-)

Needs requests library for Python. Install it with pip:

```
pip install requests
```
