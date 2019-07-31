from argparse import ArgumentParser
from os import listdir
from os.path import isfile, join, splitext


def file_len(filename):
    i = 0

    with open(filename, errors="ignore") as f:
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

            if is_file and file_extension.strip(".") in extensions and f not in to_exclude_files:
                all_files.append(full_path)

            elif not is_file and f not in to_exclude_dirs:
                all_subdirectories.append(full_path)

    except FileNotFoundError:
        print("Unexpected error")

    for subdir in all_subdirectories:
        all_files += get_all_files(subdir, extensions, to_exclude_files=to_exclude_files)

    return all_files


def get_params():
    parser = ArgumentParser()
    parser.add_argument("--path", help="Path to the target directory")
    parser.add_argument("--ext", help="Target files extension")
    parser.add_argument("--exdirs", help="Directories to exclude from search")
    parser.add_argument("--exfiles", help="File names to exclude")
    return parser.parse_args()


def main():
    args = get_params()

    if not args.path:
        raise Exception("--path parameter not specified")

    if not args.ext:
        raise Exception("--ext parameter not specified")

    if not args.exdirs:
        raise Exception("--exdirs parameter not specified")

    all_target_files = get_all_files(args.path, args.ext, args.exdirs.split(" "), args.exfiles.split(" "))

    print(*all_target_files, sep="\n")
    print("Found", len(all_target_files), "files")


if __name__ == "__main__":
    main()
