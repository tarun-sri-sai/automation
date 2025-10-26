import os
import sys
import subprocess
import shutil


def run_command(command, cwd=None):
    print(f"{cwd}> {command}")
    result = subprocess.run(command, cwd=cwd, shell=True, capture_output=True,
                            text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()


def main():
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python transfer_commits.py <src_repo> <dest_repo>\n"
              "                                  [<start_commit>]")
        sys.exit(1)

    src_repo = os.path.abspath(sys.argv[1])
    dest_repo = os.path.abspath(sys.argv[2])
    start_commit = sys.argv[3] if len(sys.argv) == 4 else None

    if not os.path.exists(dest_repo):
        run_command(f"git init", dest_repo)

    commits = run_command("git rev-list --reverse HEAD", src_repo).split("\n")

    if start_commit:
        if start_commit in commits:
            commits = commits[commits.index(start_commit):]
        else:
            print(f"Error: Start commit {start_commit} not found.")
            sys.exit(1)

    for commit in commits:
        run_command(f"git restore --source={commit} --worktree .", src_repo)
        commit_message = run_command(f"git log -1 --pretty=%B {commit}", src_repo)

        for item in os.listdir(src_repo):
            if item == ".git":
                continue
            src_path = os.path.join(src_repo, item)
            dest_path = os.path.join(dest_repo, item)
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
            else:
                shutil.copy2(src_path, dest_path)

        run_command("git add -A", dest_repo)
        run_command(f"git commit -m \"{commit_message}\"", dest_repo)

    run_command("git restore --source=HEAD --worktree .", src_repo)


if __name__ == "__main__":
    main()
