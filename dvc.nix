{ pkgs, src, ... }: {
  fetchDVCStageOutput = { stage }: let
    hash = builtins.readFile (pkgs.runCommand "hash" {
      buildInputs = with pkgs; [ yq ];
      inherit src;
    } ''
      yq -j '.stages.["sppl-merge"].outs[0].md5' $src/dvc.lock > $out
    '');

    s3-prefix = builtins.readFile (pkgs.runCommand "dvc" {
      nativeBuildInputs = with pkgs; [ dvc ];
      inherit src;
    } ''
      cd $src
      dvc config remote.$(dvc config core.remote).url > $out
      truncate -s -1 $out
    '');

    url = "${s3-prefix}/files/md5/${builtins.substring 0 2 hash}/${builtins.substring 2 (builtins.stringLength hash) hash}";
  in (pkgs.runCommand "output" {
    nativeBuildInputs = with pkgs; [ awscli2 ];
    # outputHashAlgo = "sha256";
    # outputHashMode = "recursive";
    # outputHash = "sha256-cKL9Wy87mMOHioqb4BHNn52caMzEaclCOLXAql/8WLc=";
  } ''
   cd /Users/zane/Desktop
   ls >> $out
   # aws s3 cp ${url} $out
  '');

}
