import os
import subprocess
import argparse
from whoosh import index
from whoosh.fields import Schema, TEXT, ID, STORED
from whoosh.qparser import MultifieldParser
from whoosh.analysis import StandardAnalyzer


class GitRepoIndexer:
    def __init__(self, repos_dir, index_dir):
        self.repos_dir = os.path.abspath(repos_dir)
        self.index_dir = os.path.abspath(index_dir)

        self.schema = Schema(
            path=ID(stored=True),
            repo=ID(stored=True),
            content=TEXT(analyzer=StandardAnalyzer()),
            commit_hash=ID(stored=True),
            commit_date=STORED,
            commit_author=STORED
        )

        if not os.path.exists(self.index_dir):
            os.makedirs(self.index_dir)
            self.ix = index.create_in(self.index_dir, self.schema)
        else:
            try:
                self.ix = index.open_dir(self.index_dir)
            except:
                self.ix = index.create_in(self.index_dir, self.schema)

    def get_repo_list(self):
        """Get list of all directories that are Git repositories"""
        repos = []

        if os.path.exists(os.path.join(self.repos_dir, '.git')):
            repos.append(os.path.basename(self.repos_dir))
            print(f"Found Git repo: {os.path.basename(self.repos_dir)}")
            return repos

        for item in os.listdir(self.repos_dir):
            item_path = os.path.join(self.repos_dir, item)
            if os.path.isdir(item_path):
                if os.path.exists(os.path.join(item_path, '.git')):
                    repos.append(item)
                    print(f"Found Git repository: {item}")

        return repos

    def get_all_commits(self, repo_path):
        """Get all commit hashes in reverse chronological order"""
        try:
            actual_repo_path = repo_path
            if repo_path == os.path.basename(self.repos_dir) and os.path.exists(os.path.join(self.repos_dir, '.git')):
                actual_repo_path = self.repos_dir
            else:
                actual_repo_path = os.path.join(self.repos_dir, repo_path)

            result = subprocess.run(
                ['git', 'log', '--pretty=format:%H'],
                cwd=actual_repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode != 0:
                print(f"Error getting commits: {result.stderr}")
                return []

            commits = result.stdout.strip().split('\n')
            return [c for c in commits if c]
        except Exception as e:
            print(f"Error getting commits in {repo_path}: {e}")
            return []

    def get_commit_info(self, repo_path, commit_hash):
        """Get commit metadata"""
        try:
            actual_repo_path = repo_path
            if repo_path == os.path.basename(self.repos_dir) and os.path.exists(os.path.join(self.repos_dir, '.git')):
                actual_repo_path = self.repos_dir
            else:
                actual_repo_path = os.path.join(self.repos_dir, repo_path)

            result = subprocess.run(
                ['git', 'show', '-s', '--pretty=format:%an|%ad|%s', commit_hash],
                cwd=actual_repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode != 0 or not result.stdout:
                return None, None, None

            parts = result.stdout.split('|', 2)
            if len(parts) != 3:
                return None, None, None

            author, date, message = parts
            return author, date, message
        except Exception as e:
            print(
                f"Error getting info for commit {commit_hash} in {repo_path}: {e}")
            return None, None, None

    def get_commit_files(self, repo_path, commit_hash):
        """Get all files modified in a commit"""
        try:
            actual_repo_path = repo_path
            if repo_path == os.path.basename(self.repos_dir) and os.path.exists(os.path.join(self.repos_dir, '.git')):
                actual_repo_path = self.repos_dir
            else:
                actual_repo_path = os.path.join(self.repos_dir, repo_path)

            result = subprocess.run(
                ['git', 'diff-tree', '--no-commit-id',
                    '--name-only', '-r', commit_hash],
                cwd=actual_repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode != 0:
                return []

            files = result.stdout.strip().split('\n')
            return [f for f in files if f]
        except Exception as e:
            print(
                f"Error getting files for commit {commit_hash} in {repo_path}: {e}")
            return []

    def get_file_content_at_commit(self, repo_path, commit_hash, file_path):
        """Get content of a file at a specific commit"""
        try:
            actual_repo_path = repo_path
            if repo_path == os.path.basename(self.repos_dir) and os.path.exists(os.path.join(self.repos_dir, '.git')):
                actual_repo_path = self.repos_dir
            else:
                actual_repo_path = os.path.join(self.repos_dir, repo_path)

            result = subprocess.run(
                ['git', 'show', f'{commit_hash}:{file_path}'],
                cwd=actual_repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode != 0:
                return ""

            return result.stdout
        except Exception as e:
            print(
                f"Error getting content of {file_path} at commit {commit_hash} in {repo_path}: {e}")
            return ""

    def is_binary_file(self, repo_path, commit_hash, file_path):
        """Check if a file is binary"""
        try:
            actual_repo_path = repo_path
            if repo_path == os.path.basename(self.repos_dir) and os.path.exists(os.path.join(self.repos_dir, '.git')):
                actual_repo_path = self.repos_dir
            else:
                actual_repo_path = os.path.join(self.repos_dir, repo_path)

            result = subprocess.run(
                ['git', 'show', f'{commit_hash}:{file_path}'],
                cwd=actual_repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if result.returncode != 0:
                return True

            try:
                result.stdout.decode('utf-8')
                return False
            except UnicodeDecodeError:
                return True
        except Exception:
            return True

    def index_repos(self):
        """Index all text files in all commits of all repositories"""
        repos = self.get_repo_list()

        print(f"Found {len(repos)} repositories to index")
        if not repos:
            print(f"No Git repositories found in {self.repos_dir}")
            print("Make sure you're providing a directory that contains Git repositories")
            print("or a Git repository itself.")
            return

        total_files = 0

        with self.ix.writer() as writer:
            for repo in repos:
                print(f"Indexing repository: {repo}")

                commits = self.get_all_commits(repo)
                print(f"  Found {len(commits)} commits")

                if not commits:
                    print(f"  No commits found in repo {repo}, skipping...")
                    continue

                for i, commit_hash in enumerate(commits):
                    if i % 50 == 0:
                        print(
                            f"  Processing commit {i+1}/{len(commits)}: {commit_hash}")

                    author, date, _ = self.get_commit_info(
                        repo, commit_hash)
                    if not author:
                        continue

                    files = self.get_commit_files(repo, commit_hash)
                    for file_path in files:
                        if self.is_binary_file(repo, commit_hash, file_path):
                            continue

                        content = self.get_file_content_at_commit(
                            repo, commit_hash, file_path)
                        if not content:
                            continue

                        writer.add_document(
                            path=file_path,
                            repo=repo,
                            content=content,
                            commit_hash=commit_hash,
                            commit_date=date,
                            commit_author=author
                        )

                        total_files += 1
                        if total_files % 100 == 0:
                            print(f"  Indexed {total_files} files so far...")

        print(f"Indexing complete. Total files indexed: {total_files}")

    def search(self, query_string):
        """Search the index for the given query string"""
        with self.ix.searcher() as searcher:
            query_parser = MultifieldParser(
                ["content", "path", "commit_hash"], schema=self.ix.schema)
            query = query_parser.parse(query_string)

            results = searcher.search(query, limit=100)

            if len(results) == 0:
                print("No results found.")
                return

            print(f"Found {len(results)} results:")
            print("-" * 80)

            for i, hit in enumerate(results):
                print(f"{i+1}. Repository: {hit['repo']}")
                print(f"   File: {hit['path']}")
                print(f"   Commit: {hit['commit_hash']}")
                print(f"   Author: {hit['commit_author']}")
                print(f"   Date: {hit['commit_date']}")
                print("-" * 80)


def main():
    parser = argparse.ArgumentParser(
        description='Index and search Git repositories')
    parser.add_argument('--repos-dir', default='.',
                        help='Directory containing Git repositories')
    parser.add_argument('--index-dir', default='.search_index',
                        help='Directory to store the search index')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    subparsers.add_parser('index', help='Index repositories')

    search_parser = subparsers.add_parser(
        'search', help='Search indexed repositories')
    search_parser.add_argument('query', nargs='+', help='Search query terms')

    args = parser.parse_args()

    indexer = GitRepoIndexer(args.repos_dir, args.index_dir)

    if args.command == 'index':
        indexer.index_repos()
    elif args.command == 'search':
        indexer.search(' '.join(args.query))
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
