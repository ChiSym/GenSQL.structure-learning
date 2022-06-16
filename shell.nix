{ pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/35a74aa665a681b60d68e3d3400fcaa11690ee50.tar.gz") {} }:

let
  python = pkgs.python39;
  pypkgs = pkgs.python39Packages;

  # DVC is currently broken on nixpkgs because the version of asyncssh is newer
  # than the version range required by DVC. Here we override asyncssh to use the
  # newest version allowed by DVC.
  # https://github.com/NixOS/nixpkgs/issues/157998
  dvc = let
    overriddenPython = let
      packageOverrides = self: super: {
        asyncssh = super.asyncssh.overridePythonAttrs(old: rec {
          version = "2.8.1";
          src = super.fetchPypi {
            pname = "asyncssh";
            inherit version;
            sha256 = "BkjrpY1yZTdV8o4myb2DFH2WUsHy9eh/v1qH1/j7+Do=";
          };
          doCheck = false;
        });
      };
    in python.override { inherit packageOverrides; self = overriddenPython; };
  in pkgs.dvc.override { python3 = overriddenPython; };

  edn-format = pypkgs.buildPythonPackage rec { # not in nixpkgs
    pname = "edn-format";
    version = "0.7.5";

    src = pkgs.fetchFromGitHub {
      owner = "swaroopch";
      repo = "edn_format";
      rev = "v0.7.5";
      sha256 = "sha256-DLAyrWQ/pbt8pl/b0Z9XiU+KHUeojUzj9DPzXJ3Ct+o=";
    };

    propagatedBuildInputs = with pypkgs; [
      ply
      pyRFC3339
      pytz
    ];
  };

  cgpm = pypkgs.buildPythonPackage rec { # not in nixpkgs
    pname = "cgpm";
    version = "0.1.3";

    src = pkgs.fetchFromGitHub {
      owner = "probcomp";
      repo = "cgpm";
      # head of 20200908-schaechtle-experimenting-porting-to-python3 branch
      rev = "96c15a90284f84ec426e4f06663559a0b41540d2";
      sha256 = "sha256-pEpnpPNOqWRXHZjekR8znvWrEFxmuae3hqVwu+X4pt8=";
    };

    propagatedBuildInputs = with pypkgs; [
      future
      numpy
      scikit-learn
      seaborn
      statsmodels
    ];

    # cgpm's setup.py uses git to determine the package version, but because the
    # source retrieved via pkgs.fetchFromGitHub is not a git repository this
    # will fail. As a workaround we patch setup.py to hard-code the version
    # information.
    prePatch = ''
      substituteInPlace ./setup.py --replace \
        'pkg_version, full_version = get_version()' \
        'pkg_version, full_version = ("0.1.3", "0.1.3")'
    '';

    doCheck = false; # needs older version of pytest
  };

  sppl = pypkgs.buildPythonPackage rec { # not in nixpkgs
    pname = "sppl";
    version = "1.2.1";

    src = pypkgs.fetchPypi {
      inherit pname version;
      sha256 = "sha256-x47vrQeu96uCt+3ZfsVy80gTevOAILJIL2umEdkMCkM=";
    };

    propagatedBuildInputs = with pypkgs; [
      astunparse
      numpy
      scipy
      sympy
    ];

    checkInputs = with pypkgs; [
      coverage
      pytest
      pytestCheckHook
      pytest-timeout
    ];

    pytestFlagsArray = [ "--pyargs" "sppl" ];

    pipInstallFlags = [ "--no-deps" ];
  };

  pythonWithPackages = python.withPackages (pypkgs: [
    cgpm
    edn-format
    sppl
    pypkgs.black
    pypkgs.jsonschema
    pypkgs.matplotlib
    pypkgs.numpy
    pypkgs.pandas
  ]);
in pkgs.mkShell {
  buildInputs = [
    dvc
    pkgs.clojure
    pkgs.gh
    pkgs.git
    pkgs.openjdk11
    pkgs.parallel
    pkgs.xsv
    pkgs.yarn
    pythonWithPackages
  ];

  shellHook = "alias iql-query-server='clojure -X inferenceql.auto-modeling.query-server/run'; export PYTHONPATH=${pythonWithPackages}/${pythonWithPackages.sitePackages}";
}
