# Pass The Gavel

Len, Raj, Phi project for CMU T&E Home-cooked Apps AI Hackathon

# Setup

## Python Commands

```bash
# Start environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate

### Pre-commit Integration

The pre-commit hook will also run flake8 automatically on staged files along with black.

# Install requirements

pip install -r requirements.txt

# Save new requirements
pip freeze > requirements.txt

# Install git hook scripts
pre-commit install

# Run pre-commit
pre-commit run -a
```

## Manual Run

You can do manually to

```bash
flake8 .

black .
```

## Pre-commit Formatting

This project uses [pre-commit](https://pre-commit.com/) to run code formatting checks before commits.

1. Install pre-commit if you haven't already:

```bash
pip install pre-commit
```

2. Install the git hook scripts:

```bash
pre-commit install
```

3. Now, every time you commit, `black` will automatically format your Python code according to the configuration in `pyproject.toml`.

## Manual Formatting

You can also manually run black on the entire codebase with:

```bash
black .
```
