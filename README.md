# Github Secrets

This tool analyzes a given Github repository and searches for dangling or force-pushed commits, containing potential secret or interesting information.

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
python3 github_scanner.py -h
```

You can run this script either completely unauthenticated, with rather low Github API rate limits, or your export a generated [API token](https://github.com/settings/tokens).

The tokens need no privileges at all and are only used, for authentication against the API. A fine-grained personal access token is required for this project without any additional permissions.

To export the token use:
```bash
export GITHUB_ACCOUNT_TOKEN=<your_secret_api_token>
```

To run the script and scan a repository:
```bash
python3 github_scanner.py -r <username/repository>
```

To run the script and scan all of a specific users repositories:
```bash
python3 github_scanner.py -u <username>
```

## Resources

To check your current API rate limits and usage with token:
```bash
curl -L -H "Accept: application/vnd.github+json" -H "Authorization: Bearer <your_secret_api_token>" -H "X-GitHub-Api-Version: 2022-11-28" https://api.github.com/rate_limit
```

Without token:
```bash
curl -L -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" https://api.github.com/rate_limit
```

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
