srpm:
	./getsource.sh
	rpmbuild -bs input-remapper-git.spec --define "_srcrpmdir $(outdir)"
