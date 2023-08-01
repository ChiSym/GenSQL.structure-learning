{
  inputs = {
    nixpkgs-nixos-21.url = "github:NixOS/nixpkgs/nixos-21.11";
    nixpkgs-darwin-21.url = "github:NixOS/nixpkgs/nixpkgs-21.11-darwin";
    nixpkgs-nixos-22.url = "github:NixOS/nixpkgs/nixos-22.05";
    nixpkgs-darwin-22.url = "github:NixOS/nixpkgs/nixpkgs-22.05-darwin";
    nixpkgs-unstable-pin.url = "github:NixOS/nixpkgs/35a74aa665a681b60d68e3d3400fcaa11690ee50";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self
    , nixpkgs-nixos-21
    , nixpkgs-darwin-21
    , nixpkgs-nixos-22
    , nixpkgs-darwin-22
    , nixpkgs-unstable-pin
    , flake-utils
  }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        hostPlatform = nixpkgs-nixos-21.legacyPackages.${system}.hostPlatform;

        pkgs = (if hostPlatform.isDarwin
                then nixpkgs-darwin-21
                else nixpkgs-nixos-21)
          .legacyPackages.${system};

        clj-kondo = (if hostPlatform.isDarwin
                     then nixpkgs-darwin-22
                     else nixpkgs-nixos-21)
          .legacyPackages.${system}.clj-kondo;

        dvc = let
          dvcPython = nixpkgs-unstable-pin.legacyPackages.${system}.python39;
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
          in dvcPython.override { inherit packageOverrides; self = overriddenPython; };
        in nixpkgs-unstable-pin.legacyPackages.${system}.dvc.override { python3 = overriddenPython; };

        python = pkgs.python39;

        pythonWithPackages = python.withPackages (pypkgs: let
          cgpm = pypkgs.buildPythonPackage rec { # not in nixpkgs
            pname = "cgpm";
            version = "0.1.3";

            src = pkgs.fetchFromGitHub {
              owner = "probcomp";
              repo = "cgpm";
              # head of 20200908-schaechtle-experimenting-porting-to-python3 branch
              rev = "026e3ce23b35df1981f52120b46650ec8d45b011";
              sha256 = "sha256-H34vEeRfs+xmFCx0/FqOGTBkGcSrwSEOg9i4dxYZ3nQ=";
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

          sppl = pypkgs.buildPythonPackage rec { # not in nixpkgs
            pname = "sppl";
            version = "2.0.4";

            src = pypkgs.fetchPypi {
              inherit pname version;
              sha256 = "sha256-QAp77L8RpN86V4O8F1zNA8O/szm9hNa4wWFT13av6BE=";
            };

            propagatedBuildInputs = with pypkgs; [
              astunparse
              numpy
              scipy
              sympy
            ];

            prePatch = ''
            substituteInPlace ./src/poly.py --replace \
              'from sympy.calculus.util import limit' \
              'from sympy import limit'
            substituteInPlace ./src/transforms.py --replace \
              'from sympy.calculus.util import limit' \
              'from sympy import limit'
            '';


            checkInputs = with pypkgs; [
              coverage
              pytest
              pytestCheckHook
              pytest-timeout
            ];

            pytestFlagsArray = [ "--pyargs" "sppl" ];

            pipInstallFlags = [ "--no-deps" ];
          };

        in [
          cgpm
          edn-format
          sppl
          pypkgs.black
          pypkgs.boto3
          pypkgs.catboost
          pypkgs.jsonschema
          pypkgs.matplotlib
          pypkgs.numpy
          pypkgs.pandas
          pypkgs.pytest
          pypkgs.pyyaml
          pypkgs.s3fs
        ]);
      in {
        devShell = pkgs.mkShell {
          buildInputs = [
            clj-kondo
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

          shellHook = ''
            if [[ $- == *i* ]]
            then
                dvc () {
                    clojure -M bin/git-init.clj;
                    command dvc "$@";
                }
            fi
            alias iql-query-server='clojure -X inferenceql.auto-modeling.query-server/run';
            export PYTHONPATH=${pythonWithPackages}/${pythonWithPackages.sitePackages};
          '';
        };
      }
    );
}
