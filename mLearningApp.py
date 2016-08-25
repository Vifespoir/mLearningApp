"""mLearningApp."""

# all the imports
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.local import LocalProxy
import logging
from mLearning.dataPlot import DataPlot
from bokeh.resources import INLINE
from bokeh.embed import components
import inspect


logging.basicConfig(
    level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'FLASKR.db'),
    DEBUG=True,
    SECRET_KEY='dSjt+xSuRkuVFeIbWvPQcVcrNrVUz3gezuU3MvVbDX+70UOpgIanCXBzWFVfgBiMzuShjkdM3uTAhNGNTU7pHg==',
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
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('%s has been successfully uploaded' % filename)
            return redirect(url_for('visualize_options', filename=filename))

    return render_template('upload.html')


# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


def getitem(obj, item, default):
    if item not in obj:
        return default
    else:
        return obj[item]

# TODO implement session clean urls

@app.route('/<filename>', methods=['GET', 'POST'])
def visualize_options(filename):
    logging.debug('Visualizing options...')

    # TODO Generate method name automatically

    simpleMethodNames = ['boxplot_all_quartiles', 'parallel_coordinates_graph', 'heatmap_pearson_correlation']
    complexMethodNames = ['cross_plotting_pair_of_attributes', 'transpose_index', 'plot_target_correlation']

    templateDict = dict(simpleOptions=simpleMethodNames,
                        complexOptions=complexMethodNames)
    logging.debug('Method names: %s' % templateDict)

    if request.method == 'POST':
        logging.debug('POST form: %s' % [item for item in request.form.items()])

        normalized = request.form['normalized']
        logging.debug('Normalization status: %s' % normalized)
        if normalized == 'True':
            dataStatus = True
        else:
            dataStatus = False

        methodName = request.form['option']
        logging.debug('DataPlot method to be called: %s' % methodName)
        if methodName in simpleMethodNames:
            logging.debug('Simple Method')
            try:
                return redirect(url_for('plot', filename=filename, methodName=methodName, dataStatus=dataStatus))
            except Exception as e:
                flash('Internal error: %s' % e)
                logging.debug('Internal error: %s' % e)
        elif methodName in complexMethodNames:
            logging.debug('Complex Method')
            try:
                return redirect(url_for(methodName, filename=filename, methodName=methodName, dataStatus=dataStatus))
            except Exception as e:
                flash('Internal error: %s' % e)
                logging.debug('Internal error: %s' % e)
        else:
            flash('Internal error: the method called is not available.')
            logging.debug('Internal error: the method called is not available.')

    logging.debug('Options visualized...')
    return render_template('simple_options.html', **templateDict)


@app.route('/uploads/<filename>/<dataStatus>/<methodName>')
def plot(filename, dataStatus, methodName):
    logging.debug('App Plot starting...')
    logging.debug('Normalization Status: %s' % dataStatus)
    dataPlot = DataPlot(tableName='us-veggies', dataFile='uploads/' + filename, normalized=dataStatus)
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


@app.route('/uploads/<filename>/<dataStatus>/cross_plotting_pair_of_attributes/<methodName>', methods=['GET', 'POST'])
def cross_plotting_pair_of_attributes(filename, dataStatus, methodName):
    logging.debug('App Cross Plot starting...')
    dataPlot = DataPlot(tableName='us-veggies', dataFile='uploads/' + filename, normalized=dataStatus)
    columns = dataPlot.data.columns
    if request.method == 'POST':
        logging.debug('POST form: %s' % [item for item in request.form.items()])
        firstCol, secondCol = request.form['firstCol'], request.form['secondCol']

        methods = dict(inspect.getmembers(dataPlot, predicate=inspect.ismethod))
        method = methods[methodName]
        plot = method(firstCol, secondCol)

        js_resources = INLINE.render_js()
        css_resources = INLINE.render_css()

        script, div = components(plot.document(), INLINE)

        return render_template(methodName + '.html',
                               columns=columns,
                               plot_script=script,
                               plot_div=div,
                               js_resources=js_resources,
                               css_resources=css_resources,
                               name=plot.plotName)

    return render_template(methodName + '.html',
                           columns=columns,
                           plot_script=None,
                           plot_div=None,
                           js_resources=None,
                           css_resources=None,
                           name=None)


@app.route('/uploads/<filename>/<dataStatus>/transpose_index/<methodName>', methods=['GET', 'POST'])
def transpose_index(filename, dataStatus, methodName):
    dataPlot = DataPlot(tableName='us-veggies', dataFile='uploads/' + filename, normalized=dataStatus)
    methods = dict(inspect.getmembers(dataPlot, predicate=inspect.ismethod))
    method = methods[methodName]
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

    return render_template(methodName + '.html', js_resources=js_resources,
                           css_resources=css_resources, plots=plots)


@app.route('/uploads/<filename>/<dataStatus>/plot_target_correlation/<methodName>', methods=['GET', 'POST'])
def plot_target_correlation(filename, dataStatus, methodName):
    dataPlot = DataPlot(tableName='us-veggies', dataFile='uploads/' + filename, normalized=dataStatus)
    columns = dataPlot.numericData.columns
    if request.method == 'POST':
        logging.debug('POST form: %s' % [item for item in request.form.items()])
        firstCol = request.form['firstCol']

        methods = dict(inspect.getmembers(dataPlot, predicate=inspect.ismethod))
        method = methods[methodName]
        plot = method(firstCol)

        js_resources = INLINE.render_js()
        css_resources = INLINE.render_css()

        script, div = components(plot.document(), INLINE)

        return render_template(methodName + '.html',
                               columns=columns,
                               plot_script=script,
                               plot_div=div,
                               js_resources=js_resources,
                               css_resources=css_resources,
                               name=plot.plotName)

    return render_template(methodName + '.html',
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
