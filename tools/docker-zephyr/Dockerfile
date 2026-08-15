FROM ubuntu:26.04

ENV DEBIAN_FRONTEND=noninteractive
ENV ZEPHYR_BASE=/opt/zephyrproject/zephyr

RUN apt-get update && apt-get install -y \
    git \
    curl \
    cmake \
    ninja-build \
    gperf \
    ccache \
    dfu-util \
    device-tree-compiler \
    wget \
    curl \
    xz-utils \
    file \
    make \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# UV and python
ENV UV_INSTALL_DIR=/usr/local/bin
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
RUN uv venv --python 3.13.13 /opt/zephyrproject/.venv
ENV PATH="/opt/zephyrproject/.venv/bin:${PATH}"

# west
RUN uv pip install --no-cache-dir west

ENV WEST_NUCLEO="hal_stm32 cmsis_6"
ENV WEST_IMX="hal_nxp open-amp libmetal"

# Fetch Zephyr + all west modules
RUN west init /opt/zephyrproject \
        --manifest-url https://github.com/zephyrproject-rtos/zephyr \
        --manifest-rev v4.4.2 \
        --clone-opt=--depth=1 \
    && cd /opt/zephyrproject \
    && west update zephyr $WEST_NUCLEO $WEST_IMX \
    && uv pip install --no-cache-dir -r zephyr/scripts/requirements-base.txt \
    && west zephyr-export
# RUN cd /opt/zephyrproject \
#     && west packages pip --install

# Install Zephyr SDK
RUN cd /opt/zephyrproject/zephyr \
    && west sdk install

WORKDIR /workspace

CMD ["/bin/bash"]
