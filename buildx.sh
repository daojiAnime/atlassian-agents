docker buildx build \
  --platform linux/amd64 \
  -t deep-agents-server:amd64 \
  --output type=docker,dest=./deep-agents-server-amd64.tar \
  .