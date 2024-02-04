{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-23.11";

  outputs = { self, nixpkgs }: let
    system = "aarch64-darwin";
    pkgs = (import nixpkgs { inherit system; });
    dvc = (import ./dvc.nix { inherit pkgs; src = ./.; });
  in {
    packages."${system}".default = dvc.fetchDVCStageOutput { stage = "sppl-merge"; };

    devShells."${system}".default = pkgs.mkShell {
      buildInputs = with pkgs; [ awscli2 ];
    };
  };
}
