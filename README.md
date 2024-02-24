# Gitlab Secrets

This tool analyzes a given Gitlab repository and searches for dangling or force-pushed commits, containing potential secret or interesting information.

It's based on <https://github.com/neodyme-labs/github-secrets> which does the same for Github

## Requirements

- Python3
- [requests](https://pypi.org/project/requests/)

## Installation

```bash
git clone https://github.com/neodyme-labs/github-secrets.git
```

## Usage

To get a list of basic options and switches use:
```bash
python3 gitlab_scanner.py -h
```

You can run this script either completely unauthenticated, or your generated API token by following [this guide](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html).

The tokens need requires `read_api` scope.

To export the token use:
```bash
export GITLAB_ACCOUNT_TOKEN=<your_secret_api_token>
```

To use against a custom instance of Gitlab
```bash
export GITLAB_INSTANCE_URL=<your_instance_url>
```

To run the script and scan a repository:
```bash
python3 gitlab_scanner.py <organisation>/<repository>
```

An example repository for testing is <https://gitlab.com/gitlab-secrets/gitlab-secrets>

## License

Licensed under either of

 * Apache License, Version 2.0, ([LICENSE-APACHE](LICENSE-APACHE) or <http://www.apache.org/licenses/LICENSE-2.0>)
 * MIT license ([LICENSE-MIT](LICENSE-MIT) or <http://opensource.org/licenses/MIT>)

at your option.

### Contribution

Unless you explicitly state otherwise, any contribution intentionally
submitted for inclusion in the work by you, as defined in the Apache-2.0
license, shall be dual licensed as above, without any additional terms or
conditions.