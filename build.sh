#!/usr/bin/env bash
set -e

# Use local directories for cargo and rustup
export CARGO_HOME=$PWD/.cargo
export RUSTUP_HOME=$PWD/.rustup
export PATH=$CARGO_HOME/bin:$PATH

# Install Rust (stable) via rustup
curl https://sh.rustup.rs -sSf | sh -s -- -y --default-toolchain stable --profile minimal
source $CARGO_HOME/env

# Verify installation
rustc --version
cargo --version

# Set performance-focused build flags
export RUSTFLAGS="-C target-cpu=native -C opt-level=3"
export CARGO_PROFILE_RELEASE_LTO=fat
export CARGO_PROFILE_RELEASE_CODEGEN_UNITS=1
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1

# Upgrade pip and install maturin
pip install --upgrade pip
pip install maturin

# Install TypeScript compiler (Node.js is pre-installed on Render)
echo "Installing TypeScript compiler..."
npm install -g typescript

# Compile TypeScript files
echo "Compiling TypeScript files..."
if [ -f tsconfig.json ]; then
    tsc
else
    echo "No tsconfig.json found, skipping TypeScript compilation"
fi

# Build and install QuizParser with maximum optimizations
cd routes/QuizParser
echo "Building QuizParser with maximum optimizations..."
maturin build --release --strip
pip install --force-reinstall target/wheels/*.whl
cd ../..

# Build and install StudyPlanParser with maximum optimizations
cd routes/StudyPlanParser
echo "Building StudyPlanParser with maximum optimizations..."
maturin build --release --strip
pip install --force-reinstall target/wheels/*.whl
cd ../..

# Build and install SubmitQuizResult with maximum optimizations
cd routes/SubmitQuizResult
echo "Building SubmitQuizResult with maximum optimizations..."
maturin build --release --strip
pip install --force-reinstall target/wheels/*.whl
cd ../..

# Ensure requirements.txt exists
if [ ! -f requirements.txt ]; then
    touch requirements.txt
fi
pip install -r requirements.txt

echo "✓ Build complete with performance optimizations"
echo "✓ TypeScript compilation complete"
