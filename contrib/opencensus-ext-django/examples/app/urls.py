# Copyright 2017, OpenCensus Authors
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

"""project_name URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin

import app.views


urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', app.views.home),
    url(r'^greetings$', app.views.greetings),
    url(r'^_ah/health$', app.views.health_check),
    url(r'^request$', app.views.get_request_header),
    url(r'^mysql$', app.views.mysql_trace),
    url(r'^postgresql$', app.views.postgresql_trace),
    url(r'^trace_requests', app.views.trace_requests),
    url(r'^sqlalchemy_mysql$', app.views.sqlalchemy_mysql_trace),
    url(r'^sqlalchemy_postgresql$', app.views.sqlalchemy_postgresql_trace),
]
