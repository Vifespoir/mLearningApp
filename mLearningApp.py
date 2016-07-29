"""Flask tutorial."""

# all the imports
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from werkzeug.utils import secure_filename
import logging
from mLearning.dataPlot import DataPlot


from bokeh.resources import INLINE
from bokeh.util.string import encode_utf8
from bokeh.embed import components


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
            return redirect(url_for('plot', filename=filename))

    return render_template('upload.html')

from flask import send_from_directory

# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return render_template('uploaded.html', filename=filename)
#
# def getitem(obj, item, default):
#     if item not in obj:
#         return default
#     else:
#         return obj[item]


@app.route('/uploads/<filename>')
def plot(filename):
    plots = DataPlot('us-veggies', 'uploads/' + filename)
    fig = plots.boxplot_all_quartiles(normalized=True)
    logging.info(fig)
    # Configure resources to include BokehJS inline in the document.
    # For more details see:
    #   http://bokeh.pydata.org/en/latest/docs/reference/resources_embedding.html#bokeh-embed
    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()

    # For more details see:
    #   http://bokeh.pydata.org/en/latest/docs/user_guide/embedding.html#components
    script, div = components(fig, INLINE)

    return render_template(
            'embed.html',
            plot_script=script,
            plot_div=div,
            js_resources=js_resources,
            css_resources=css_resources)

def main():
    app.debug = True
    app.run()

if __name__ == "__main__":
    main()
