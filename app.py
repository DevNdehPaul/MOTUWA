from flask import Flask, render_template, request
app = Flask(__name__)
@app.route('/')
def homepage():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    return render_template('ContactSupport.html')

if __name__ == '__main__':
    app.run(debug=True)