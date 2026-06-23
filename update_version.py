import sys
import re

def main():
    if len(sys.argv) < 2:
        print("Usage: update_version.py <version>  (e.g. 1.2.0)")
        sys.exit(1)

    raw = sys.argv[1].strip()
    parts = raw.split('.')
    try:
        parts = [str(int(x)) for x in parts]
    except ValueError:
        print(f"[ERROR] Invalid version: {raw}")
        sys.exit(1)

    while len(parts) < 4:
        parts.append('0')
    parts = parts[:4]

    ver_tuple = ', '.join(parts)     # 1, 2, 0, 0
    ver_dot4  = '.'.join(parts)      # 1.2.0.0
    ver_short = '.'.join(parts[:3])  # 1.2.0

    with open('version_info.txt', 'r', encoding='utf-8') as f:
        txt = f.read()

    txt = re.sub(r'filevers=\([^)]+\)',  f'filevers=({ver_tuple})', txt)
    txt = re.sub(r'prodvers=\([^)]+\)',  f'prodvers=({ver_tuple})', txt)
    txt = re.sub(r"(StringStruct\(u'FileVersion',\s*u')[^']+'",    rf"\g<1>{ver_dot4}'",  txt)
    txt = re.sub(r"(StringStruct\(u'ProductVersion',\s*u')[^']+'", rf"\g<1>{ver_dot4}'",  txt)

    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(txt)

    with open('installer.iss', 'r', encoding='utf-8') as f:
        iss = f.read()

    iss = re.sub(r'#define AppVersion "[^"]*"', f'#define AppVersion "{ver_short}"', iss)

    with open('installer.iss', 'w', encoding='utf-8') as f:
        f.write(iss)

    with open('converter.py', 'r', encoding='utf-8') as f:
        code = f.read()

    code = re.sub(r'^VERSION\s*=\s*"[^"]*"', f'VERSION     = "{ver_short}"', code, flags=re.MULTILINE)

    with open('converter.py', 'w', encoding='utf-8') as f:
        f.write(code)

    print(f"Version: {ver_short}  (build: {ver_dot4})")

if __name__ == '__main__':
    main()
