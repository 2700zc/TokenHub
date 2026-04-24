import subprocess
import shutil
import os

def clean():
    """Clean build and dist directories."""
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')

def build():
    """Build TokenHub executable."""
    clean()
    subprocess.run([
        'pyinstaller',
        '--onedir',
        '--noconsole',
        '--name', 'TokenHub',
        '--clean',
        'src/main.py'
    ], check=True)
    print('Build complete. Check dist/TokenHub/')

if __name__ == '__main__':
    build()