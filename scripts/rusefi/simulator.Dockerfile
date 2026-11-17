# Fallback env for building/running the 32-bit rusEFI simulator (base tune) when the host has no gcc-multilib.
# Used automatically by build_rusefi_core48.sh; CI installs gcc-multilib natively instead.
FROM ubuntu:24.04
RUN apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends make gcc-multilib g++-multilib python3 xxd git ca-certificates && rm -rf /var/lib/apt/lists/*
