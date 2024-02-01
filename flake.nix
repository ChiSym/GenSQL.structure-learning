{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-23.11";

  outputs = { self, nixpkgs }: let
    system = "aarch64-darwin";
    pkgs = (import nixpkgs { inherit system; });

    stage = "sppl-merge";
    region = "us-east-2";
    hash = builtins.readFile (pkgs.runCommand "hash" {
      buildInputs = with pkgs; [ yq ];
      src = ./.;
    } ''
      yq -j '.stages.["sppl-merge"].outs[0].md5' $src/dvc.lock > $out
    '');

    s3-prefix = builtins.readFile (pkgs.runCommand "dvc" {
      nativeBuildInputs = with pkgs; [ dvc ];
      src = ./.;
    } ''
      cd $src
      dvc config remote.$(dvc config core.remote).url > $out
      truncate -s -1 $out
    '');

    url = "${s3-prefix}/files/md5/${builtins.substring 0 2 hash}/${builtins.substring 2 (builtins.stringLength hash) hash}?region=${region}";

    # file = builtins.fetchurl {
    #   url = url;
    #   sha256 = "";
    # };

    file = (pkgs.runCommand "file" {
      nativeBuildInputs = with pkgs; [ awscli2 ];
      outputHashAlgo = "sha256";
      outputHashMode = "recursive";
      outputHash = "sha256-Om4BcXK76QrExnKcDzw574l+h75C8yK/EbccpbcvLsQ=";
    } ''
    '');
    test = pkgs.runCommand "test" {} ''echo "${s3-prefix}" > $out'';
    buildInputs = with pkgs; [ yq ];
  in {
    inherit file hash s3-prefix test url;
    devShells."${system}".default = pkgs.mkShell {
      buildInputs = with pkgs; [ dvc yq awscli2 ];
    };
  };
}
