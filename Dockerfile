FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive

# Install apt-getable dependencies
RUN apt-get update \
    && apt-get install -y \
        build-essential \
        cmake \
        git \
        libeigen3-dev \
        libopencv-dev \
        libceres-dev \
        python3-dev \
        python3-numpy \
        python3-opencv \
        python3-pip \
        python3-pyproj \
        python3-scipy \
        python3-yaml \
        curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# ==================================================================================================
# Flash Attention version 1.0.9. Latest version to support Tesla GPU. For Ampere GPU, use the latest version.
# ==================================================================================================
WORKDIR /app
RUN git clone https://github.com/Dao-AILab/flash-attention.git
RUN cd flash-attention && git checkout 6d48e14a6c2f551db96f0badc658a6279a929df3 && python setup.py install

# ==================================================================================================
# LightGlue. Optionally uses Flash Attention to speed up the process. Patched to work with pre-normalized feature coordinates
# ==================================================================================================
WORKDIR /app
RUN git clone https://github.com/cvg/LightGlue.git
RUN cd LightGlue && git checkout 5a9e87d85905a6770547b86a79fa0ae227d59f36
COPY ./lightglue.patch /app/LightGlue
RUN cd LightGlue && git apply lightglue.patch && python -m pip install -e .

# ==================================================================================================
# pypopsift. GPU accelerated SIFT. needs libboost-all-dev
# ==================================================================================================
WORKDIR /app
RUN git clone --recurse-submodules https://github.com/OpenDroneMap/pypopsift
RUN cd pypopsift && mkdir build && cd build && cmake .. -DPYBIND11_PYTHON_VERSION=3.8
RUN cd pypopsift/build && make -j8
RUN cd pypopsift && pip install -e .

# ==================================================================================================
# ALIKED Feature detector
# ==================================================================================================
WORKDIR /app
RUN git clone --recurse-submodules https://github.com/Shiaoming/ALIKED.git
RUN cd /app/ALIKED && pip install -r requirements.txt
RUN cd /app/ALIKED/custom_ops && sh build.sh

COPY . /source/OpenSfM

WORKDIR /source/OpenSfM

RUN pip3 install -r requirements.txt && \
    python3 setup.py build
