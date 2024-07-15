#! /bin/zsh

set -e

# If running on my desktop, copy the files to my Pi
if ! cat /proc/cpuinfo | grep "Raspberry Pi"; then
    rsync -avP ../pirate-alarm kericho:~/repos
    ssh kericho "cd ~/repos/pirate-alarm && ./setup.zsh"
    exit
fi

# Create the virtual environment
new_sum=$()
if [[ ! -d "venv" || ! -f "requirements.md5sum" || $(md5sum requirements.txt) != $(cat requirements.md5sum) ]]; then
    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt
    deactivate
fi
md5sum requirements.txt > requirements.md5sum
