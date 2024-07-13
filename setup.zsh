#! /bin/zsh

# Create virtual environment
virtualenv venv

source venv/bin/activate

pip install -r requirements.txt

deactivate

