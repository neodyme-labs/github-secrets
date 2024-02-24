import requests, logging, os, argparse

#############################CONFIG#############################
# Can be created here: https://gitlab.com/-/user_settings/personal_access_tokens
# Personal access token requires `read_api` scope
gitlab_access_token = os.getenv('GITLAB_ACCOUNT_TOKEN')
# For example https://gitlab.com for the public instance
gitlab_instance_url = os.getenv('GITLAB_INSTANCE_URL', default="https://gitlab.com")
#############################CONFIG#############################


def commit_print(project:str, repository:str , commits: set[str]):
    for commit in commits:
        print(f"{gitlab_instance_url}/{project}/{repository}/-/commit/{commit}")

def get_repository_id_from_name(project:str, repository:str) -> int:
    url = f"{gitlab_instance_url}/api/v4/projects/{project}%2f{repository}?simple=true"
    data = requests.get(url, headers=request_headers)
    datajson = data.json()
    id = datajson['id']
    logging.info(f"Got id {id} for {project}/{repository}")
    return id

def get_all_commits(repo_id:int) -> set[str]:
    url = f"{gitlab_instance_url}/api/v4/projects/{repo_id}/events?action=pushed"
    data = requests.get(url, headers=request_headers)
    datajson = data.json()
    commits = set()
    for event in datajson:
        if event.get("push_data") and event.get("push_data").get("commit_from"):
            commits.add(event.get("push_data").get("commit_from"))
        if event.get("push_data") and event.get("push_data").get("commit_to"):
            commits.add(event.get("push_data").get("commit_to"))
    logging.info(f"Got {len(commits)} total commit(s)")
    return commits
            

def get_all_official_commits(repo_id:int) -> set[str]:
    url = f"{gitlab_instance_url}/api/v4/projects/{repo_id}/repository/commits?all=true" # doesn't work, doesn't show dangling commits even if they can still got directly
    data = requests.get(url, headers=request_headers)
    datajson = data.json()
    commits = set()
    for commit in datajson:
        if commit.get("id"):
            commits.add(commit.get("id"))
    logging.info(f"Got {len(commits)} official commit(s)")
    return commits

def find_dangling_commits(project, repository):
    repo_id = get_repository_id_from_name(project, repository)
    official_commits = get_all_official_commits(repo_id)
    all_commits = get_all_commits(repo_id)
    dangling_commits = all_commits - official_commits

    if dangling_commits:
        print("\nFound these dangling commits, which were in the event log and are not in the history anymore:")
        commit_print(project, repository ,dangling_commits)
    else:
        print("\nFound no dangling commits")

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
        find_dangling_commits(args.project, args.repository)
    except Exception as e:
        logging.exception(e)
        