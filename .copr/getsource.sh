#!/bin/bash
# Make sure the script can run properly no matter where it's called from
# The below line will always point to the repo's root directory.
repodir="$(realpath "$(dirname "${BASH_SOURCE[0]}")/../")"
PkgName=input-remapper-git
CoreRepo=https://github.com/sezanzeb/input-remapper
TarPath=archive/refs/heads/main.tar.gz
VerDate="$(date --utc +%y.%m.%d.%-k%M%S)"
Release=1
sourcedir=$(rpmbuild --eval='%_sourcedir')
source0="${sourcedir}/input-remapper-main.tar.gz"

cd "${repodir}" || exit
echo "Downloading latest input-remapper commit from git repository ${CoreRepo} to ${sourcedir}"
curl -L ${CoreRepo}/$TarPath -o ${source0}
echo "Copying README.Fedora to ${sourcedir}"
cp ${repodir}/README.Fedora ${sourcedir}/README.Fedora

cat > "${sourcedir}/_version" << EOF
${PkgName}
${VerDate}
${Release}
EOF
