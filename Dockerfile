FROM nixos/nix

RUN nix-channel --update
RUN nix-env -if https://install.devenv.sh/latest

WORKDIR /gensql.structure-learning

CMD ["devenv", "shell"]
