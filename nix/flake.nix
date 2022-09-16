{
  inputs = {
    nixpkgs-nixos.url = "github:NixOS/nixpkgs/nixos-21.11";
    nixpkgs-darwin.url = "github:NixOS/nixpkgs/nixpkgs-21.11-darwin";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs-nixos, nixpkgs-darwin, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        nixpkgs = if nixpkgs-nixos.legacyPackages.${system}.hostPlatform.isDarwin
                  then nixpkgs-darwin
                  else nixpkgs-nixos;

        pkgs = nixpkgs.legacyPackages.${system};

        pythonPackages = pypkgs: with pypkgs; [sympy];
        python = pkgs.python39.withPackages(pythonPackages);
      in {
        devShell = pkgs.mkShell {
          buildInputs = [
            python
          ];
        };
      }
    );
}
