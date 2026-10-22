# Contributing to GEO Metadata Engine

We welcome contributions to this project. Please read the following guidelines before contributing.

## Code Reviews

All code changes, including those from project members, require a code review. We use GitHub Pull Requests for this purpose. See the [GitHub documentation on pull requests](https://help.github.com/articles/about-pull-requests/) for more information.

When updating dependencies, make sure to update [THIRD-PARTY-LICENSES.md](THIRD-PARTY-LICENSES.md) accordingly.

## Code Style

Python code follows [PEP 8](https://peps.python.org/pep-0008/) and Django's [coding style](https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/). We format with [autopep8](https://pypi.org/project/autopep8/), e.g. via the [VS Code extension](https://marketplace.visualstudio.com/items?itemName=ms-python.autopep8). It is not enforced in CI; please check `git diff` before committing, especially in older files.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE-OF-CONDUCT.md).

## Developer Documentation

For technical setup, architecture, and development guidelines see [CLAUDE.md](CLAUDE.md).
