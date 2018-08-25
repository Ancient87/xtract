from flask import (
        Flask,
        render_template,
)
import connexion
from connexion.resolver import  RestyResolver
from flask_cors import CORS
import os
import api
from collections import defaultdict

APP_HOST = os.environ['APP_HOST']
APP_PORT = os.environ['APP_PORT']

app = connexion.App(__name__, specificatyion_dir="./")

app.add_api('xtract_api_spec.yaml', resolver=RestyResolver('api'))
application = app.app

@app.route('/')
def home():
    """
    Hello world @ 5000
    """
    return api.stockdata.get('acn')
    return render_template('home.html')

'''
@app.cli.command()
def routes():
    'Display registered routes'
    rules = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods))
        rules.append((rule.endpoint, methods, str(rule)))

    sort_by_rule = operator.itemgetter(2)
    for endpoint, methods, rule in sorted(rules, key=sort_by_rule):
        route = '{:50s} {:25s} {}'.format(endpoint, methods, rule)
        print(route)
'''

def list_routes():
    """
        Roll through Flask's URL rules and print them out
        Thank you to Jonathan Tushman
            And Thank you to Roger Pence
            Sourced http://flask.pocoo.org/snippets/117/ "Helper to list routes (like Rail's rake routes)"
        Note that a lot has possibly changed since that snippet and rule classes have a __str__
            which greatly simplifies all of this
    """

    format_str = lambda *x: "{:30s} {:40s} {}".format(*x)  # pylint: disable=W0108
    clean_map = defaultdict(list)

    for rule in application.url_map.iter_rules():
        methods = ",".join(rule.methods)
        clean_map[rule.endpoint].append((methods, str(rule),))

    print(format_str("View handler", "HTTP METHODS", "URL RULE"))
    print("-" * 80)
    for endpoint in sorted(clean_map.keys()):
        for rule, methods in sorted(clean_map[endpoint], key=lambda x: x[1]):
            print(format_str(endpoint, methods, rule))

if __name__ == '__main__':
    list_routes()
    app.run(host=APP_HOST, port=APP_PORT, debug=True)
