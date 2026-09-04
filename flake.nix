{
  description = "Python development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };

      python = pkgs.python312;

      libraries = with pkgs; [
        stdenv.cc.cc.lib
        zlib
      ];
    in {
      devShells.${system}.default = pkgs.mkShell {
        packages = [
          python
          pkgs.uv
        ];

        LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath libraries;

        UV_PYTHON = "${python}/bin/python";
        UV_PYTHON_DOWNLOADS = "never";
      };
    };
}