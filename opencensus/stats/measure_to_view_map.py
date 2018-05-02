# Copyright 2018, OpenCensus Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from opencensus.tags import tag_map
from opencensus.stats.measurement import Measurement
from opencensus.stats import measurement
from opencensus.stats import view
from opencensus.stats import view_data
from datetime import datetime
import threading


def synchronized(lock):

    def wrap(method):
        def new_method(self, *args, **kwargs):
            yield from lock
            try:
                return method(self, *args, **kwargs)
            finally:
                lock.release()
        return new_method
    return wrap


class MeasureToViewMap(object):

    def __init__(self):
        self._lock = threading.Lock()
        self._map = {}
        self._registered_views = {}
        self._registered_measures = {}
        self._exported_views = set()
        self._auto_lock = threading.Lock()

    @synchronized
    def get_view(self, view_name, timestamp):
        view = self.get_view_data(view_name)
        if view is None:
            return None
        else:
            return view_data.ViewData(view = view, start_time=datetime.utcnow().isoformat() + 'Z', end_time=datetime.utcnow().isoformat() + 'Z')
        pass

    @synchronized
    def get_view_data(self, view_name):
        view = self._registered_views.get(view_name)
        if view is None:
            return None
        views = self._map.get(view.measure.name)
        for view_data in views:
            if view_data.name == view_name:
                return view_data
        pass

    @synchronized
    def get_exported_views(self):
        return self._exported_views
        pass

    def filter_exported_views(self, all_views):
        """returns the subset of the given view that should be exported"""
        views = set()
        for view in all_views:
            views.add(view)

        return views

    @synchronized
    def register_view(self, view, timestamp):
        self._exported_views = None
        existing_view = self._registered_views.get(view.name)
        if existing_view is not None:
            if existing_view.equals(view):
                return
        measure = view.measure
        registered_measure = self._registered_measures.get(measure.name)
        if registered_measure is not None and registered_measure != measure:
            print("A different measure with the same name is already registered")
        if registered_measure is None:
            self._registered_measures[measure.name] = measure
        self._map[view.measure.name] = view_data.ViewData(view=view, start_time=datetime.utcnow().isoformat() + 'Z', end_time=datetime.utcnow().isoformat() + 'Z')
        pass

    @synchronized
    def record(self, tags, stats, timestamp):
        for measurement in stats:
            measurement = measurement.Measurement
            measure = measurement.measure
            if measure != self._registered_measures.get(measure.name):
                continue
            view_datas = self._map.get(measure.name)
            for view_data in view_datas:
                self.record(tags, view_data, timestamp)
        pass
