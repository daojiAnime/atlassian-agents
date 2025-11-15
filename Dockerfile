FROM python:3.12

WORKDIR /app/

ENV PYTHONUNBUFFERED=1

# Install uv
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:0.9.9 /uv /uvx /bin/

ENV TZ=Asia/Shanghai

# Place executables in the environment at the front of the path
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#using-the-environment
ENV PATH="/app/.venv/bin:$PATH"

# Compile bytecode
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
ENV UV_COMPILE_BYTECODE=1

# uv Cache
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV UV_LINK_MODE=copy

# Install dependencies
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

# Install 
# RUN sed -i s:/deb.debian.org:/mirrors.tuna.tsinghua.edu.cn:g /etc/apt/sources.list.d/* && \
#     apt-get update && \
#     apt-get install -y libzbar0 libgl1 && rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH=/app

COPY ./pyproject.toml ./uv.lock ./main.py ./langgraph.json /app/
COPY ./app /app/app

# Sync the project
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project
    #--no-dev


CMD ["langgraph", "dev", "--no-browser", "--no-reload"]
