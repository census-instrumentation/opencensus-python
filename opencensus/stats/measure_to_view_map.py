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
from opencensus.stats.view import View
from opencensus.stats.view_data import ViewData
from datetime import datetime
import logging


class MeasureToViewMap(object):

    def __init__(self):
        self._map = {}
        self._registered_views = {}
        self._registered_measures = {}
        self._exported_views = set()

    def get_view(self, view_name, timestamp):
        view = self.get_view_data(view_name)
        print("view", view)
        if view is None:
            return None

        view_data = ViewData(view=view, start_time=timestamp, end_time=timestamp)
        return view_data

    def get_view_data(self, view_name):
        view = self._registered_views.get(view_name)
        if view is None:
            return None

        views = []
        for key, value in self._map.items():
            if key == view.measure.name:
                views.append(self._map[key])

        for view_data in views:
            if view_data.view.name == view_name:
                print("view data", view_data)
                return view_data

    def get_exported_views(self):
        return self._exported_views

    def filter_exported_views(self, all_views):
        """returns the subset of the given view that should be exported"""
        views = set(all_views)
        return views

    def register_view(self, view, timestamp):
        self._exported_views = None
        existing_view = self._registered_views.get(view.name)
        if existing_view is not None:
            if existing_view == view:
                # ignore the views that are already registered
                return
            else:
                logging.warning("A different view with the same name is already registered")
                return
        measure = view.measure
        registered_measure = self._registered_measures.get(measure.name)
        if registered_measure is not None and registered_measure != measure:
            logging.warning("A different measure with the same name is already registered")
            return
        self._registered_views[measure.name] = view
        if registered_measure is None:
            self._registered_measures[measure.name] = measure
        self._map[view.measure.name] = ViewData(view=view, start_time=timestamp, end_time=timestamp)

    def record(self, tags, stats, timestamp):
        for measurement, value in stats.items():
            # measurement = measurement
            measure = measurement.measure
            if measure != self._registered_measures.get(measure.name):
                return
            view_datas = []
            for key, value in self._map.items():
                if key == measure.name:
                    view_datas.append(self._map[key])
            for view_data in view_datas:
                ViewData.record(view_data, context=tags, value=view_data.view.measure, timestamp=timestamp)
