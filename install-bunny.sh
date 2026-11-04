#!/bin/sh
set -eu

# Resolve the exact GitHub commit first; never trust a cached master raw file.
command -v python3 >/dev/null 2>&1 || { echo 'Python 3 is required' >&2; exit 1; }
command -v curl >/dev/null 2>&1 || { echo 'curl is required' >&2; exit 1; }
REPO="vbrekher/TorrServer-bunny"
BIN_DIR="${HOME}/.local/bin"
SHARE="${HOME}/.local/share/torrserver-bunny"
mkdir -p "$BIN_DIR" "$SHARE"

# GitHub's anonymous REST API can return 403 after rate limiting.
# Resolve the immutable master SHA via Git smart HTTP instead; no GitHub API
# request, authentication token, or JSON parsing is required.
REV=""
if command -v git >/dev/null 2>&1; then
  REMOTE_LINE="$(GIT_TERMINAL_PROMPT=0 git -c http.lowSpeedLimit=1 -c http.lowSpeedTime=15 \
    ls-remote --heads "https://github.com/${REPO}.git" refs/heads/master 2>/dev/null || true)"
  REV="$(printf '%s\n' "$REMOTE_LINE" | awk '$2 == "refs/heads/master" { print $1; exit }')"
  if ! printf '%s' "$REV" | grep -Eq '^[0-9a-f]{40}$'; then
    REV=""
  fi
fi

if [ -n "$REV" ]; then
  echo "Downloading TorrServer CLI at verified Git commit: $REV"
  SOURCE_URL="https://raw.githubusercontent.com/${REPO}/${REV}/bunny/cli.py"
  SOURCE_LABEL="$REV"
else
  # Fallback for systems without git or where smart HTTP cannot connect.
  # The cache-busting query avoids previously observed stale master responses;
  # feature/build verification below will reject an outdated CLI before install.
  NONCE="$(date +%s)-$$"
  echo "Git revision lookup unavailable; downloading fresh master with mandatory CLI validation."
  SOURCE_URL="https://raw.githubusercontent.com/${REPO}/master/bunny/cli.py?cache_bust=${NONCE}"
  SOURCE_LABEL="master (cache-busted, build-checked)"
fi

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT HUP INT TERM
if ! curl -fsSL --retry 3 "$SOURCE_URL" -o "$TMP"; then
  echo 'Could not download the CLI from GitHub. Existing local installation left unchanged.' >&2
  echo 'If GitHub temporarily returns HTTP 403/429, check connectivity or retry after the limit resets.' >&2
  exit 1
fi

# Verify presence of the regression fix BEFORE overwriting the installed CLI.
python3 - "$TMP" <<'PY'
import pathlib,sys
source=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
required=('2026-11-04-watchdog-route-diagnostics', 'def registry_ids(', "def ensure_registry(", "'/mc/registries/digest'", 'def activity_status(', 'def activity_snapshot(', 'def activity_probe(')
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

echo "Installed ~/.local/bin/torrserver-bunny (source: $SOURCE_LABEL)"
echo "If necessary, add $BIN_DIR to your PATH."
# Use "doctor" for read-only post-500 diagnosis; default remains interactive setup.
if [ "$#" -eq 0 ]; then set -- setup; fi
"$BIN_DIR/torrserver-bunny" "$@"
