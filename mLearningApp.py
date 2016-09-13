"""mLearningApp."""

# all the imports
import os
from flask import Flask, request, session, g, redirect, url_for, render_template, flash  # send_from_directory, abort
from werkzeug.utils import secure_filename
import logging
from mLearning.dataPlot import DataPlot
from bokeh.resources import INLINE
from bokeh.embed import components
import inspect
import ast
from secret import SECRET_KEY
from os import listdir  # getcwd
# from jinja2 import FileSystemLoader

logging.basicConfig(
    level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    SECRET_KEY=SECRET_KEY,
    UPLOAD_FOLDER='uploads/',
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,
    static_folder='/home/vifespoir/static'
))

app.config.from_envvar('FLASKR_SETTINGS', silent=True)

# TODO make the following works
# loader = FileSystemLoader(getcwd() + '/templates/', followlinks=True)
# app.jinja_loader = loader

# Constants
ALLOWED_EXTENSIONS = ['csv']
SIMPLE_METHOD_NAMES = ['boxplot_all_quartiles', 'parallel_coordinates_graph', 'heatmap_pearson_correlation']
COMPLEX_METHOD_NAMES = ['cross_plotting_pair_of_attributes', 'transpose_index', 'plot_target_correlation']


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def check_data_status():  # check if data should be normalized
    try:
        session['dataStatus'] = ast.literal_eval(request.args['normalized'])
        logging.debug('Normalization Input: %s' % session['dataStatus'])
        flash('Data Normalized: %s' % session['dataStatus'], 'alert-info')

    except Exception:
        session['dataStatus'] = False


def check_if_session_active():
    try:
        session['filename']
        return True
    except KeyError:
        flash('Session Expired', 'alert-danger')
        return False


@app.route('/')
def home():
    return redirect(url_for('choose_file'))


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'alert-danger')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file', 'alert-danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            session['filename'] = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], session['filename']))
            flash('%s has been successfully uploaded' % session['filename'], 'alert-success')
            session['name'], session['extension'] = session['filename'].split('.', 1)
            return redirect(url_for('visualize_options', name=session['name']))

    return render_template('upload.html')


@app.route('/files')
def choose_file():
    try:
        files = listdir(app.config['UPLOAD_FOLDER'])
        flash('%s file(s) found.' % len(files), 'alert-info')
    except OSError as e:
        logging.debug('Error when loading files %s' % e)
        return redirect(url_for('upload_file'))
    else:
        return render_template('choose_file.html', files=files)

# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
#
# def getitem(obj, item, default):
#     if item not in obj:
#         return default
#     else:
#         return obj[item]


@app.route('/<name>', methods=['GET', 'POST'])
def visualize_options(name):
    logging.debug('Visualizing options...')

    # TODO Generate method name automatically

    session.setdefault('filename', name)
    session.setdefault('name', name.split('.', 1)[0])

    session['simpleOptions'] = SIMPLE_METHOD_NAMES
    session['complexOptions'] = COMPLEX_METHOD_NAMES

    logging.debug('Options visualized...')
    return render_template('choose_plot.html')


@app.route('/<name>/simple/<methodName>', methods=['GET', 'POST'])
def plot(name, methodName):
    logging.debug('App Plot starting...')

    session['methodName'] = methodName

    check_data_status()  # check if data should be normalized

    if not check_if_session_active():  # check if a dataPlot model is being served
        return redirect(url_for('choose_file'))

    if session['methodName'] in SIMPLE_METHOD_NAMES:
        dataPlot = DataPlot(tableName='us-veggies',
                            dataFile='uploads/' + session['filename'],
                            normalized=session['dataStatus'])

        logging.debug('dataPlot Status: %s' % dataPlot.normalized)
        methods = dict(inspect.getmembers(dataPlot, predicate=inspect.ismethod))
        method = methods[session['methodName']]
        plot = method()
        # Configure resources to include BokehJS inline in the document.
        # For more details see:
        #   http://bokeh.pydata.org/en/latest/docs/reference/resources_embedding.html#bokeh-embed
        js_resources = INLINE.render_js()
        css_resources = INLINE.render_css()
        # For more details see:
        #   http://bokeh.pydata.org/en/latest/docs/user_guide/embedding.html#components
        script, div = components(plot.document(), INLINE)
        return render_template('simple_plot.html',
                               plot_script=script,
                               plot_div=div,
                               js_resources=js_resources,
                               css_resources=css_resources,
                               name=plot.plotName)

    else:
        logging.debug('URL_FOR %s' % session['methodName'])
        return redirect(url_for(session['methodName'], name=session['name'], methodName=session['methodName']))


@app.route('/<name>/complex/<methodName>', methods=['GET', 'POST'])
def cross_plotting_pair_of_attributes(name, methodName):
    logging.debug('App Cross Plot starting...')
    dataPlot = DataPlot(tableName='us-veggies',
                        dataFile='uploads/' + session['filename'],
                        normalized=session['dataStatus'])

    logging.debug('dataPlot Status: %s' % dataPlot.normalized)
    columns = dataPlot.data.columns

    if request.method == 'POST':
        logging.debug('POST form: %s' % [item for item in request.form.items()])
        firstCol, secondCol = request.form['firstCol'], request.form['secondCol']

        methods = dict(inspect.getmembers(dataPlot, predicate=inspect.ismethod))
        method = methods[session['methodName']]
        plot = method(firstCol, secondCol)

        js_resources = INLINE.render_js()
        css_resources = INLINE.render_css()

        script, div = components(plot.document(), INLINE)

        return render_template(session['methodName'] + '.html',
                               columns=columns,
                               plot_script=script,
                               plot_div=div,
                               js_resources=js_resources,
                               css_resources=css_resources,
                               name=plot.plotName)

    return render_template(session['methodName'] + '.html',
                           columns=columns,
                           plot_script=None,
                           plot_div=None,
                           js_resources=None,
                           css_resources=None,
                           name=None)


@app.route('/<name>/complex/<methodName>', methods=['GET', 'POST'])
def transpose_index(name, methodName):
    logging.debug('App Transpose Index starting...')
    dataPlot = DataPlot(tableName='us-veggies',
                        dataFile='uploads/' + session['filename'],
                        normalized=session['dataStatus'])

    logging.debug('dataPlot Status: %s' % dataPlot.normalized)

    methods = dict(inspect.getmembers(dataPlot, predicate=inspect.ismethod))
    method = methods[session['methodName']]
    transpose_index = method()

    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()

    plots = []
    for fig in transpose_index:
        script, div = components(transpose_index[fig], INLINE)
        plots.append(dict(plot_script=script,
                          plot_div=div,
                          name=fig))

    return render_template(session['methodName'] + '.html', js_resources=js_resources,
                           css_resources=css_resources, plots=plots)


@app.route('/<name>/complex/<methodName>', methods=['GET', 'POST'])
def plot_target_correlation(name, methodName):
    logging.debug('App Plot Target Correlation starting...')
    dataPlot = DataPlot(tableName='us-veggies',
                        dataFile='uploads/' + session['filename'],
                        normalized=session['dataStatus'])

    logging.debug('dataPlot Status: %s' % dataPlot.normalized)

    columns = dataPlot.numericData.columns

    if request.method == 'POST':
        logging.debug('POST form: %s' % [item for item in request.form.items()])
        firstCol = request.form['firstCol']

        methods = dict(inspect.getmembers(dataPlot, predicate=inspect.ismethod))
        method = methods[session['methodName']]
        plot = method(firstCol)

        js_resources = INLINE.render_js()
        css_resources = INLINE.render_css()

        script, div = components(plot.document(), INLINE)

        return render_template(session['methodName'] + '.html',
                               columns=columns,
                               plot_script=script,
                               plot_div=div,
                               js_resources=js_resources,
                               css_resources=css_resources,
                               name=plot.plotName)

    return render_template(session['methodName'] + '.html',
                           columns=columns,
                           plot_script=None,
                           plot_div=None,
                           js_resources=None,
                           css_resources=None,
                           name=None)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
