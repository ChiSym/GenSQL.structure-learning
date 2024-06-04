{
  description = "Description for the project";

  inputs = {
    flake-parts.url = "github:hercules-ci/flake-parts";
    flake-parts.inputs.nixpkgs-lib.follows = "nixpkgs";

    nixpkgs.url = "github:NixOS/nixpkgs?ref=nixos-23.05";

    systems.url = "github:nix-systems/default";

    lpm-fidelity.url = "github:InferenceQL/lpm.fidelity";
    lpm-discretize.url = "github:InferenceQL/lpm.discretize";
  };

  outputs = inputs@{ flake-parts, systems, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [ ./devshell.nix ];
      systems = import systems;
    };
}
