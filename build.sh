#!/usr/bin/env bash
set -e

# Use local directories for cargo and rustup
export CARGO_HOME=$PWD/.cargo
export RUSTUP_HOME=$PWD/.rustup
export PATH=$CARGO_HOME/bin:$PATH

# Install Rust (stable) via rustup
curl https://sh.rustup.rs -sSf | sh -s -- -y
rustup default stable

# Upgrade pip and install maturin
pip install --upgrade pip maturin

export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1

# Build and install QuizParser
cd routes/QuizParser
maturin build --release
pip install target/wheels/*.whl
cd ../..

# Ensure requirements.txt exists
if [ ! -f requirements.txt ]; then
    touch requirements.txt
fi
pip install -r requirements.txt
