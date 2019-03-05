import config
import pygit2


def main():
    repo = pygit2.Repository(config.get("git.path"))
    reference = repo.branches.get(config.get("git.reference"))

    print(reference, type(reference))
    prev_commit = None
    while True:
        commit = reference.peel()
        if commit is None:
            print(prev_commit, type(prev_commit))
            break

        if prev_commit is not None:
            diff = repo.diff(prev_commit, commit)
            print(diff, type(diff))
            break
        prev_commit = commit

    return
    for oid in repo:
        object = repo.git_object_lookup_prefix(oid)
        if isinstance(object, pygit2.Commit):
            commit = object
        else:
            continue
        #print(oid, type(oid))
        #print(commit.author.name, commit.author.email)
        #print(commit.committer.name, commit.committer.email)

        #print(commit.message)

        print(commit.tree)
        print("tree start")
        for entry in commit.tree:
            print(entry.name)
        print("tree end")

        print(commit.tree_id)

        print(commit.parents)

        print(commit.parent_ids)

        print(commit.commit_time)
        print(commit.commit_time_offset)
    pass

if __name__ == "__main__":
    main()