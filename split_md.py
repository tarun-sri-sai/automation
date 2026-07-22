import logging
import marko
import os
import re
from argparse import ArgumentParser
from marko.block import Document, Heading
from marko.inline import RawText
from marko.md_renderer import MarkdownRenderer
from pathlib import Path


def _to_kebab_case(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text


def _extract_text(node: Document) -> str:
    if isinstance(node, RawText):
        return node.children
    if hasattr(node, "children"):
        children = node.children
        if isinstance(children, list):
            return "".join(_extract_text(child) for child in children)
    return ""


def _create_files(ast: Document) -> None:
    content_idx = -1
    directory_path = ""
    for i, node in enumerate(ast.children):
        if isinstance(node, Heading) and node.level == 1:
            directory_path = Path(_to_kebab_case(_extract_text(node)))
            os.makedirs(directory_path, exist_ok=True)

            content_idx = i
            break

    split_asts = []
    curr_ast = None
    for i, node in enumerate(ast.children[content_idx:]):
        if isinstance(node, Heading) and node.level == 2:
            curr_ast = Document()
            curr_ast.children = [node]
            split_asts.append(curr_ast)
        elif curr_ast is not None:
            curr_ast.children.append(node)
        else:
            logging.warning(
                f"skipping node at index {i} because a valid h2 as not been "
                "hit yet"
            )

    file_names = []
    for i, split_ast in enumerate(split_asts):
        file_name = ""
        for node in split_ast.children:
            if isinstance(node, Heading):
                node.level -= 1

                if node.level == 1:
                    file_name = _to_kebab_case(_extract_text(node))

        if not file_name:
            logging.warning(
                f"skipping ast at index {i} because it does not have a h1"
            )

        file_names.append(file_name)

    renderer = MarkdownRenderer()
    for i, file_name in enumerate(file_names):
        if not file_name:
            continue

        file_path = directory_path / f"{file_name}.md"

        logging.info(f"writing to file {file_path}")
        with open(file_path, "w") as f:
            f.write(renderer.render(split_asts[i]))


def _split_markdown(md_path: Path) -> None:
    logging.info(f"reading path {md_path}")
    text = md_path.read_text(encoding="utf-8")

    logging.info("parsing text as markdown")
    ast = marko.Markdown().parse(text)

    _create_files(ast)


def main() -> None:
    parser = ArgumentParser(description="split markdown files by headings")
    parser.add_argument(
        "file", type=Path, help="path to the input markdown file"
    )

    args = parser.parse_args()

    _split_markdown(args.file)


if __name__ == "__main__":
    main()
