{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-23.11";

  outputs = { self, nixpkgs, ... }: let
    system = "aarch64-darwin";
    pkgs = nixpkgs.legacyPackages."${system}";
  in {
    devShells."${system}".default = pkgs.mkShell {
      buildInputs = with pkgs; [ (python3.withPackages (ps: with ps; [ duckdb ])) ];
    };
  };
}
