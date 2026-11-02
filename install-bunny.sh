#!/bin/sh
set -eu

# Resolve the exact GitHub commit first; never trust a cached master raw file.
command -v python3 >/dev/null 2>&1 || { echo 'Python 3 is required' >&2; exit 1; }
command -v curl >/dev/null 2>&1 || { echo 'curl is required' >&2; exit 1; }
REPO="vbrekher/TorrServer-bunny"
BIN_DIR="${HOME}/.local/bin"
SHARE="${HOME}/.local/share/torrserver-bunny"
mkdir -p "$BIN_DIR" "$SHARE"

REV="$(curl -fsSL --retry 3 -H 'Accept: application/vnd.github+json' \
  "https://api.github.com/repos/${REPO}/commits/master" | \
  python3 -c 'import sys,json,re; s=json.load(sys.stdin).get("sha",""); sys.stdout.write(s if re.fullmatch(r"[0-9a-f]{40}",s) else "")')"
if [ -z "$REV" ]; then
  echo 'Could not resolve current GitHub commit; not installing an unverified version.' >&2
  exit 1
fi

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT HUP INT TERM
echo "Downloading TorrServer CLI at commit: $REV"
curl -fsSL --retry 3 \
  "https://raw.githubusercontent.com/${REPO}/${REV}/bunny/cli.py" -o "$TMP"

# Verify presence of the regression fix BEFORE overwriting the installed CLI.
python3 - "$TMP" <<'PY'
import pathlib,sys
source=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
required=('2026-11-02-registry-digest-verified', 'def registry_ids(', "def ensure_registry(", "'/mc/registries/digest'")
if not all(x in source for x in required) or "Several GHCR registries found" in source:
    sys.exit('Downloaded CLI does not contain the required registry fix; aborting before setup.')
print('Registry fix verified: current CLI loaded.')
PY

python3 -m py_compile "$TMP"
mv "$TMP" "$SHARE/cli.py"
chmod 600 "$SHARE/cli.py"

cat > "$BIN_DIR/torrserver-bunny" <<'WRAPPER'
#!/bin/sh
exec python3 "${HOME}/.local/share/torrserver-bunny/cli.py" "$@"
WRAPPER
chmod 755 "$BIN_DIR/torrserver-bunny"

echo "Installed ~/.local/bin/torrserver-bunny (source commit $REV)"
echo "If necessary, add $BIN_DIR to your PATH."
"$BIN_DIR/torrserver-bunny" setup
