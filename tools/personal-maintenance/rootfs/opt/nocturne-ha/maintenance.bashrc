export PATH=/usr/local/bin:/usr/bin:/bin
export HISTFILE=/dev/null
unset SUPERVISOR_TOKEN
PS1='Nocturne onderhoud:\w\$ '
printf '\nNocturne onderhoud. Root binnen deze app; maak eerst een HA-back-up.\n'
printf 'Begin met: nocturne-ha doctor | nocturne-ha recover | nocturne-ha api --help\n\n'
