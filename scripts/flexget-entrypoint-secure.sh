#!/bin/sh
umask 077
python3 - <<'FLEXGET_PATCHES' || printf '%s\n' 'FlexGet startup patches could not be loaded' >&2
from importlib.util import find_spec
from pathlib import Path
import os
import tempfile

package = Path(find_spec('flexget').origin).parent


def patch_source(relative_path, original, replacement):
    target = package / relative_path
    source = target.read_text(encoding='utf-8')
    if replacement in source:
        return
    if source.count(original) != 1:
        print(f'FlexGet startup patch could not locate code in {relative_path}')
        return

    patched = source.replace(original, replacement, 1)
    compile(patched, str(target), 'exec')
    with tempfile.NamedTemporaryFile(
        dir=target.parent, mode='w', encoding='utf-8', delete=False
    ) as temp:
        temp.write(patched)
        os.fchmod(temp.fileno(), 0o644)
    os.replace(temp.name, target)


# Telegram may take longer than five seconds to acknowledge document uploads.
builder = '            .proxy(self.socks_proxy)\n'
patch_source(
    'components/notify/notifiers/telegram.py',
    builder,
    builder + '            .read_timeout(30)\n',
)

# The bind-mounted plugin checkout also contains its test suite.
plugin_glob = "        for plugin_path in plugins_dir.glob('**/*.py'):\n"
patch_source(
    'plugin.py',
    plugin_glob,
    plugin_glob
    + "            if plugins_dir == Path('/config/plugins') and plugin_path.relative_to(plugins_dir).parts[0] == 'tests':\n"
    + "                continue\n",
)
FLEXGET_PATCHES
exec /usr/bin/entrypoint.sh "$@"
