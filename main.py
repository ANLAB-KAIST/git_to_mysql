import config
import pygit2

def main():
    repo = pygit2.Repository(config.get("git.path"))
    print(repo.is_bare)
    for oid in repo:
        object = repo.git_object_lookup_prefix(oid)
        if isinstance(object, pygit2.Commit):
            commit = object
        else:
            continue
        print(oid)
        print(commit.author)

        print(commit.committer)

        print(commit.message)

        print(commit.tree)

        print(commit.tree_id)

        print(commit.parents)

        print(commit.parent_ids)

        print(commit.commit_time)
        print(commit.commit_time_offset)
    pass

if __name__ == "__main__":
    main()