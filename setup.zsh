#! /bin/zsh

set -e

# If running on my desktop, copy the files to my Pi
if ! cat /proc/cpuinfo | grep "Raspberry Pi"; then
    rsync -avP ../pirate-alarm kericho:~/repos
    ssh kericho "cd ~/repos/pirate-alarm && ./setup.zsh"
    exit
fi

mkdir -p md5sums

# Create the virtual environment
if [[ ! -d "venv" || ! -f "md5sums/requirements.txt.md5sum" || $(md5sum requirements.txt) != $(cat md5sums/requirements.txt.md5sum) ]]; then
    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt
    deactivate
    md5sum requirements.txt > md5sums/requirements.txt.md5sum
fi

# Create a symlink for the systemd units
pushd systemd
updated=false
for unit in *; do
    symlink=/etc/systemd/system/$unit
    target=/home/isaiah/repos/pirate-alarm/systemd/$unit
    if [[ ! -L $symlink ]]; then
        sudo ln -sf $target $symlink
        updated=true
    fi
    if [[ ! -f "../md5sums/$unit.md5sum" || $(md5sum $unit) != $(cat ../md5sums/$unit.md5sum) ]]; then
        updated=true
        md5sum $unit > ../md5sums/$unit.md5sum
    fi
done
if $updated; then
    sudo systemctl daemon-reload
    for unit in *; do
        sudo systemctl enable $unit
    done
fi
popd
