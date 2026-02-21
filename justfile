set quiet
set shell := ["bash", "-cu"]

# ----------------------- #
# Paths / constants

_reg := "ghcr.io"

# ----------------------- #

# Default fallback
_default:
    just --list

# Login to the registry.
_login:
    echo $(gh auth token) | docker login {{ _reg }} -u dummy --password-stdin

# ----------------------- #

# Build the bundle.
[working-directory("bundle")]
[arg("publish", long, short="p", help="Publish the bundle", value="true")]
build publish="false":
    porter build

    if {{ publish }}; then \
        just publish; \
    fi


# Publish the bundle.
[working-directory("bundle")]
publish: _login
    porter publish
    porter publish --tag latest --force