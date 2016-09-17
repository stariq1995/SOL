from flask import Flask
import argparse

app = Flask(__name__)

@app.route('/api/v1/compose')
def compose(apps, topology, mode, epoch_mode='max', fairness_mode='weighted'):
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path-dir', required=True)
    options = parser.parse_args()
    app.run(debug=True)

