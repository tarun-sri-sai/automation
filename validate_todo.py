import re
import git
from tabulate import tabulate
from argparse import ArgumentParser


def finalize(task, parent_done=False):
    if (
        parent_done or
        (
            task["comments"] and
            task["comments"][-1].startswith("[DONE] ")
        )
    ):
        task["done"] = True

    for sub in task["tasks"]:
        finalize(sub, parent_done=task["done"])


def is_section_title_block(block_text):
    lines = block_text.split("\n")
    if len(lines) < 3:
        return False

    first, *_, last = lines
    pattern = r"\*+"
    return (
        re.fullmatch(pattern, first.strip()) is not None and
        re.fullmatch(pattern, last.strip()) is not None
    )


def parse_todo_data(text):
    result = {"comments": [], "done": False, "tasks": []}

    blocks = [
        b
        for b in text.split("\n\n")
        if not is_section_title_block(b)
    ]

    parent_stack = [result]

    for block in blocks:
        lines = [l for l in block.split("\n") if l]

        indent = len(lines[0]) - len(lines[0].lstrip(" "))
        while indent // 4 + 1 < len(parent_stack):
            parent_stack.pop()

        task = {
            "comments": [line.strip() for line in lines],
            "done": False,
            "tasks": []
        }

        parent_stack[-1]["tasks"].append(task)
        parent_stack.append(task)

    for task in result["tasks"]:
        finalize(task)

    return result


def collect_tasks(task, acc, parents, task_checksums=None):
    if not task["comments"]:
        return

    if task_checksums is not None:
        task_checksum = hash(task["comments"][0])
        task_checksums[task_checksum] = task_checksums.get(task_checksum, 0) + 1

    checksum = hash("".join(parents) + task["comments"][0])
    acc[checksum] = {
        "done": task["done"],
        "comments": task["comments"]
    }

    for sub in task["tasks"]:
        collect_tasks(sub, acc, parents + [task["comments"][0]], task_checksums)


def load_todo_commits(repo):
    commits = list(reversed(list(repo.iter_commits(paths="to-do.txt"))))
    data = []

    for commit in commits:
        try:
            blob = commit.tree / "to-do.txt"
            content = blob.data_stream.read().decode()
            data.append({
                "commit": commit.hexsha[:7],
                "message": commit.message.strip(),
                "data": parse_todo_data(content)
            })
        except Exception:
            pass

    return data


def validate_todos(commit_data):
    for i in range(len(commit_data) - 1):
        current = {}
        nxt = {}
        current_tasks = {}
        next_tasks = {}

        for t in commit_data[i]["data"]["tasks"]:
            collect_tasks(t, current, [], current_tasks)

        for t in commit_data[i + 1]["data"]["tasks"]:
            collect_tasks(t, nxt, [], next_tasks)

        removed_undone = [
            {
                "comments": "\n".join(data["comments"]),
                "duplicate": hash(data["comments"][0]) in next_tasks
            }
            for checksum, data in current.items()
            if not data["done"] and checksum not in nxt
        ]

        if removed_undone:
            prev_commit = commit_data[i]['message']
            next_commit = commit_data[i + 1]['message']
            title = (
                "undone tasks removed between commits "
                f"{prev_commit} -> {next_commit}"
            )

            rows = [
                (
                    ("(Possibly moved)\n" if x["duplicate"] else "") +
                    x["comments"],
                ) for x in removed_undone
            ]

            print(tabulate(rows, headers=[title], tablefmt="grid"))
            print()


def main():
    parser = ArgumentParser(description="validate todo history using git commits")
    parser.add_argument("directory", type=str, help="path to git repo")
    args = parser.parse_args()

    repo = git.Repo(args.directory)
    commit_data = load_todo_commits(repo)

    if len(commit_data) < 2:
        print("not enough commits to validate")
        return

    validate_todos(commit_data)


if __name__ == "__main__":
    main()
