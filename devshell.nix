{ ... }:
{
  perSystem = { config, self', inputs', pkgs, system, ... }: 
  let
    inherit (pkgs) lib;

    python = pkgs.python310;

    nodejs = pkgs.nodejs_20;
    pnpm = (pkgs.runCommand "corepack-enable" { } ''
      mkdir -p $out/bin
      ${nodejs}/bin/corepack enable --install-directory $out/bin
    '');

    parallel = (pkgs.writeScriptBin "parallel" ''
      ${lib.getExe pkgs.parallel} --will-cite "$@"
    '');

    system-packages = (with pkgs; [
      awscli2
      parallel
      xsv

      clojure
      clj-kondo

      nodejs
      pnpm

      python
      poetry
    ]);

    linux-only-pkgs = lib.optionals pkgs.stdenv.isLinux (with pkgs; [
      libgcc
      libz
      stdenv.cc.cc
    ]);

    darwin-only-pkgs = lib.optionals pkgs.stdenv.isDarwin (with pkgs; [
      darwin.apple_sdk.frameworks.CoreText
    ]);

    packages = builtins.concatLists [
      system-packages
      linux-only-pkgs
      darwin-only-pkgs
    ];

    lib-path = pkgs.lib.makeLibraryPath packages;
  in
  {
    devShells.default = pkgs.mkShell {
      inherit packages;

      shellHook = ''
        export LD_LIBRARY_PATH="${lib-path}:$LD_LIBRARY_PATH"

        pnpm install

        poetry config virtualenvs.path $(pwd)/.venv
        poetry env use ${python}/bin/python

        # We need to set PYTHON_KEYRING_BACKEND to use the null backend as
        # `poetry install` will hang waiting for the keyring access on some
        # distros
        PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring \
        poetry install --no-root
        export PATH="$(poetry env info -p)/bin:$PWD/bin:$PATH"
        
        mkdir -p .dvc/cache
        dvc cache dir .dvc/cache
      '';
    };
  };
}
