docker buildx build \
  --platform linux/amd64 \
  -t deep-agents-ui:amd64 \
  --output type=docker,dest=./deep-agents-ui-amd64.tar \
  .