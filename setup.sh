#!/bin/bash

# check if $profile exists, if not create it
if [ ! -e "$HOME/.bashrc" ]; then
  touch "$HOME/.bashrc"
fi

# current folder
root=$(dirname "$(readlink -f "$0")")

# check if # lords-asm-for-mc-begin comment exists in $profile, if so remove everything between # lords-asm-for-mc-begin and # lords-asm-for-mc-end
if grep -q "# lords-asm-for-mc-begin" "$HOME/.bashrc"; then
  echo "Usuwanie poprzedniej instalacji 'lords-asm-for-mc' z $HOME/.bashrc"
  sed -i '/# lords-asm-for-mc-begin/,/# lords-asm-for-mc-end/d' "$HOME/.bashrc"
fi

# install requirements
echo "Instalowanie zależności 'lords-asm-for-mc' w $root przy użyciu pip"
pip install -r "$root/requirements.txt"

# add # lords-asm-for-mc-begin comment to $profile
echo "# lords-asm-for-mc-begin" >> "$HOME/.bashrc"
echo "# Nie edytuj, nie usuwaj ani nie zmieniaj tych komentarzy; są używane przez 'lords-asm-for-mc' do instalacji i dezinstalacji" >> "$HOME/.bashrc"

# add alias to compile.py
compile="$root/compile.py"
echo "function lor { \$@ | python \"$compile\" \"\$@\"; }" >> "$HOME/.bashrc"

# add alias to send.py
send="$root/tools/send.py"
echo "function rfsend { \$@ | python \"$send\" \"\$@\"; }" >> "$HOME/.bashrc"

echo "Alias 'lor' i 'rfsend' utworzony w $HOME/.bashrc"

# add $root to the PATH, if not already there
if [[ ":$PATH:" != *":$root:"* ]]; then
  echo "export PATH=\"\$PATH:$root\"" >> "$HOME/.bashrc"
fi

echo "Dodano '$root' do ścieżki (PATH)"

echo "Gotowe"