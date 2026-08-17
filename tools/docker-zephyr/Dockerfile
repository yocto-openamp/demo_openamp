FROM alpine:3.24.1

ENV ZEPHYR_TOP=/opt/zephyrproject
ENV ZEPHYR_BASE=${ZEPHYR_TOP}/zephyr
ENV ZEPHYR_SDK_INSTALL_DIR=/opt/zephyr-sdk

# ccache

RUN apk add --no-cache \
        bash \
        git \
        wget \
        curl \
        cmake \
        ninja \
        gperf \
        dfu-util \
        dtc \
        xz \
        file \
        make \
        gcompat

# UV and python
ENV UV_INSTALL_DIR=/usr/local/bin
ENV UV_PYTHON_INSTALL_DIR=/opt/uv/python
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
RUN uv venv --python 3.13.13 $ZEPHYR_TOP/.venv
ENV PATH="$ZEPHYR_TOP/.venv/bin:${PATH}"

# west
RUN uv pip install --no-cache-dir west

ENV WEST_NUCLEO="hal_stm32 cmsis_6"
ENV WEST_IMX="hal_nxp open-amp libmetal"
# ENV ZEPHYR_REV="v4.4.2"
ENV ZEPHYR_REV="main"

# Fetch Zephyr + all west modules
RUN west init $ZEPHYR_TOP \
        --manifest-url https://github.com/zephyrproject-rtos/zephyr \
        --manifest-rev $ZEPHYR_REV \
        --clone-opt=--depth=1 \
    && cd $ZEPHYR_TOP \
    && west update zephyr $WEST_NUCLEO $WEST_IMX \
    && uv pip install --no-cache-dir -r zephyr/scripts/requirements-base.txt \
    && west zephyr-export

# Install Zephyr SDK
RUN cd $ZEPHYR_BASE \
    && west sdk install \
        --install-dir "$ZEPHYR_SDK_INSTALL_DIR" \
        --no-hosttools \
        --gnu-toolchains arm-zephyr-eabi


ENV XDG_CACHE_HOME=/tmp/.cache
RUN mkdir -m 1777 "$XDG_CACHE_HOME"

ENV HOME=/tmp

WORKDIR /workspace

CMD ["/bin/bash"]
