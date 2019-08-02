import subprocess
from argparse import ArgumentParser
from os import listdir
from os.path import isfile, join, splitext
from abc import ABCMeta, abstractmethod
from bs4 import UnicodeDammit


def get_file_content(file):
    with open(file, mode='rb') as stream:
        return stream.read()


def convert_file_to_utf8(file, from_encoding):
    tmp_file = file + '-tmp'
    execute_command('iconv --from-code={0} --to-code=UTF-8 "{1}" > "{2}"'.format(from_encoding, file, tmp_file))
    execute_command('rm "{0}"'.format(file))
    execute_command('mv "{0}" "{1}"'.format(tmp_file, file))


class Worker:
    __metaclass__ = ABCMeta

    @abstractmethod
    def do(self, file: str):
        raise NotImplementedError


class PrependPchWorker(Worker):
    def __init__(self, pch):
        self.__pch = pch

    def do(self, file: str):
        self.__prepend_pch(file, self.__pch)
        print('#include "stdafx.h" into', file)

    def __prepend_pch(self, file, pch):
        content = get_file_content(file)
        content = '#include "{0}"\n'.format(pch).encode('ascii') + content
        self.__write_content(file, content)

    @staticmethod
    def __write_content(file, content):
        with open(file, mode='wb') as stream:
            stream.write(content)


class ToUtf8Worker(Worker):
    def do(self, file: str):
        content = get_file_content(file)
        dammit = UnicodeDammit(content)

        if dammit.original_encoding != 'utf-8':
            print('Encode', file, 'to utf-8')
            convert_file_to_utf8(file, dammit.original_encoding)


def execute_command(command):
    print(command)
    return subprocess.run(command, shell=True, capture_output=True)


def get_all_files(path, extensions, to_exclude_dirs=[], to_exclude_files=[]):
    all_files = []
    all_subdirectories = []

    try:
        for f in listdir(path):
            full_path = join(path, f)
            is_file = isfile(full_path)
            _, file_extension = splitext(full_path)

            stripped_file_extension = file_extension.strip(".")

            extension_available = not extensions or stripped_file_extension in extensions

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

    # files selection settings
    parser.add_argument('--path', help='Path to the target directory')
    parser.add_argument('--extension', help='Target files extension')
    parser.add_argument('--dir_exclude', help='Directories to exclude from search')
    parser.add_argument('--file_exclude', help='File names to exclude')

    # commands
    parser.add_argument('--prepend_pch', help='Insert include for passed header file first for all selected files')
    parser.add_argument('--conv_to_utf8',
                        help='All selected files not in UTF-8 encoding will be converted to UTF-8',
                        action='store_true')

    return parser.parse_args()


def main():
    args = get_params()

    if not args.path:
        raise Exception('--path parameter not specified')

    workers = []

    if args.prepend_pch:
        workers.append(PrependPchWorker(args.prepend_pch))

    if args.conv_to_utf8:
        workers.append(ToUtf8Worker())

    if not workers:
        print('No command set. Nothing to do')
        return

    all_target_files = get_all_files(args.path,
                                     args.extension.split() if args.extension else [],
                                     args.dir_exclude.split() if args.dir_exclude else [],
                                     args.file_exclude.split() if args.file_exclude else [])

    for file in all_target_files:
        for worker in workers:
            worker.do(file)


if __name__ == '__main__':
    main()
