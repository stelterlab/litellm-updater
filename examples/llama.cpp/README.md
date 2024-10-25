# How to use with llama.cpp server

copy env_example to .env and adjust the values (IPs, Keys, etc.)

After that, run the following command to start the containers:

```
docker compose up -d
```

as usual. The litellm-update will terminate after it has done its job.

This will use only the CPU. If you want to passthru you GPU you will have to add the necessary extras. For example with NVIDIA GPUs:

```
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

[NIVIDA container toolkit required](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

You will have to build it before running it:

```
docker build -t litellm-update:dev .
```
