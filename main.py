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

    for commit in iter:
        if prev_commit is not None:
            # Put old one first, new one later
            # For GIT_SORT_TOPOLOGICAL, it is cur-prev and for REVERSE, prev-cur
            diff = repo.diff(commit, prev_commit)
            tzone = datetime.timezone(datetime.timedelta(minutes=commit.commit_time_offset))
            date = datetime.datetime.fromtimestamp(commit.commit_time, tzone)
            # print(commit.id, date, commit.commit_time, datetime.datetime.fromtimestamp(commit.commit_time).isoformat())

            id = str(commit.id)
            msg = str(commit.message)
            if diff.patch is not None:
                diff = str(diff.patch)

            try:
                session.begin()
                row = schema.CommitDiff(id, msg, diff, date)
                session.add(row)
                session.commit()
            except Exception as e:
                new_diff = "Exception occured: " + str(e)
                if diff is None:
                    new_diff += "\nDiff is None"
                else:
                    new_diff += "\nDiff length is " + str(len(diff))
                print(id, msg)
                session.rollback()
                session.begin()
                row = schema.CommitDiff(id, msg, new_diff, date)
                session.add(row)
                session.commit()

            counter += 1
            if counter >= 1000:
                counter = 0
                print("1000 Updates are done.")
        prev_commit = commit
    session.close()


if __name__ == "__main__":
    main()
