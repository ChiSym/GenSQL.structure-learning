{ pkgs, config, ... }:

{
  # https://devenv.sh/packages/
  packages = let
    system-packages = with pkgs; [
      awscli2
      clj-kondo
      parallel
      xsv
      duckdb
      giflib
    ];
    python-packages = with config.languages.python.package.pkgs; [
      setuptools
      numpy
      pandas
      scipy
      duckdb
    ];
    linux-only-pkgs = if pkgs.stdenv.isLinux then with pkgs; [
      libgcc
    ] else [];
    darwin-only-pkgs = if pkgs.stdenv.isDarwin then with pkgs; [
    ] else [];
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
