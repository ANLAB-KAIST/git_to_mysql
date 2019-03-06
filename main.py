import config
import pygit2
import schema
import datetime
from collections import deque
import threading
import multiprocessing
from sqlalchemy.exc import IntegrityError
from concurrent import futures


def repo_job(thread_id, current_commit_id, child_commit_id) -> (list, tuple or None):
    repo = pygit2.Repository(config.get("git.path").format(str(thread_id)))
    current_commit = repo.get(current_commit_id)
    ret_tuple = None
    if child_commit_id is not None:
        child_commit = repo.get(child_commit_id)

        diff = repo.diff(current_commit, child_commit, context_lines=0)
        tzone = datetime.timezone(datetime.timedelta(minutes=child_commit.commit_time_offset))
        date = datetime.datetime.fromtimestamp(child_commit.commit_time, tzone)

        stats = diff.stats
        patch = diff.patch
        insertions = stats.insertions
        deletions = stats.deletions
        msg = child_commit.message

        ret_tuple = (str(patch), str(msg), int(insertions), int(deletions), date)

    parent_list = []
    for parent_commit in current_commit.parents:
        parent_list.append(str(parent_commit.id))

    return parent_list, ret_tuple


class SharedStat:
    def __init__(self):
        self.lock = threading.Lock()
        self.cv = threading.Condition(lock=self.lock)
        self.counter = 0
        self.num_waiting = 0
        self.finished = False
        self.thread_count = multiprocessing.cpu_count()
        self.pool = futures.ProcessPoolExecutor()


def worker(thread_id, session, queue, shared):
    with shared.lock:
        print(threading.current_thread().name)

    while True:
        while not shared.finished:
            with shared.lock:
                shared.num_waiting += 1
                if len(queue) > 0:
                    (child_commit_id, current_commit_id) = queue.popleft()
                    shared.num_waiting -= 1
                    break
                else:
                    if shared.num_waiting == shared.thread_count:
                        shared.finished = True
                        shared.cv.notify_all()
                    else:
                        shared.cv.wait()
                shared.num_waiting -= 1
        if shared.finished:
            break

        ret_future = shared.pool.submit(repo_job, thread_id, current_commit_id, child_commit_id)
        (parent_list, ret_tuple) = ret_future.result()
        if ret_tuple is not None:

            with shared.lock:
                print("{} is processing {} and {}".format(threading.current_thread().name, child_commit_id, current_commit_id))

            (patch, msg, insertions, deletions, date) = ret_tuple
            try:
                session.begin()
                row = schema.CommitDiff(child_commit_id, current_commit_id, msg, patch, insertions, deletions, date)
                session.add(row)
                session.commit()
            except IntegrityError:
                session.rollback()
                continue
            except Exception as e:
                new_diff = "Exception occured: " + str(e)
                if patch is None:
                    new_diff += "\nDiff is None"
                else:
                    new_diff += "\nDiff length is " + str(len(patch))
                with shared.lock:
                    print(child_commit_id, current_commit_id, new_diff)
                session.rollback()
                try:
                    session.begin()
                    row = schema.CommitDiff(child_commit_id, current_commit_id, msg, new_diff, insertions, deletions, date)
                    session.add(row)
                    session.commit()
                except IntegrityError:
                    session.rollback()
                    continue

        with shared.lock:
            shared.counter += 1
            if shared.counter >= 1000:
                shared.counter = 0
                print("1000 Updates are done. " + threading.current_thread().name)

            for parent_commit_id in parent_list:
                queue.append((current_commit_id, parent_commit_id))
            shared.cv.notify_all()


class Worker(threading.Thread):

    def __init__(self, thread_id: int, work_queue: deque, shared: SharedStat):
        self.thread_id = thread_id
        self.queue = work_queue
        self.shared = shared
        threading.Thread.__init__(self)

    def run(self):
        session = schema.get_session()
        try:
            worker(self.thread_id, session, self.queue, self.shared)
        except Exception as e:
            print("Criticial Error: " + str(e))
        session.close()


def main():
    schema.init_database()
    repo = pygit2.Repository(config.get("git.path").format(""))
    reference = repo.branches.get(config.get("git.reference"))
    print(reference.target, type(reference))

    bfs_queue = deque()
    start_commit = reference.peel()
    bfs_queue.append((None, str(start_commit.id)))

    shared_stat = SharedStat()

    thread_list = []
    thread_id = 0
    for i in range(shared_stat.thread_count):
        worker = Worker(thread_id, bfs_queue, shared_stat)
        thread_id += 1
        worker.start()
        thread_list.append(worker)

    for worker in thread_list:
        worker.join()


if __name__ == "__main__":
    main()
