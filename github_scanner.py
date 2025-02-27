import requests, logging, os, argparse

#############################CONFIG#############################
# Can be created here: https://github.com/settings/tokens
# Personal access tokens, no additional permissions required
github_account_token = os.getenv('GITHUB_ACCOUNT_TOKEN')
#############################CONFIG#############################

def elements_not_in_list(search_from, search_in):
    return [x for x in search_from if x not in search_in]

def elements_in_list(search_from, search_in):
    return [x for x in search_from if x in search_in]

def commit_print(repo, commits):
    for commit in commits:
        print(f"https://github.com/{repo}/commit/{commit}")

def api_error_handling(api_response):
    if 'message' in api_response:
        logging.error(api_response['message'])
        os._exit(1)

# Pulls the maximal amount of commits from the history with a starting commit SHA1
def pull_commits(repo, start_commit, already_known_commits):
    initial_count = len(already_known_commits)
    stop = False
    start = start_commit
    while not stop:
        url = f"https://api.github.com:443/repos/{repo}/commits?per_page=100&sha={start}"
        data = requests.get(url, headers=request_headers)
        api_error_handling(data.json())
        json_data = data.json()
        if len(json_data) == 1 and json_data[0]['sha'] in already_known_commits:
            stop = True
        else:
            for commit in json_data:
                if commit['sha'] in already_known_commits:
                    stop = True
                else:
                    already_known_commits.add(commit['sha'])
        start = json_data[-1]['sha']
    logging.info(f"Pulled {len(already_known_commits) - initial_count} commits")

# Iterates over all publicly available branches, and queries all commits of each branch
def pull_all_commits_from_all_branches(repo):
    commits = set()
    url = f"https://api.github.com:443/repos/{repo}/branches"
    data = requests.get(url, headers=request_headers)
    api_error_handling(data.json())
    for branch in data.json():
        logging.info(f"Pulling all commits for branch {branch['name']}")
        pull_commits(repo, branch['commit']['sha'],commits)
    logging.info(f"Pulled {len(commits)} from all branches")
    return commits

# Gets all commits from the events api endpoint, that have no commits attached and thus only overwrite the current head
def pull_all_force_pushed_commits_from_events(repo):
    commits = set()
    url = f"https://api.github.com:443/repos/{repo}/events"
    data = requests.get(url, headers=request_headers)
    api_error_handling(data.json())
    for event in data.json():
        if event["type"] == "PushEvent":
            if len(event["payload"]["commits"]) == 0:
                commits.add(event["payload"]["before"])
    logging.info(f"Pulled {len(commits)} force-pushed commits from events")
    return commits

def pull_all_repos(account, is_org=False):
    repos = []
    start_page = 1
    account_type = "orgs" if is_org else "users"
    
    while True:
        url = f"https://api.github.com:443/{account_type}/{account}/repos?per_page=100&page={start_page}"
        data = requests.get(url, headers=request_headers)
        api_error_handling(data.json())
        
        response_data = data.json()
        if not response_data:
            break
            
        for repo in response_data:
            repos.append(repo["name"])

        if len(response_data) == 100:
            start_page += 1
        else:
            break
            
    return repos

# Gets all pushed commits available from the events api endpoint
def pull_all_commits_from_events(repo):
    commits = set()
    url = f"https://api.github.com:443/repos/{repo}/events"
    data = requests.get(url, headers=request_headers)
    api_error_handling(data.json())
    for event in data.json():
        if event["type"] == "PushEvent":
            for commit in event["payload"]["commits"]:
                commits.add(commit['sha'])
    logging.info(f"Pulled {len(commits)} commits from events")
    return commits

def find_dangling_commits(repo):
    historic_commits = pull_all_commits_from_all_branches(repo)
    force_pushed_commits = pull_all_force_pushed_commits_from_events(repo)
    event_commits = pull_all_commits_from_events(repo)
    missing_history_commits = elements_not_in_list(event_commits, historic_commits)
    probably_force_pushed_commits = elements_in_list(missing_history_commits,force_pushed_commits)
    if probably_force_pushed_commits:
        print(f"\nFound these commits in {repo}, which were probably force pushed and are not in the history anymore:")
        commit_print(repo,probably_force_pushed_commits)

    dangling_commits = elements_not_in_list(missing_history_commits, probably_force_pushed_commits)
    if dangling_commits:
        print(f"\nFound these dangling commits in {repo}, which were in the eventlog and are not in the history anymore:")
        commit_print(repo,dangling_commits)
    if not probably_force_pushed_commits and not dangling_commits:
        print(f"\nFound no dangling commits in repository: {repo}")

if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s")
    parser = argparse.ArgumentParser(description='Github Deleted Secrets Scanner')
    parser.add_argument('repository_or_account',help='Required repository or account (user/org) to scan (default format: account/repository, add -u or -o for just account name)')
    parser.add_argument('-u', '--user', action='store_true', help='Make the script scan all repositories of a user')
    parser.add_argument('-o', '--org', action='store_true', help='Make the script scan all repositories of an organization')
    parser.add_argument('-v', '--verbose', action='store_true',help='Make the script more verbose.')
    args = parser.parse_args()

    # Input validation
    if (args.user or args.org) and "/" in args.repository_or_account:
        logging.error("Account name cannot contain a slash! If you want to scan a specific repository, remove the -u/--user or -o/--org flag")
        os._exit(1)
    elif not (args.user or args.org) and "/" not in args.repository_or_account:
        logging.error("You only passed an account name. Add the -u/--user flag to scan all repos of a user, -o/--org flag to scan all repos of an organization, or use account/repository format to scan a single repo")
        os._exit(1)
    elif args.user and args.org:
        logging.error("You can't use both -u/--user and -o/--org flags at the same time")
        os._exit(1)

    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.ERROR)
    request_headers = {}
    if github_account_token:
        request_headers["Authorization"] = "Bearer " + github_account_token
        logging.info("Using the supplied API Token!")
    try:
        if args.user or args.org:
            account_type = "organization" if args.org else "user"
            repos = pull_all_repos(args.repository_or_account, is_org=args.org)
            logging.info(f"Found {len(repos)} repos for {account_type} {args.repository_or_account}")
            for repo in repos:
                find_dangling_commits(f"{args.repository_or_account}/{repo}")
        else:
            find_dangling_commits(f"{args.repository_or_account}")

    except Exception as e:
        data = requests.get("https://api.github.com/rate_limit", headers=request_headers)
        json_data = data.json()
        if int(json_data["rate"]["remaining"]) == 0:
            logging.error("You have reached your Github API limits. If you run this script without an API Token, you have to wait for an hour, before you can scan again or you provide an API token!")
        else:
            logging.exception(e)
