"""Flask tutorial."""

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
            return redirect(url_for('visualize', filename=filename))

    return render_template('upload.html')


# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


def getitem(obj, item, default):
    if item not in obj:
        return default
    else:
        return obj[item]


@app.route('/uploads/<filename>', methods=['GET', 'POST'])
def visualize(filename):
    methodNames = ['normalize_data', 'cross_plotting_pair_of_attributes', 'transpose_index', 'plot_target_correlation', '__init__', 'boxplot_all_quartiles', 'parallel_coordinates_graph', 'heatmap_pearson_correlation']
    logging.debug(methodNames)
    logging.debug(request.method)
    if request.method == 'POST':
        methodName = request.form['option']
        logging.debug(methodName)
        if methodName != '':
            return redirect(url_for('plot', filename=filename, plotName=methodName))

    return render_template(
        'plot_options.html',
        options=methodNames)


@app.route('/uploads/<filename>/<plotName>')
def plot(filename, plotName):
    plot = DataPlot('us-veggies', 'uploads/' + filename)
    methods = dict(inspect.getmembers(plot, predicate=inspect.ismethod))
    method = methods[plotName]
    plot = method()
    # Configure resources to include BokehJS inline in the document.
    # For more details see:
    #   http://bokeh.pydata.org/en/latest/docs/reference/resources_embedding.html#bokeh-embed
    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()
    # For more details see:
    #   http://bokeh.pydata.org/en/latest/docs/user_guide/embedding.html#components
    script, div = components(plot.document(), INLINE)
    return render_template(
        'embed.html',
        plot_script=script,
        plot_div=div,
        js_resources=js_resources,
        css_resources=css_resources,
        name=plot.plotName)


def main():
    app.debug = True
    app.run()

if __name__ == "__main__":
    main()
