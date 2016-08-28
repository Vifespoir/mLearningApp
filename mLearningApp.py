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

logging.basicConfig(
    level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'FLASKR.db'),
    DEBUG=True,
    SECRET_KEY=SECRET_KEY,
    UPLOAD_FOLDER='uploads/',
    MAX_CONTENT_LENGTH=16 * 1024 * 1024
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

# Constants
ALLOWED_EXTENSIONS = ['csv']


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/')
def root():
    return redirect(url_for('upload_file'))


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            session['filename'] = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], session['filename']))
            flash('%s has been successfully uploaded' % session['filename'])
            session['name'], session['extension'] = session['filename'].split('.', 1)
            return redirect(url_for('visualize_options', name=session['name']))

    return render_template('upload.html')


# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
#
# def getitem(obj, item, default):
#     if item not in obj:
#         return default
#     else:
#         return obj[item]

# TODO implement session clean urls


@app.route('/<name>', methods=['GET', 'POST'])
def visualize_options(name):
    logging.debug('Visualizing options...')

    # TODO Generate method name automatically

    simpleMethodNames = ['boxplot_all_quartiles', 'parallel_coordinates_graph', 'heatmap_pearson_correlation']
    complexMethodNames = ['cross_plotting_pair_of_attributes', 'transpose_index', 'plot_target_correlation']

    session['simpleOptions'] = simpleMethodNames
    session['complexOptions'] = complexMethodNames

    session['dataStatus'] = False

    if request.method == 'POST':
        logging.debug('POST form: %s' % [item for item in request.form.items()])

        session['dataStatus'] = request.form['normalized']

        logging.debug('Normalization status: %s' % session['dataStatus'])

    logging.debug('Options visualized...')
    return render_template('home.html')


@app.route('/<name>/<methodName>')
def plot(name, methodName):
    logging.debug('App Plot starting...')
    logging.debug('Normalization Status: %s' % session['dataStatus'])
    dataPlot = DataPlot(tableName='us-veggies',
                        dataFile='uploads/' + session['filename'],
                        normalized=session['dataStatus'])
    logging.debug('dataPlot Status: %s' % dataPlot.normalized)
    methods = dict(inspect.getmembers(dataPlot, predicate=inspect.ismethod))
    method = methods[methodName]
    plot = method()
    # Configure resources to include BokehJS inline in the document.
    # For more details see:
    #   http://bokeh.pydata.org/en/latest/docs/reference/resources_embedding.html#bokeh-embed
    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()
    # For more details see:
    #   http://bokeh.pydata.org/en/latest/docs/user_guide/embedding.html#components
    script, div = components(plot.document(), INLINE)
    return render_template('embed.html',
                           plot_script=script,
                           plot_div=div,
                           js_resources=js_resources,
                           css_resources=css_resources,
                           name=plot.plotName)


@app.route('/<name>/cross_plotting_pair_of_attributes', methods=['GET', 'POST'])
def cross_plotting_pair_of_attributes(name):
    logging.debug('App Cross Plot starting...')
    dataPlot = DataPlot(tableName='us-veggies',
                        dataFile='uploads/' + session['filename'],
                        normalized=session['dataStatus'])
    columns = dataPlot.data.columns
    if request.method == 'POST':
        logging.debug('POST form: %s' % [item for item in request.form.items()])
        firstCol, secondCol = request.form['firstCol'], request.form['secondCol']

        methods = dict(inspect.getmembers(dataPlot, predicate=inspect.ismethod))
        method = methods['cross_plotting_pair_of_attributes']
        plot = method(firstCol, secondCol)

        js_resources = INLINE.render_js()
        css_resources = INLINE.render_css()

        script, div = components(plot.document(), INLINE)

        return render_template('cross_plotting_pair_of_attributes' + '.html',
                               columns=columns,
                               plot_script=script,
                               plot_div=div,
                               js_resources=js_resources,
                               css_resources=css_resources,
                               name=plot.plotName)

    return render_template('cross_plotting_pair_of_attributes' + '.html',
                           columns=columns,
                           plot_script=None,
                           plot_div=None,
                           js_resources=None,
                           css_resources=None,
                           name=None)


@app.route('/<name>/transpose_index', methods=['GET', 'POST'])
def transpose_index(name):
    dataPlot = DataPlot(tableName='us-veggies',
                        dataFile='uploads/' + session['filename'],
                        normalized=session['dataStatus'])
    methods = dict(inspect.getmembers(dataPlot, predicate=inspect.ismethod))
    method = methods['transpose_index']
    transpose_index = method()
    logging.debug(plot)

    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()

    plots = []
    for fig in transpose_index:
        script, div = components(transpose_index[fig], INLINE)
        plots.append(dict(plot_script=script,
                          plot_div=div,
                          name=fig))
    logging.debug(plots)

    return render_template('transpose_index' + '.html', js_resources=js_resources,
                           css_resources=css_resources, plots=plots)


@app.route('/<name>/plot_target_correlation', methods=['GET', 'POST'])
def plot_target_correlation(name):
    dataPlot = DataPlot(tableName='us-veggies',
                        dataFile='uploads/' + session['filename'],
                        normalized=session['dataStatus'])
    columns = dataPlot.numericData.columns

    if request.method == 'POST':
        logging.debug('POST form: %s' % [item for item in request.form.items()])
        firstCol = request.form['firstCol']

        methods = dict(inspect.getmembers(dataPlot, predicate=inspect.ismethod))
        method = methods['plot_target_correlation']
        plot = method(firstCol)

        js_resources = INLINE.render_js()
        css_resources = INLINE.render_css()

        script, div = components(plot.document(), INLINE)

        return render_template('plot_target_correlation' + '.html',
                               columns=columns,
                               plot_script=script,
                               plot_div=div,
                               js_resources=js_resources,
                               css_resources=css_resources,
                               name=plot.plotName)

    return render_template('plot_target_correlation' + '.html',
                           columns=columns,
                           plot_script=None,
                           plot_div=None,
                           js_resources=None,
                           css_resources=None,
                           name=None)


def main():
    app.debug = True
    app.run()

if __name__ == "__main__":
    main()
