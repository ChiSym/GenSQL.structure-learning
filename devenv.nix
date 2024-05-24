{ pkgs, config, ... }:

let
  inherit (pkgs) lib;

  python = pkgs.python310.override {
    packageOverrides = final: prev: {
      psycopg2cffi = null;
    };
  };
in
{
  # https://devenv.sh/packages/
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

  enterShell = ''
    pnpm install
    export PYTHONPATH=$PWD/.venv/lib/python3.10/site-packages:$PYTHONPATH
    parallel () {
      command parallel --will-cite "$@";
    }
  '';

  # https://devenv.sh/languages/
  languages.clojure.enable = true;

  languages.javascript = {
    enable = true;
    corepack.enable = true;
  };

  languages.python = {
    enable = true;
    package = python;
    poetry = {
      enable = true;
      install = {
        enable = true;
        allExtras = true;
      };
      activate.enable = true;
    };
  };
}
