{
  description = "inferenceql.auto-modeling";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    devenv.url = "github:cachix/devenv";
    nix2container.url = "github:nlewo/nix2container";
    nix2container.inputs.nixpkgs.follows = "nixpkgs";
    mk-shell-bin.url = "github:rrbutani/nix-mk-shell-bin";
  };

  outputs = inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
        inputs.devenv.flakeModule
      ];

      systems = [ "x86_64-linux" "x86_64-darwin" "aarch64-darwin" ];

      perSystem = { config, self', inputs', pkgs, system, ... }: {
        devenv.shells.default = {
          name = "devenv";

          languages.clojure.enable = true;
          languages.javascript.corepack.enable = true;
          languages.javascript.enable = true;
          languages.python.enable = true;
          languages.python.poetry.activate.enable = true;
          languages.python.poetry.enable = true;

          pre-commit.hooks.black.enable = true;

          packages = with pkgs; [
            clj-kondo
            parallel
          ];

          enterShell = ''
            parallel () {
              command parallel --will-cite "$@";
            }
          '';
        };
      };

      flake = {
        # The usual flake attributes can be defined here, including system-
        # agnostic ones like nixosModule and system-enumerating ones, although
        # those are more easily expressed in perSystem.
      };
    };
}
