{
  description = "Structure learning pipeline";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-23.11";
  };

  outputs = inputs@{ self, nixpkgs }: let
    system = "aarch64-darwin";
    pkgs = (import nixpkgs { system = system; });
  in {
    packages.${system} = rec {

      subsample = pkgs.runCommand "subsampled.csv" {
        nativeBuildInputs = with pkgs; [ (python3.withPackages(ps: with ps; [ pandas pyyaml ])) ];
      } ''
        mkdir -p data/test
        python ${./scripts/subsample.py} \
          --data ${./data/data.csv} \
          --test-data-dir data/test \
          --params ${./params.yaml} \
          --output $out
      '';

      validated = pkgs.runCommand "validated.csv" { } ''
          if INVALID_COLUMNS=$(xsv headers -j ${subsample} | grep -v -E "^[0-9a-zA-Z_\-]+$")
          then
              printf 'Column names may only include alphanumeric characters, dashes, or underscores.\n\n'
              printf 'Invalid column names:\n\n%s\n' "$INVALID_COLUMNS"
              exit 1
          else
              cp ${subsample} $out
          fi
      '';

      clojure-home = pkgs.runCommand "clojure-home" {
        __noChroot = true;
        src = ./deps.edn;
        nativeBuildInputs = with pkgs; [ clojure git ];
      } ''
        mkdir -p $out
        cp $src ./deps.edn

        CLJ_CONFIG=$out/.clojure \
        GIT_SSL_CAINFO=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt \
        GITLIBS=$out/.gitlibs \
        JAVA_TOOL_OPTIONS="-Duser.home=$out" \
        clojure -P
      '';

      offline-clojure = pkgs.runCommand "offline-clojure" {
        nativeBuildInputs = with pkgs; [ makeWrapper ];
        buildInputs = with pkgs; [ clojure ];
      } ''
        mkdir -p $out/bin

        cp ${pkgs.clojure}/bin/clojure ./clojure
        patchShebangs clojure

        cp ./clojure $out/bin/clojure
        wrapProgram $out/bin/clojure \
          --set CLJ_CONFIG ${clojure-home}/.clojure \
          --set GITLIBS ${clojure-home}/.gitlibs \
          --set JAVA_TOOL_OPTIONS "-Duser.home=${clojure-home}"

        cp ${pkgs.clojure}/bin/clj ./clj
        patchShebangs clj

        cp ./clj $out/bin/clj
        wrapProgram $out/bin/clj \
          --set CLJ_CONFIG ${clojure-home}/.clojure \
          --set GITLIBS ${clojure-home}/.gitlibs \
          --set JAVA_TOOL_OPTIONS "-Duser.home=${clojure-home}"
      '';

      nullified = pkgs.runCommand "nullified.csv" {
        nativeBuildInputs = with pkgs; [ offline-clojure ];
        src = ./.;
      } ''
        cp -r $src/* ./
        clojure -X inferenceql.structure-learning.main/nullify \
          < ${validated} \
          > $out
      '';

      schema = pkgs.runCommand "schema.edn" {
        nativeBuildInputs = with pkgs; [ offline-clojure ];
        src = ./.;
      } ''
        cp -r $src/* ./
        clojure -X inferenceql.structure-learning.main/guess-schema \
          < ${nullified} \
          > $out
      '';

      cgpm-schema = pkgs.runCommand "cgpm-schema.edn" {
        nativeBuildInputs = with pkgs; [ offline-clojure ];
        src = ./.;
      } ''
        cp -r $src/* ./
        clojure -X inferenceql.structure-learning.main/guess-schema \
          < ${schema} \
          > $out
      '';

      ignored = pkgs.runCommand "ignored.csv" {
        nativeBuildInputs = with pkgs; [ offline-clojure ];
        src = ./.;
      } ''
        cp -r $src/* ./
        clojure -X inferenceql.structure-learning.main/ignore \
          :schema '"${schema}"' \
          < ${nullified} \
          > $out
      '';

    };
  };
}
