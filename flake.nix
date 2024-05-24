{
  description = "A very basic flake";

  inputs = {
    nixpkgs.url = "github:cachix/devenv-nixpkgs/rolling";
    nixpkgs-python.url = "github:cachix/nixpkgs-python";
    systems.url = "github:nix-systems/default";
    devenv.url = "github:cachix/devenv";
  };

  nixConfig = {
    extra-trusted-public-keys =
      "devenv.cachix.org-1:w1cLUi8dv3hnoSPGAuibQv+f9TZLr6cv/Hm9XgU50cw=";
    extra-substituters = "https://devenv.cachix.org";
  };

  outputs = { self, nixpkgs, devenv, systems, ... }@inputs:
  let
    forEachSystem = nixpkgs.lib.genAttrs (import systems);
  in
  {
    devShells = forEachSystem (system:
    let
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      default = devenv.lib.mkShell {
        inherit inputs pkgs;

        modules = [
          ({ pkgs, config, ... }: 
          let 
            inherit (pkgs) lib;
          in
          {
            packages = let
              system-packages = (with pkgs; [
                awscli2
                clj-kondo
                parallel
                xsv
                duckdb
                giflib
                cairo
                pango
              ]);

              python-packages = (with config.languages.python.package.pkgs; [
                setuptools
                numpy
                pandas
                scipy
                duckdb
              ]);

              linux-only-pkgs = lib.optionals pkgs.stdenv.isLinux (with pkgs; [
                libgcc
              ]);

              darwin-only-pkgs = lib.optionals pkgs.stdenv.isDarwin (with pkgs; [
                darwin.apple_sdk.frameworks.CoreText
              ]);
            in system-packages ++ python-packages ++ linux-only-pkgs ++ darwin-only-pkgs;

            languages.clojure.enable = true;

            languages.javascript = {
              enable = true;
              corepack.enable = true;
            };

            languages.python = {
              enable = true;
              version = "3.10.12";
              poetry = {
                enable = true;
                install = {
                  enable = true;
                  allExtras = true;
                };
                activate.enable = true;
              };
            };

            enterShell = ''
                pnpm install
                export PYTHONPATH=$PWD/.venv/lib/python3.10/site-packages:$PYTHONPATH
                parallel () {
                command parallel --will-cite "$@";
                }
            '';
          })
        ];
      };
    }
    );
  };
}
