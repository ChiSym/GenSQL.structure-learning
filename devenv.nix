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
      nodePackages.vega-lite
      nodePackages.vega-cli
    ];
    python-packages = with config.languages.python.package.pkgs; [
      numpy
      pandas
      scipy
      duckdb
    ];
  in system-packages ++ python-packages;

  enterShell = ''
    pnpm install
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
      activate.enable = true;
    };
  };
}
