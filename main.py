import config
import pygit2
import schema
import datetime


def main():
    schema.init_database()
    repo = pygit2.Repository(config.get("git.path"))
    reference = repo.branches.get(config.get("git.reference"))

    print(reference.target, type(reference))

    prev_commit = None
    iter = repo.walk(reference.peel().id, pygit2.GIT_SORT_TOPOLOGICAL)
    iter.simplify_first_parent()
    session = schema.get_session()

    counter = 0

    session.begin()
    for commit in iter:
        if prev_commit is not None:
            # Put old one first, new one later
            # For GIT_SORT_TOPOLOGICAL, it is cur-prev and for REVERSE, prev-cur
            diff = repo.diff(commit, prev_commit)
            tzone = datetime.timezone(datetime.timedelta(minutes=commit.commit_time_offset))
            date = datetime.datetime.fromtimestamp(commit.commit_time, tzone)
            # print(commit.id, date, commit.commit_time, datetime.datetime.fromtimestamp(commit.commit_time).isoformat())

            row = schema.CommitDiff(str(commit.id), str(commit.message), str(diff.patch), date)
            session.add(row)


            counter += 1
            if counter >= 1000:
                counter = 0
                print("1000 Updates are done. committing.")
                session.commit()
                session.begin()

        prev_commit = commit
    session.commit()
    session.close()


if __name__ == "__main__":
    main()
