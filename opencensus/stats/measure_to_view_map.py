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

from opencensus.stats.view_data import ViewData
from collections import defaultdict
import logging
import copy


class MeasureToViewMap(object):
    """Measure To View Map stores a map from names of Measures to
    specific View Datas

    """

    def __init__(self):
        # stores the one-to-many mapping from Measures to View Datas
        self._measure_to_view_data_list_map = defaultdict(list)
        # stores a map from the registered View names to the Views
        self._registered_views = {}
        # stores a map from the registered Measure names to the Measures
        self._registered_measures = {}
        # stores the set of the exported views
        self._exported_views = set()

    @property
    def exported_views(self):
        """the current exported views"""
        return self._exported_views

    def get_view(self, view_name, timestamp):
        """get the View Data from the given View name"""
        view = self._registered_views.get(view_name)
        if view is None:
            return None

        view_data_list = self._measure_to_view_data_list_map.get(
            view.measure.name)
        if view_data_list is not None:
            for view_data in view_data_list:
                if view_data.view.name == view_name:
                    view_data_copy = copy.deepcopy(view_data)
                    view_data_copy.end()
                    return view_data_copy

    def filter_exported_views(self, all_views):
        """returns the subset of the given view that should be exported"""
        views = set(all_views)
        return views

    def register_view(self, view, timestamp):
        """registers the view's measure name to View Datas given a view"""
        self._exported_views = None
        existing_view = self._registered_views.get(view.name)
        if existing_view is not None:
            if existing_view == view:
                # ignore the views that are already registered
                return
            else:
                logging.warning(
                    "A different view with the same name is already registered"
                )  # pragma: NO COVER
        measure = view.measure
        registered_measure = self._registered_measures.get(measure.name)
        if registered_measure is not None and registered_measure != measure:
            logging.warning(
                "A different measure with the same name is already registered")
        self._registered_views[view.name] = view
        if registered_measure is None:
            self._registered_measures[measure.name] = measure
        self._measure_to_view_data_list_map[view.measure.name].append(
            ViewData(view=view, start_time=timestamp, end_time=timestamp))

    def record(self, tags, measurement_map, timestamp):
        """records stats with a set of tags"""
        for measure, value in measurement_map.items():
            if measure != self._registered_measures.get(measure.name):
                return
            view_datas = []
            for measure_name, view_data_list \
                    in self._measure_to_view_data_list_map.items():
                if measure_name == measure.name:
                    view_datas.extend(view_data_list)
            for view_data in view_datas:
                view_data.record(
                    context=tags, value=value, timestamp=timestamp)
