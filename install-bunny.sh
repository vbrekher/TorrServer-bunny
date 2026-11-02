#!/bin/sh
set -eu
# Download the versioned installer from this repository; does not need sudo.
command -v python3 >/dev/null 2>&1 || { echo 'Python 3 is required' >&2; exit 1; }
command -v curl >/dev/null 2>&1 || { echo 'curl is required' >&2; exit 1; }
BASE="https://raw.githubusercontent.com/vbrekher/TorrServer-bunny/master"
BIN_DIR="${HOME}/.local/bin"
SHARE="${HOME}/.local/share/torrserver-bunny"
mkdir -p "$BIN_DIR" "$SHARE"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT HUP INT TERM
curl -fsSL --retry 3 "$BASE/bunny/cli.py" -o "$TMP"
python3 -m py_compile "$TMP"
mv "$TMP" "$SHARE/cli.py"
cat > "$BIN_DIR/torrserver-bunny" <<'WRAPPER'
#!/bin/sh
exec python3 "${HOME}/.local/share/torrserver-bunny/cli.py" "$@"
WRAPPER
chmod 755 "$BIN_DIR/torrserver-bunny"
echo 'Installed ~/.local/bin/torrserver-bunny'
echo "If necessary, add $BIN_DIR to your PATH."
"$BIN_DIR/torrserver-bunny" setup
