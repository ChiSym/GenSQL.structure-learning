# docker buildx create --use
## building an image for two platforms
# docker buildx build --platform=linux/amd64,linux/arm64 .

#docker build --platform linux/x86_64 -t autom:x86 .

FROM nixos/nix:latest

COPY . /tmp/build
WORKDIR /tmp/build

# This is required to build x86_64 images on a Mac M1.
ENV NIX_CONFIG="filter-syscalls = false"

RUN nix-channel --update && \
    nix-env -if https://install.devenv.sh/latest && \
    nix-collect-garbage -d

RUN devenv ci

RUN echo "DONE"

# FROM nixos/nix:latest AS builder

# # Copy our source and setup our working dir.
# COPY . /tmp/build
# WORKDIR /tmp/build

#     # Build our Nix environment
# RUN nix \
#     --extra-experimental-features "nix-command flakes" \
#     --option filter-syscalls false \
#     build

# # Copy the Nix store closure into a directory. The Nix store closure is the
# # entire set of Nix store values that we need for our build.
# RUN mkdir /tmp/nix-store-closure
# RUN cp -R $(nix-store -qR result/) /tmp/nix-store-closure

# # Final image is based on scratch. We copy a bunch of Nix dependencies
# # but they're fully self-contained so we don't need Nix anymore.
# FROM scratch

# WORKDIR /app

# # Copy /nix/store
# COPY --from=builder /tmp/nix-store-closure /nix/store
# COPY --from=builder /tmp/build/result /inferenceql.automodeling
