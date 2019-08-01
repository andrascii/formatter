import subprocess
from argparse import ArgumentParser
from os import listdir
from os.path import isfile, join, splitext


def do(command):
    print(command)
    return subprocess.run(command, shell=True, capture_output=True)


def file_len(filename):
    i = 0

    with open(filename, errors='ignore') as f:
        for i, l in enumerate(f, 1):
            pass

    return i


def get_all_files(path, extensions, to_exclude_dirs=[], to_exclude_files=[]):
    all_files = []
    all_subdirectories = []

    try:
        for f in listdir(path):
            full_path = join(path, f)
            is_file = isfile(full_path)
            _, file_extension = splitext(full_path)

            extension_available = not extensions and not file_extension or \
                file_extension and file_extension.strip(".") in extensions

            if is_file and extension_available and f not in to_exclude_files:
                all_files.append(full_path)

            elif not is_file and f not in to_exclude_dirs:
                all_subdirectories.append(full_path)

    except FileNotFoundError:
        print('Unexpected error')

    for subdir in all_subdirectories:
        all_files += get_all_files(subdir, extensions, to_exclude_files=to_exclude_files)

    return all_files


def get_params():
    parser = ArgumentParser()
    parser.add_argument('--path', help='Path to the target directory')
    parser.add_argument('--ext', help='Target files extension')
    parser.add_argument('--exdirs', help='Directories to exclude from search')
    parser.add_argument('--exfiles', help='File names to exclude')
    return parser.parse_args()


def get_file_charset(file):
    result = do('file -bi ' + file)
    # parse string like this one: type/x-c++; charset=cp1251
    _, charset = result.stdout.split(b';')
    charset_value = charset.split(b'=')
    return charset_value[1].strip().decode('ascii')


def convert_file_to_utf8(file, from_encoding):
    tmp_file = file + '-tmp'
    do('iconv --from-code={0} --to-code=UTF-8 "{1}" > "{2}"'.format(from_encoding, file, tmp_file))
    do('rm "{0}"'.format(file))
    do('mv "{0}" "{1}"'.format(tmp_file, file))


def get_file_content(file):
    try:
        with open(file) as stream:
            return stream.read()

    except UnicodeDecodeError:
        charset = get_file_charset(file)
        convert_file_to_utf8(file, charset)

        with open(file) as stream:
            return stream.read()


def write_content(file, content):
    with open(file, mode='w') as stream:
        stream.write(content)


def prepend_stdafx(file):
    content = get_file_content(file)
    content = '#include "stdafx.h"\n' + content
    write_content(file, content)


def main():
    args = get_params()

    if not args.path:
        raise Exception('--path parameter not specified')

    if not args.ext:
        raise Exception('--ext parameter not specified')

    if not args.exdirs:
        raise Exception('--exdirs parameter not specified')

    all_target_files = get_all_files(args.path, args.ext, args.exdirs.split(" "), args.exfiles.split(" "))

    for file in all_target_files:
        prepend_stdafx(file)
        print('Wrote to', file)

    print('Modified', len(all_target_files), 'files')


if __name__ == '__main__':
    main()
