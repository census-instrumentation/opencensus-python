import datetime
import json
import random
import os

from opencensus.ext.azure.common.schedule import PeriodicTask

_TIMESTAMP_FORMAT = '%Y-%m-%dT%H%M%S.%f'


class LocalFileBlob(object):
    def __init__(self, fullpath):
        self.fullpath = fullpath

    def delete(self):
        os.remove(self.fullpath)

    def get(self):
        with open(self.fullpath, 'r') as file:
            return tuple(
                json.loads(line.strip())
                for line in file.readlines()
            )

    def put(self, data):
        fullpath = self.fullpath + '.tmp'
        with open(fullpath, 'w') as file:
            for item in data:
                file.write(json.dumps(item))
                # The official Python doc: Do not use os.linesep as a line
                # terminator when writing files opened in text mode (the
                # default); use a single '\n' instead, on all platforms.
                file.write('\n')
        os.rename(fullpath, self.fullpath)

    def lease(self, seconds):
        ts = datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds)
        fullpath = self.fullpath
        if fullpath.endswith('.lock'):
            fullpath = fullpath[: fullpath.rindex('@')]
        fullpath += '@{}.lock'.format(ts.strftime(_TIMESTAMP_FORMAT))
        try:
            os.rename(self.fullpath, fullpath)
        except:
            return None
        self.fullpath = fullpath
        return self


class LocalFileStorage(object):
    def __init__(self, path, max_size=1024*1024, maintenance_period=60):
        self.path = os.path.abspath(path)
        self.max_size = max_size
        self.maintenance_period = maintenance_period
        self._maintenance_routine()
        self._maintenance_task = PeriodicTask(
            interval=self.maintenance_period,
            function=self._maintenance_routine,
        )
        self._maintenance_task.start()

    def close(self):
        self._maintenance_task.cancel()

    def _maintenance_routine(self):
        if not os.path.isdir(self.path):
            try:
                os.makedirs(self.path)
            except:
                pass  # keep silent
        try:
            for blob in self.gets():
                pass  # keep silent
        except:
            pass  # keep silent

    def gets(self):
        deadline = datetime.datetime.utcnow()
        deadline -= datetime.timedelta(seconds=self.maintenance_period)
        deadline = deadline.strftime(_TIMESTAMP_FORMAT)
        for name in sorted(os.listdir(self.path)):
            path = os.path.join(self.path, name)
            if not os.path.isfile(path):
                continue  # skip if not a file
            if path.endswith('.tmp'):
                if name < deadline:
                    try:
                        os.remove(path)  # TODO: log data loss
                    except:
                        pass  # keep silent
                continue
            if path.endswith('.lock'):
                now = datetime.datetime.utcnow().strftime(_TIMESTAMP_FORMAT)
                if path[path.rindex('@') + 1 : -5] > now:  # under lease
                    continue
                new_path = path[: path.rindex('@')]
                try:
                    os.rename(path, new_path)
                except:
                    continue  # keep silent
                path = new_path
            if path.endswith('.blob'):
                yield LocalFileBlob(path)

    def get(self):
        cursor = self.gets()
        try:
            return next(cursor)
        except StopIteration:
            pass
        return None

    def put(self, data):
        blob = LocalFileBlob(os.path.join(
            self.path,
            '{}-{}.blob'.format(
                datetime.datetime.utcnow().strftime(_TIMESTAMP_FORMAT),
                '{:08x}'.format(random.getrandbits(32)),  # thread-safe random
            ),
        ))
        blob.put(data)
        return blob
