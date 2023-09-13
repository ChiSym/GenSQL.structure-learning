FROM nixos/nix

RUN nix-channel --update
RUN nix-env -if https://install.devenv.sh/latest

WORKDIR /inferenceql.auto-modeling

CMD ["devenv", "shell"]
