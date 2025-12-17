import ast
import sys


def find_methods_calling_method(source_code: str, method_name: str):
    """
    Parses a Python class and returns method names that contain method_name.

    :param source_code: String containing Python source code.
    :param method_name: Name of the callee method.
    :return: List of method names calling method_name.
    """
    tree = ast.parse(source_code)
    target_methods = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for body_item in node.body:
                if isinstance(body_item, ast.FunctionDef):
                    # Get the source of the method body
                    method_code = ast.get_source_segment(
                        source_code,
                        body_item
                    )
                    if method_code and method_name in method_code:
                        target_methods.append(body_item.name)
    return sorted(set(target_methods))


def main():
    input_file = sys.argv[1] if len(sys.argv) > 1 else None
    with open(input_file or input("Python file: "), "r") as f:
        code = f.read()

    method_name = sys.argv[2] if len(sys.argv) > 2 else None
    methods = find_methods_calling_method(
        code,
        method_name or input("Method name: ")
    )
    print(*methods, sep="\n")


if __name__ == "__main__":
    main()
