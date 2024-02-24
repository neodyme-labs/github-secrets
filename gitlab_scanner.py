import requests, logging, os, argparse

#############################CONFIG#############################
# Can be created here: https://gitlab.com/-/user_settings/personal_access_tokens
# Personal access token requires `read_api` scope
gitlab_access_token = os.getenv('GITLAB_ACCOUNT_TOKEN')
# For example https://gitlab.com for the public instance
gitlab_instance_url = os.getenv('GITLAB_INSTANCE_URL', default="https://gitlab.com")
#############################CONFIG#############################

def elements_not_in_list(search_from, search_in):
    return [x for x in search_from if x not in search_in]

def elements_in_list(search_from, search_in):
    return [x for x in search_from if x in search_in]

def commit_print(repo, commits):
    for commit in commits:
        print(f"{gitlab_instance_url}/{repo_id}/-/commit/{commit}")

def repository_id_from_name(project:str, repo:str) -> int:
    url = f"{gitlab_instance_url}/api/v4/projects/{project}%2f{repo}?simple=true"
    data = requests.get(url, headers=request_headers)
    datajson = data.json()
    id = datajson['id']
    logging.info(f"Got id {id} for {project}/{repo}")
    return id

def get_all_commits(repo_id:int) -> list[str]:
    url = f"{gitlab_instance_url}/api/v4/projects/{repo_id}/repository/commits?all=true" # doesn't work, doesn't show dangling commits even if they can still got directly
    data = requests.get(url, headers=request_headers)
    datajson = data.json()

# # Pulls the maximal amount of commits from the history with a starting commit SHA1
# def pull_commits(repo_id, start_commit, already_known_commits):
#     initial_count = len(already_known_commits)
#     stop = False
#     start = start_commit
#     while not stop:
#         url = f"{gitlab_instance_url}/repos/{repo_id}/commits?per_page=100&sha={start}"
#         data = requests.get(url, headers=request_headers)
#         json_data = data.json()
#         if len(json_data) == 1 and json_data[0]['sha'] in already_known_commits:
#             stop = True
#         else:
#             for commit in json_data:
#                 if commit['sha'] in already_known_commits:
#                     stop = True
#                 else:
#                     already_known_commits.add(commit['sha'])
#         start = json_data[-1]['sha']
#     logging.info(f"Pulled {len(already_known_commits) - initial_count} commits")

# # Iterates over all publicly available branches, and queries all commits of each branch
# def pull_all_commits_from_all_branches(repo_id):
#     commits = set()
#     url = f"{gitlab_instance_url}/repos/{repo_id}/branches"
#     data = requests.get(url, headers=request_headers)
#     for branch in data.json():
#         logging.info(f"Pulling all commits for branch {branch['name']}")
#         pull_commits(repo, branch['commit']['sha'],commits)
#     logging.info(f"Pulled {len(commits)} from all branches")
#     return commits

# # Gets all commits from the events api endpoint, that have no commits attached and thus only overwrite the current head
# def pull_all_force_pushed_commits_from_events(repo_id):
#     commits = set()
#     url = f"{gitlab_instance_url}/repos/{repo_id}/events"
#     data = requests.get(url, headers=request_headers)
#     for event in data.json():
#         if event["type"] == "PushEvent":
#             if len(event["payload"]["commits"]) == 0:
#                 commits.add(event["payload"]["before"])
#     logging.info(f"Pulled {len(commits)} force-pushed commits from events")
#     return commits

# # Gets all pushed commits available from the events api endpoint
# def pull_all_commits_from_events(repo_id):
#     commits = set()
#     url = f"{gitlab_instance_url}/repos/{repo_id}/events"
#     data = requests.get(url, headers=request_headers)
#     for event in data.json():
#         if event["type"] == "PushEvent":
#             for commit in event["payload"]["commits"]:
#                 commits.add(commit['sha'])
#     logging.info(f"Pulled {len(commits)} commits from events")
#     return commits

# def find_dangling_commits(repo_id):
#     historic_commits = pull_all_commits_from_all_branches(repo_id)
#     force_pushed_commits = pull_all_force_pushed_commits_from_events(repo_id)
#     event_commits = pull_all_commits_from_events(repo_id)
#     missing_history_commits = elements_not_in_list(event_commits, historic_commits)
#     probably_force_pushed_commits = elements_in_list(missing_history_commits,force_pushed_commits)
#     if probably_force_pushed_commits:
#         print("\nFound these commits, which were probably force pushed and are not in the history anymore:")
#         commit_print(repo,probably_force_pushed_commits)

#     dangling_commits = elements_not_in_list(missing_history_commits, probably_force_pushed_commits)
#     if dangling_commits:
#         print("\nFound these dangling commits, which were in the eventlog and are not in the history anymore:")
#         commit_print(repo,dangling_commits)
#     if not probably_force_pushed_commits and not dangling_commits:
#         print("\nFound no dangling commits")

if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s")
    parser = argparse.ArgumentParser(description='Github Deleted Secrets Scanner')
    parser.add_argument('project',help='Required project')
    parser.add_argument('repository',help='Required repository to scan')
    parser.add_argument('-v', '--verbose', action='store_true',help='Make the script more verbose.')
    args = parser.parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.ERROR)
    request_headers = {}

    if gitlab_access_token:
        request_headers["Authorization"] = "Bearer " + gitlab_access_token
        logging.info("Using the supplied API Token!")
    try:
        repo_id = repository_id_from_name(args.project, args.repository)
        find_dangling_commits(repo_id)
    except Exception as e:
        logging.exception(e)

        # data = requests.get("https://api.github.com/rate_limit", headers=request_headers)
        # json_data = data.json()
        # if int(json_data["rate"]["remaining"]) == 0:
        #     logging.error("You have reached your Github API limits. If you run this script without an API Token, you have to wait for an hour, before you can scan again or you provide an API token!")
        # else:
        #     logging.exception(e)
        