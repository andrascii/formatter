import subprocess
from argparse import ArgumentParser
from os import listdir
from os.path import isfile, join, splitext


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

            extension_available = not extensions and not file_extension or \
                stripped_file_extension in extensions

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
    parser.add_argument('--extension', help='Target files extension')
    parser.add_argument('--dir_exclude', help='Directories to exclude from search')
    parser.add_argument('--file_exclude', help='File names to exclude')
    parser.add_argument('--prepend_pch', help='Insert include for passed header file first for all selected files')
    return parser.parse_args()


class PrependPchWorker:
    def __init__(self, target_files, pch):
        self.__target_files = target_files
        self.__pch = pch

    def do(self):
        for file in self.__target_files:
            self.__prepend_pch(file, self.__pch)
            print('Wrote to', file)

        print('Modified', len(self.__target_files), 'files')

    def __get_file_content(self, file):
        try:
            with open(file) as stream:
                return stream.read()

        except UnicodeDecodeError:
            charset = self.__get_file_charset(file)
            self.__convert_file_to_utf8(file, charset)

            with open(file) as stream:
                return stream.read()

    def __prepend_pch(self, file, pch):
        content = self.__get_file_content(file)
        content = '#include "{0}"\n'.format(pch) + content
        self.__write_content(file, content)

    @staticmethod
    def __write_content(file, content):
        with open(file, mode='w') as stream:
            stream.write(content)

    @staticmethod
    def __get_file_charset(file):
        result = execute_command('file -bi ' + file)
        # parse string like this one: type/x-c++; charset=cp1251
        _, charset = result.stdout.split(b';')
        charset_value = charset.split(b'=')
        return charset_value[1].strip().decode('ascii')

    @staticmethod
    def __convert_file_to_utf8(file, from_encoding):
        tmp_file = file + '-tmp'
        execute_command('iconv --from-code={0} --to-code=UTF-8 "{1}" > "{2}"'.format(from_encoding, file, tmp_file))
        execute_command('rm "{0}"'.format(file))
        execute_command('mv "{0}" "{1}"'.format(tmp_file, file))


def main():
    args = get_params()

    if not args.path:
        raise Exception('--path parameter not specified')

    if not args.extension:
        raise Exception('--extension parameter not specified')

    if not args.dir_exclude:
        raise Exception('--dir_exclude parameter not specified')

    if not args.prepend_pch:
        raise Exception('--prepend_pch parameter not specified but this is only option')

    all_target_files = get_all_files(args.path,
                                     args.extension.split(),
                                     args.dir_exclude.split(),
                                     args.file_exclude.split())

    worker = PrependPchWorker(all_target_files, args.prepend_pch)
    worker.do()


if __name__ == '__main__':
    main()
