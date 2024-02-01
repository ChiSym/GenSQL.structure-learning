{ pkgs, modulesPath, ... }: {
  imports = [ "${modulesPath}/virtualisation/amazon-image.nix" ];

  environment.systemPackages = [
    (import (fetchTarball {
      url = https://install.devenv.sh/latest;
      sha256 = "0wj5455mk0kgm4vnvqia6x4qhkwwf3cn07pdsd4wmfdbp9rxr44a";
    })).packages.x86_64-linux.default
  ];
  programs.git.enable = true;
  virtualisation.docker.enable = true;

  system.stateVersion = "23.05";
}
