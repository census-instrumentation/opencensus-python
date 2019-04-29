import datetime
import json
import random
import os

from opencensus.common.schedule import PeriodicTask


def _fmt(timestamp):
    return timestamp.strftime('%Y-%m-%dT%H%M%S.%f')


def _now():
    return datetime.datetime.utcnow()


def _seconds(seconds):
    return datetime.timedelta(seconds=seconds)


class LocalFileBlob(object):
    def __init__(self, fullpath):
        self.fullpath = fullpath

    def delete(self, silent=False):
        try:
            os.remove(self.fullpath)
        except Exception:
            if not silent:
                raise

    def get(self):
        with open(self.fullpath, 'r') as file:
            return tuple(
                json.loads(line.strip())
                for line in file.readlines()
            )

    def put(self, data, lease_period=0):
        fullpath = self.fullpath + '.tmp'
        with open(fullpath, 'w') as file:
            for item in data:
                file.write(json.dumps(item))
                # The official Python doc: Do not use os.linesep as a line
                # terminator when writing files opened in text mode (the
                # default); use a single '\n' instead, on all platforms.
                file.write('\n')
        if lease_period:
            timestamp = _now() + _seconds(lease_period)
            self.fullpath += '@{}.lock'.format(_fmt(timestamp))
        os.rename(fullpath, self.fullpath)

    def lease(self, period):
        timestamp = _now() + _seconds(period)
        fullpath = self.fullpath
        if fullpath.endswith('.lock'):
            fullpath = fullpath[: fullpath.rindex('@')]
        fullpath += '@{}.lock'.format(_fmt(timestamp))
        try:
            os.rename(self.fullpath, fullpath)
        except Exception:
            return None
        self.fullpath = fullpath
        return self


class LocalFileStorage(object):
    def __init__(
        self,
        path,
        max_size=100*1024*1024,  # 100MB
        maintenance_period=60,  # 1 minute
        retention_period=7*24*60*60,  # 7 days
        write_timeout=60,  # 1 minute
    ):
        self.path = os.path.abspath(path)
        self.max_size = max_size
        self.maintenance_period = maintenance_period
        self.retention_period = retention_period
        self.write_timeout = write_timeout
        self._maintenance_routine()
        self._maintenance_task = PeriodicTask(
            interval=self.maintenance_period,
            function=self._maintenance_routine,
        )
        self._maintenance_task.daemon = True
        self._maintenance_task.start()

    def close(self):
        self._maintenance_task.cancel()

    def _maintenance_routine(self):
        if not os.path.isdir(self.path):
            try:
                os.makedirs(self.path)
            except Exception:
                pass  # keep silent
        try:
            for blob in self.gets():
                pass  # keep silent
        except Exception:
            pass  # keep silent

    def gets(self):
        timeout_deadline = _fmt(_now() - _seconds(self.write_timeout))
        retention_deadline = _fmt(_now() - _seconds(self.retention_period))
        for name in sorted(os.listdir(self.path)):
            path = os.path.join(self.path, name)
            if not os.path.isfile(path):
                continue  # skip if not a file
            if path.endswith('.tmp'):
                if name < timeout_deadline:
                    try:
                        os.remove(path)  # TODO: log data loss
                    except Exception:
                        pass  # keep silent
            if path.endswith('.lock'):
                now = _fmt(_now())
                if path[path.rindex('@') + 1: -5] > now:  # under lease
                    continue
                new_path = path[: path.rindex('@')]
                try:
                    os.rename(path, new_path)
                except Exception:
                    continue  # keep silent
                path = new_path
            if path.endswith('.blob'):
                if name < retention_deadline:
                    try:
                        os.remove(path)  # TODO: log data loss
                    except Exception:
                        pass  # keep silent
                else:
                    yield LocalFileBlob(path)

    def get(self):
        cursor = self.gets()
        try:
            return next(cursor)
        except StopIteration:
            pass
        return None

    def put(self, data, lease_period=0):
        blob = LocalFileBlob(os.path.join(
            self.path,
            '{}-{}.blob'.format(
                _fmt(_now()),
                '{:08x}'.format(random.getrandbits(32)),  # thread-safe random
            ),
        ))
        blob.put(data, lease_period)
        return blob
