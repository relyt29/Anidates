#!/usr/bin/env python3

from flask import Flask, render_template, request, redirect, g, url_for, session, jsonify, Response
#from werkzeug.middleware.proxy_fix import ProxyFix
from flask_discord import DiscordOAuth2Session, requires_authorization, Unauthorized
from flask_session import Session
#import os
from flask_cors import CORS
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
#os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "true"      # !! Only in development environment.
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.config['SESSION_TYPE'] = sekreti.SESSION_TYPE
app.config['SESSION_REDIS'] = sekreti.SESSION_REDIS
app.config['SECRET_KEY'] = sekreti.SECRET_KEY
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = sekreti.PERMANENT_SESSION_LIFETIME

app.config["DISCORD_CLIENT_ID"] = sekreti.DISCORD_CLIENT_ID
app.config["DISCORD_CLIENT_SECRET"] = sekreti.DISCORD_CLIENT_SECRET
app.config["DISCORD_REDIRECT_URI"] = sekreti.DISCORD_REDIRECT_URI

sess = Session()
discord = DiscordOAuth2Session(app)

logger = logging.basicConfig(level=logging.DEBUG,
                             filename="app.log",
                             filemode='a')
app.logger = logger
ANIMETAS_CONTRACT_ADDRESS = "0x18Df6C571F6fE9283B87f910E41dc5c8b77b7da5"
ANIMETAS_ABI = abis.animetas_abi
#CORS(app) # TODO scope to minimum scope necessary

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
    return db, db.cursor()



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



def is_valid_address(eth_address):
    """
    checks if an address is of the right structure to be an ethereum addresss
    :param address: the address to check
    :return:
    """
    web3_handle = get_web3()
    return web3_handle.isAddress(eth_address)

def to_checksum_address(eth_address):
    web3_handle = get_web3()
    return web3_handle.toChecksumAddress(eth_address)


def check_address_decorator(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        # Because the address is sometimes in args and sometimes in kwargs
        eth_address = None
        if 'eth_address' in kwargs:
            eth_address = kwargs['eth_address']
        else:
            eth_address = args[0]
        if not is_valid_address(eth_address):
            return render_template("error.html")
        return fn(*args, **kwargs)

    return wrapped


def check_session_authentication(session):
    def inner_function(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            if 'eth_address' in kwargs:
                eth_address = kwargs['eth_address']
            else:
                eth_address = args[0]
            #logging.debug("Address from wrapping")
            #logging.debug(eth_address)
            if session.get(eth_address) is None:
                #logging.debug("Session is not authenticated")
                return redirect(url_for('hello'))
            return function(*args, **kwargs)

        return wrapped

    return inner_function


@app.before_first_request
def init_application():
    sess.init_app(app)

@app.before_first_request
def init_db():
    db, cur = get_cursor()
    create_sql = """CREATE TABLE IF NOT EXISTS userprofiles(
                        eth_address TEXT NOT NULL UNIQUE,
                        token_id INTEGER,
                        name TEXT,
                        age INTEGER,
                        location TEXT,
                        profile_text TEXT
                    );"""
                        #UNIQUE (eth_address)
    cur.execute(create_sql)
    db.commit()

@app.route("/")
def hello():
    return render_template('index.html')

@app.route('/dbtest/<string:eth_address>')
@check_address_decorator
@check_session_authentication(session)
def dbtest(eth_address):
    _, cur = get_cursor()
    cur.execute('SELECT version()')
    db_version = cur.fetchone()
    return (str(db_version), 200)

@app.route("/discordant")
def discordant():
    data = discord.callback()
    user = discord.fetch_user()
    # there might be an attack here, maybe, I'm not sure
    # around using client-side provided info for the eth_address
    # but it might be hashed server side so we might be good?
    # idk, need to think more about it
    addy = str(data['eth_address'])
    session[addy] = str(user.id)
    url_construct = url_for('dashboard', eth_address=addy)
    return redirect(url_construct)

@app.errorhandler(Unauthorized)
def redirect_unauthorized(e):
    return redirect(url_for('hello'))

@app.route("/logout/<string:eth_address>")
@check_address_decorator
@check_session_authentication(session)
def logout(eth_address):
    # remove the key from the session
    session.pop(eth_address, None)
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
        address_returned = to_checksum_address(address_returned)
        if is_valid_address(request.json['address']):
            if address_returned == to_checksum_address(request.json['address']):
                # we've determined it's a valid signature on a real ETH address.
                animetas_contract = get_animetas_contract()
                try:
                    number_animetas_held = animetas_contract.functions.balanceOf(address_returned).call()
                    if number_animetas_held > 0:
                        redirect_obj = discord.create_session(scope=['identify'],data={"eth_address": address_returned})
                        return jsonify({'success': True, 'body': redirect_obj.location}), 200, {'ContentType':'application/json'}
                    else:
                        return jsonify({'body': 'Invalid user: You dont hold any animetas!'}), 400, {'ContentType':'application/json'}
                except:
                    return jsonify({'body': 'Some kind of error calling animetas contract, contact the devs'}), 500, {'ContentType':'application/json'}

        return jsonify({'body': 'Invalid user: ETH address signature invalid'}), 400, {'ContentType':'application/json'}

def write_db_user_profile(address, token_id, name, age, location, profile_text):
    db, cur = get_cursor()
    assert is_valid_address(address)
    insert_sql = """INSERT INTO userprofiles (
                        eth_address,
                        token_id,
                        name,
                        age,
                        location,
                        profile_text)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (eth_address)
                    DO
                    UPDATE SET
                    token_id=EXCLUDED.token_id,
                    name=EXCLUDED.name,
                    age=EXCLUDED.age,
                    location=EXCLUDED.location,
                    profile_text=EXCLUDED.profile_text;
                    """
    cur.execute(insert_sql,( address, token_id, name, age, location, profile_text))
    db.commit()


def new_animeta(address, animetas_contract):
    token_id = int(animetas_contract.functions.tokenOfOwnerByIndex(address, 0).call())
    name = "Animeta #{}".format(token_id)
    age = "1000"
    location = "The Metaverse"
    profile_text = "This is some default profile text. Why don't you edit it, eh?"
    write_db_user_profile(address, token_id, name, age, location, profile_text)
    return token_id, name, age, location, profile_text


# User profile is made up of:
# Public ETH Addr
# Animeta token ID
# Picture (indexed by token_id)
# Animeta user defined Name
# Animeta age
# Animeta location
# Animeta profile text.
def get_current_profile(address):
    _,cur = get_cursor()
    # should be sanitized for SQLI by psycopg2, using this syntax
    rows = cur.execute("SELECT token_id, name, age, location, profile_text FROM userprofiles WHERE eth_address = %s", (address,))
    if rows:
        assert len(rows) < 2 and len(rows) >= 0
    else:
        rows = []
    animetas_contract = get_animetas_contract()
    number_animetas_held = animetas_contract.functions.balanceOf(address).call()
    assert number_animetas_held > 0
    if len(rows) == 0:
        (token_id, name, age, location, profile_text) = new_animeta(address, animetas_contract)
    else:
        (token_id, name, age, location, profile_text) = rows[0]
        found = False
        for i in range(0, number_animetas_held-1):
            test_token_id = animetas_contract.functions.tokenOfOwnerByIndex(address, i).call()
            if test_token_id == token_id:
                found = True
        if not found:
            (token_id, name, age, location, profile_text) = new_animeta(address, animetas_contract)
    return token_id, name, age, location, profile_text






@app.route("/dashboard/<string:eth_address>")
@requires_authorization
@check_address_decorator
@check_session_authentication(session)
def dashboard(eth_address):
    (token_id, name, age, location, profile_text) = get_current_profile(eth_address)
    # jinja2 should sanitize XSS so we are good there
    return render_template('dashboard.html', token_id=token_id, name=name, age=age, location=location, profile_text=profile_text)



if __name__ == "__main__":
    # App is behind one proxy that sets the -For and -Host headers.
    #proxied_app = ProxyFix(app, x_for=1, x_host=1)
    # TODO: CSRF - flask.wtf etc
    #app.run(host='127.0.0.1', port=8080, debug=True)
    from waitress import serve
    serve(app, listen='127.0.0.1:8080', url_scheme='https')

