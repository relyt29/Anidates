#!/usr/bin/env python3

from flask import Flask, render_template, request, redirect, g, url_for, session, jsonify, Response
from flask_session import Session
from functools import wraps
import logging
import sekreti
import abis
import redis

from web3 import Web3
from eth_account.messages import encode_defunct
from eth_account import Account
import psycopg2

from hexbytes import HexBytes

app = Flask(__name__)
app.config.from_object(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.config['SESSION_TYPE'] = sekreti.SESSION_TYPE
app.config['SESSION_REDIS'] = sekreti.SESSION_REDIS
app.config['SECRET_KEY'] = sekreti.SECRET_KEY
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = sekreti.PERMANENT_SESSION_LIFETIME
sess = Session()

logger = logging.basicConfig(level=logging.DEBUG,
                             filename="app.log",
                             filemode='a')
app.logger = logger
ANIMETAS_CONTRACT_ADDRESS = "0x18Df6C571F6fE9283B87f910E41dc5c8b77b7da5"
ANIMETAS_ABI = abis.animetas_abi


def get_db():
    """
    gets the DB from the flask global context.
    :return: db handle
    """
    db = getattr(g, '_database', None)
    if db is None:
        connect_string = "dbname={} user={} password={} host=localhost".format(
                sekreti.DB_NAME, sekreti.DB_USERNAME, sekreti.DB_PASSWORD)
        db = g._database = psycopg2.connect(connect_string)
    return db

def get_cursor():
    """
    gets the cursor from the db handle
    :return: cursor that can be used to query db
    """
    db = get_db()
    return db.cursor()



def get_web3():
    w3 = getattr(g, '_web3handle', None)
    if w3 is None:
        w3 = sekreti.get_web3_provider()
        g._web3handle = w3
    return w3

def get_animetas_contract():
    animetas_contract = getattr(g, '_animetascontract', None)
    if animetas_contract is None:
        w3 = get_web3()
        animetas_contract = w3.eth.contract(address=ANIMETAS_CONTRACT_ADDRESS, abi=ANIMETAS_ABI)
        g._animetascontract = animetas_contract
    return animetas_contract



def is_valid_address(address):
    """
    checks if an address is of the right structure to be an ethereum addresss
    :param address: the address to check
    :return:
    """
    web3_handle = get_web3()
    return web3_handle.isAddress(address)


def check_address_decorator(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        # Because the address is sometimes in args and sometimes in kwargs
        address = None
        if 'address' in kwargs:
            address = kwargs['address']
        else:
            address = args[0]
        if not is_valid_address(address):
            return render_template("error.html")
        return fn(*args, **kwargs)

    return wrapped


def check_session_authentication(session):
    def inner_function(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            if 'address' in kwargs:
                address = kwargs['address']
            else:
                address = args[0]
            #logging.debug("Address from wrapping")
            #logging.debug(address)
            if session.get(address.lower()) is None:
                #logging.debug("Session is not authenticated")
                return redirect(url_for('hello'))
            return function(*args, **kwargs)

        return wrapped

    return inner_function


@app.before_first_request
def init_application():
    sess.init_app(app)


@app.route("/")
def hello():
    return render_template('index.html')

@app.route('/dbtest/<string:address>')
@check_address_decorator
@check_session_authentication(session)
def dbtest(address):
    cur = get_cursor()
    cur.execute('SELECT version()')
    db_version = cur.fetchone()
    return (str(db_version), 200)



@app.route("/logout/<string:address>")
@check_address_decorator
@check_session_authentication(session)
def logout(address):
    # remove the key from the session
    session.pop(address.lower(), None)
    return redirect(url_for('hello'))

@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404



@app.route("/authenticate/", methods=['GET', 'POST'])
def authenticate():
    if request.method == 'POST':
        message_str = request.json['message']
        message = encode_defunct(text=message_str)
        signature = bytes.fromhex(str(request.json['signature'])[2:])
        logging.debug(message)
        logging.debug(signature)
        address_returned = Account.recover_message(message, signature=signature)
        if address_returned.lower() == request.json['address'].lower():
            # we've determined it's a valid signature on a real ETH address.
            animetas_contract = get_animetas_contract()
            try:
                number_animetas_held = animetas_contract.functions.balanceOf(address_returned).call()
                if number_animetas_held > 0:
                    session[address_returned.lower()] = 'in-session'
                    return jsonify({'success': True, 'body': address_returned.lower()}), 200, {'ContentType':'application/json'}
                else:
                    return jsonify({'body': 'Invalid user: You dont hold any animetas!'}), 400, {'ContentType':'application/json'}
            except:
                return jsonify({'body': 'Some kind of error calling animetas contract, contact the devs'}), 500, {'ContentType':'application/json'}

        else:
            return jsonify({'body': 'Invalid user: ETH address signature invalid'}), 400, {'ContentType':'application/json'}


@app.route("/dashboard/<string:address>")
@check_address_decorator
@check_session_authentication(session)
def dashboard(address):
    return render_template('dashboard.html', address=address)


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080, debug=True)

