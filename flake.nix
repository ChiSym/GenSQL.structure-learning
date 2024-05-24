{
  description = "A very basic flake";

  inputs = {
    nixpkgs.url = "github:cachix/devenv-nixpkgs/rolling";
    nixpkgs-python.url = "github:cachix/nixpkgs-python";
    systems.url = "github:nix-systems/default";
    devenv.url = "github:cachix/devenv";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
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
          ./devenv.nix
        ];
      };
    }
    );
  };
}
