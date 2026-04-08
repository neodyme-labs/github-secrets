import requests, logging, os, argparse
from datetime import datetime, timedelta
request_headers = {}

#############################CONFIG#############################
# Can be created here: https://github.com/settings/tokens
# Personal access tokens, no additional permissions required
github_account_token = os.getenv('GITHUB_ACCOUNT_TOKEN')
#############################CONFIG#############################

def get_trending_repos(count=100, days_back=365):
    """
    Fetches the most starred repositories created within the last X days.
    """
    repos = set()
    since_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    url = f"https://api.github.com/search/repositories"
    params = {
        'q': f'created:>{since_date}',
        'sort': 'stars',
        'order': 'desc',
        'per_page': count
    }
    
    logging.info(f"Fetching top {count} trending repos since {since_date}")
    
    try:
        response = requests.get(url, params=params, headers=request_headers)
        data = response.json()
        api_error_handling(data)
        items = data.get('items', [])

        if not items:
            print("No repositories found.")
            return

        for i, repo in enumerate(items, 1):
            repos.add(repo['full_name'])
        return repos
    except requests.exceptions.RequestException as e:
        print(f"Something went wrong: {e}")

def api_error_handling(api_response):
    if 'message' in api_response:
        logging.error(api_response['message'])
        os._exit(1)

def commit_print(repo, commits):
    for commit in commits:
        print(f"https://github.com/{repo}/commit/{commit}")

def pull_all_branches(repo):
    branches = []
    page = 1
    while True:
        url = f"https://api.github.com:443/repos/{repo}/branches?per_page=100&page={page}"
        data = requests.get(url, headers=request_headers)
        response_data = data.json()
        api_error_handling(response_data)
        if not response_data:
            break
        branches.extend(response_data)
        if len(response_data) < 100:
            break
        page += 1
    return branches

# Gets all commits from the events api endpoint, that have no commits attached and thus only overwrite the current head
def pull_all_pushevent_commits_from_events(repo):
    commits = set()
    page = 1
    # The /events endpoint caps at 300 events across 3 pages of 100.
    while True:
        url = f"https://api.github.com:443/repos/{repo}/events?per_page=100&page={page}"
        data = requests.get(url, headers=request_headers)
        response_data = data.json()
        # GitHub caps pagination on this endpoint and returns an error body
        # rather than an empty list once the cap is hit — treat it as "done".
        if isinstance(response_data, dict) and "pagination is limited" in response_data.get("message", ""):
            logging.warning(
                f"/events pagination cap reached for {repo} (GitHub hard-limits this endpoint to ~300 events); "
                "older force-pushed commits in this repo will not be detected. "
                "For deeper history, consider querying GH Archive (https://www.gharchive.org/)."
            )
            break
        api_error_handling(response_data)
        if not response_data:
            break
        for event in response_data:
            if event["type"] == "PushEvent":
                commits.add(event["payload"]["before"])
                commits.add(event["payload"]["head"])
        if len(response_data) < 100:
            break
        page += 1
    logging.info(f"Pulled {len(commits)} force-pushed commits from events")
    return commits

def commit_has_associated_pr(repo, commit):
    url = f"https://api.github.com/repos/{repo}/commits/{commit}/pulls"
    data = requests.get(url, headers=request_headers).json()
    api_error_handling(data)
    if data:
        return True

    # Fallback: search across all PRs in the repo that reference this SHA.
    # Catches squash/rebase merges and deleted branches.
    url = "https://api.github.com/search/issues"
    params = {"q": f"repo:{repo} type:pr {commit}"}
    resp = requests.get(url, params=params, headers=request_headers).json()
    api_error_handling(resp)
    return resp.get("total_count", 0) > 0

def find_dangling_commits(repo):
    probably_force_pushed_commits = set()
    repo_branches = pull_all_branches(repo)
    repo_pushevent_commits = pull_all_pushevent_commits_from_events(repo)
    for commit in repo_pushevent_commits:
        reachable = False
        for branch in repo_branches:
            url = f"https://api.github.com/repos/{repo}/compare/{branch['name']}...{commit}"
            data = requests.get(url, headers=request_headers)
            commit_diff = data.json()
            # "No common ancestor" is a legitimate 404 response meaning the
            # commit is not reachable from this branch — keep checking others.
            if isinstance(commit_diff, dict) and commit_diff.get("message", "").startswith("No common ancestor"):
                continue
            api_error_handling(commit_diff)
            # "identical" or "behind" means the commit is reachable from this branch
            if commit_diff["status"] in ("identical", "behind"):
                reachable = True
                break
        if not reachable and not commit_has_associated_pr(repo, commit):
            probably_force_pushed_commits.add(commit)

    if probably_force_pushed_commits:
        print(f"\nFound these commits in {repo}, which were probably force pushed and are not in the history anymore:")
        commit_print(repo,probably_force_pushed_commits)


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


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s")
    parser = argparse.ArgumentParser(description='Github Deleted Secrets Scanner')
    parser.add_argument('repository_or_account', nargs='?', help='Required repository or account (user/org) to scan (default format: account/repository, add -u or -o for just account name)')
    parser.add_argument('-u', '--user', action='store_true', help='Make the script scan all repositories of a user')
    parser.add_argument('-o', '--org', action='store_true', help='Make the script scan all repositories of an organization')
    parser.add_argument('-t', '--test', nargs='?', type=int, const=-1, default=None, help='Test the script by scanning trending repos. Optionally pass a number to limit the count. (default 100 repos)')
    parser.add_argument('-v', '--verbose', action='store_true',help='Make the script more verbose.')
    args = parser.parse_args()

    if args.test is None and not args.repository_or_account:
        parser.error("repository_or_account is required unless -t/--test is used")

    # Input validation
    if args.test is None and (args.user or args.org) and "/" in args.repository_or_account:
        logging.error("Account name cannot contain a slash! If you want to scan a specific repository, remove the -u/--user or -o/--org flag")
        os._exit(1)
    elif args.test is None and not (args.user or args.org) and "/" not in args.repository_or_account:
        logging.error("You only passed an account name. Add the -u/--user flag to scan all repos of a user, -o/--org flag to scan all repos of an organization, or use account/repository format to scan a single repo")
        os._exit(1)
    elif args.user and args.org:
        logging.error("You can't use both -u/--user and -o/--org flags at the same time")
        os._exit(1)

    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)
    if github_account_token:
        request_headers["Authorization"] = "Bearer " + github_account_token
        logging.info("Using the supplied API Token!")
    try:
        if args.test is not None:
            trending = get_trending_repos() if args.test == -1 else get_trending_repos(args.test)
            for repo in trending or []:
                logging.info(f"Searching force pushed commits in {repo}")
                find_dangling_commits(repo)
        elif args.user or args.org:
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
