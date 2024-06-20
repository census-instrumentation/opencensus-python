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

from flask import Flask, render_template, request

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/view_configs')
def view_configs():
    sampler = request.args.get('sampler')
    exporter = request.args.get('exporter')
    propagator = request.args.get('propagator')
    return render_template(
        'view_configs.html',
        sampler=sampler,
        exporter=exporter,
        propagator=propagator)


if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)
