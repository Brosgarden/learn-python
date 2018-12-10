# content of test_sample.py
import json

from github.repo import Repository, Branch


def test_branch():
    data = '''
      {
    "name": "remove-java8",
    "commit": {
      "sha": "28bfb7d3df849b4d591e88d0e7f63a02d6092902",
      "url": "https://api.github.com/repos/Brosgarden/learn-storm/commits/28bfb7d3df849b4d591e88d0e7f63a02d6092902"
    }
  }'''
    api_response = json.loads(data)
    branch = Branch(api_response)
    assert branch.name == "remove-java8"
    assert branch.commit_hash == "28bfb7d3df849b4d591e88d0e7f63a02d6092902"


def test_repo():
    data = '''
      {
    "id": 143317560,
    "node_id": "MDEwOlJlcG9zaXRvcnkxNDMzMTc1NjA=",
    "name": "brosgarden.github.io",
    "full_name": "Brosgarden/brosgarden.github.io",
    "private": false,
    "owner": {
      "login": "Brosgarden",
      "id": 6343550,
      "node_id": "MDQ6VXNlcjYzNDM1NTA=",
      "avatar_url": "https://avatars0.githubusercontent.com/u/6343550?v=4",
      "gravatar_id": "",
      "url": "https://api.github.com/users/Brosgarden",
      "html_url": "https://github.com/Brosgarden",
      "followers_url": "https://api.github.com/users/Brosgarden/followers",
      "following_url": "https://api.github.com/users/Brosgarden/following{/other_user}",
      "gists_url": "https://api.github.com/users/Brosgarden/gists{/gist_id}",
      "starred_url": "https://api.github.com/users/Brosgarden/starred{/owner}{/repo}",
      "subscriptions_url": "https://api.github.com/users/Brosgarden/subscriptions",
      "organizations_url": "https://api.github.com/users/Brosgarden/orgs",
      "repos_url": "https://api.github.com/users/Brosgarden/repos",
      "events_url": "https://api.github.com/users/Brosgarden/events{/privacy}",
      "received_events_url": "https://api.github.com/users/Brosgarden/received_events",
      "type": "User",
      "site_admin": false
    },
    "html_url": "https://github.com/Brosgarden/brosgarden.github.io",
    "description": null,
    "fork": false,
    "url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io",
    "forks_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/forks",
    "keys_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/keys{/key_id}",
    "collaborators_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/collaborators{/collaborator}",
    "teams_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/teams",
    "hooks_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/hooks",
    "issue_events_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/issues/events{/number}",
    "events_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/events",
    "assignees_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/assignees{/user}",
    "branches_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/branches{/branch}",
    "tags_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/tags",
    "blobs_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/git/blobs{/sha}",
    "git_tags_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/git/tags{/sha}",
    "git_refs_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/git/refs{/sha}",
    "trees_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/git/trees{/sha}",
    "statuses_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/statuses/{sha}",
    "languages_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/languages",
    "stargazers_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/stargazers",
    "contributors_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/contributors",
    "subscribers_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/subscribers",
    "subscription_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/subscription",
    "commits_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/commits{/sha}",
    "git_commits_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/git/commits{/sha}",
    "comments_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/comments{/number}",
    "issue_comment_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/issues/comments{/number}",
    "contents_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/contents/{+path}",
    "compare_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/compare/{base}...{head}",
    "merges_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/merges",
    "archive_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/{archive_format}{/ref}",
    "downloads_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/downloads",
    "issues_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/issues{/number}",
    "pulls_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/pulls{/number}",
    "milestones_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/milestones{/number}",
    "notifications_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/notifications{?since,all,participating}",
    "labels_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/labels{/name}",
    "releases_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/releases{/id}",
    "deployments_url": "https://api.github.com/repos/Brosgarden/brosgarden.github.io/deployments",
    "created_at": "2018-08-02T16:07:05Z",
    "updated_at": "2018-08-02T16:19:25Z",
    "pushed_at": "2018-08-02T16:19:24Z",
    "git_url": "git://github.com/Brosgarden/brosgarden.github.io.git",
    "ssh_url": "git@github.com:Brosgarden/brosgarden.github.io.git",
    "clone_url": "https://github.com/Brosgarden/brosgarden.github.io.git",
    "svn_url": "https://github.com/Brosgarden/brosgarden.github.io",
    "homepage": null,
    "size": 4,
    "stargazers_count": 0,
    "watchers_count": 0,
    "language": "Ruby",
    "has_issues": true,
    "has_projects": true,
    "has_downloads": true,
    "has_wiki": true,
    "has_pages": true,
    "forks_count": 0,
    "mirror_url": null,
    "archived": false,
    "open_issues_count": 0,
    "license": null,
    "forks": 0,
    "open_issues": 0,
    "watchers": 0,
    "default_branch": "master"
  }'''
    api_response = json.loads(data)
    repo = Repository(api_response)
    assert repo.name == "brosgarden.github.io"
    assert repo.clone_url == "https://github.com/Brosgarden/brosgarden.github.io.git"
    assert repo.ssh_url == "git@github.com:Brosgarden/brosgarden.github.io.git"
