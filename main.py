import github.repo


def print_header(header_name):
    print("====== {0} ======".format(header_name))


def main():
    user = 'brosgarden'
    repositories = github.repo.get_repos(user)
    print_header("Repositories")
    for repo in repositories:
        print_header(repo.name)
        repo.print_clone_urls()

        print("Branches")
        branches = github.repo.list_branches(user, repo)
        for branch in branches:
            branch.print_info()
        print()


if __name__ == '__main__':
    main()
