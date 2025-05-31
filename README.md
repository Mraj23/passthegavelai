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
