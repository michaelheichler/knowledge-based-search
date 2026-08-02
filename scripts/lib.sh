backup_file() {
	local path="$1"
	local tag="${2:-kbs}"
	[ -e "$path" ] || [ -L "$path" ] || return 0
	local stamp target number
	stamp="$(date -u +%Y%m%dT%H%M%SZ)"
	target="$path.$tag.$stamp.bak"
	number=1
	while [ -e "$target" ] || [ -L "$target" ]; do
		target="$path.$tag.$stamp.$number.bak"
		number=$((number + 1))
	done
	cp -P "$path" "$target"
	printf '%s\n' "backed up $path to $target"
}
