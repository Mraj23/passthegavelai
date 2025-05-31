import os


def get_directory_tree(root_path: str) -> str:
    """
    Walks the directory at `root_path` and returns a multiline string
    showing its tree. Directories appear on their own line; files are
    prefixed with "    | " at the correct indent level.

    Example output:
        my_folder
            | file1.txt
            | file2.py
            subdir1
                | nested.txt
        other_folder
            | another_file.md

    :param root_path: Path to the folder whose tree you want to generate.
    :return: A single string containing the directory tree (with newlines).
    """
    lines = []

    def _helper(curr_path: str, indent_level: int):
        name = os.path.basename(curr_path) or curr_path
        # Print the directory name at this level
        lines.append(" " * (4 * indent_level) + name)

        if os.path.isdir(curr_path):
            try:
                entries = sorted(os.listdir(curr_path))
            except PermissionError:
                # Skip directories we can't enter
                return

            for entry in entries:
                full_entry = os.path.join(curr_path, entry)
                if os.path.isdir(full_entry):
                    # Recurse on subdirectory (increase indent)
                    _helper(full_entry, indent_level + 1)
                else:
                    # Print file with a "| " prefix at this indent
                    prefix = " " * (4 * (indent_level + 1)) + "| "
                    lines.append(prefix + entry)

    # Start recursion at indent_level=0
    _helper(root_path, 0)
    return "\n".join(lines)
