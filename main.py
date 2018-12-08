import github.repo


def print_header(header_name):
    print("====== {0} ======".format(header_name))


def do_other_thing():
    user = 'brosgarden'
    repositories = github.repo.get_repos(user)
    print_header("Repositories")
    for repo in repositories:
        print(repo.name)
        print(repo.clone_url)
        print(repo.ssh_url)

        print_header("Branches")
        branches = github.repo.list_branches(user, repo)
        for branch in branches:
            print("Branch: {0} - HEAD SHA: {1}".format(branch.name, branch.commit_hash))
        print()


if __name__ == '__main__':
    do_other_thing()
