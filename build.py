import subprocess
import shutil
import os
import tempfile

CONFIG_FILE = os.path.join('dist', 'config.json')

def clean():
    """Clean build and dist directories, preserving the user's config.json."""
    user_cfg = None
    if os.path.exists(CONFIG_FILE):
        # Move the user's config aside so it survives the dist rebuild
        user_cfg = os.path.join(tempfile.gettempdir(), 'tokenhub_config_backup.json')
        try:
            shutil.move(CONFIG_FILE, user_cfg)
        except Exception:
            user_cfg = None

    if os.path.exists('build'):
        shutil.rmtree('build', ignore_errors=True)
    if os.path.exists('dist'):
        shutil.rmtree('dist', ignore_errors=True)

    # Put the user's config back into the fresh dist
    if user_cfg and os.path.exists(user_cfg):
        os.makedirs('dist', exist_ok=True)
        try:
            shutil.move(user_cfg, CONFIG_FILE)
        except Exception:
            pass

def build():
    """Build TokenHub executable."""
    clean()
    subprocess.run([
        'pyinstaller',
        '--onefile',
        '--noconsole',
        '--name', 'TokenHub',
        '--icon', 'icon.ico',
        '--clean',
        'src/main.py'
    ], check=True)
    print('Build complete. Check dist/TokenHub.exe')

if __name__ == '__main__':
    build()