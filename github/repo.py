import requests


class Repository:
    def __init__(self, json):
        self.name = json['name']
        self.clone_url = json['clone_url']
        self.ssh_url = json['ssh_url']


class Branch:
    def __init__(self, json):
        self.name = json['name']
        self.commit_hash = json['commit']['sha']


class GitHubApiException(Exception):
    pass


def get_repos(user):
    response = __send_api_request("https://api.github.com/users/{0}/repos".format(user))
    repos = []
    for repo in response:
        repos.append(Repository(repo))
    return repos


def list_branches(user, repo):
    response = __send_api_request("https://api.github.com/repos/{0}/{1}/branches".format(user, repo.name))
    branches = []
    for branch in response:
        branches.append(Branch(branch))
    return branches


def __send_api_request(request_url):
    response = requests.get(request_url)
    if response.status_code != 200:
        print(response)
        raise GitHubApiException
