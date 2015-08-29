#!venv/bin/python
from flask import request, jsonify, url_for, abort, g, redirect
from util import *
from ..__init__ import app, auth
from ..models import *
import boto
import random, string


# Testing a resource with login_required
@app.route('/resource')
@app.route('/resource/')
@auth.login_required # Leads to verify_password decorator
def get_resource():
    return jsonify({'data': "Hello, %s!" % g.user.email})


# Route to get an authentication token
@app.route('/token')
@app.route('/token/')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({"token": token.decode('ascii')})


# Get: return users with limit or offset fields.
# Post: user registration
@app.route('/users', methods=['POST','GET'])
@app.route('/users/', methods=['POST','GET'])
def users():
    if request.method == 'GET':
        lim = request.args.get('limit', 100)
        off = request.args.get('offset', 0)
        users = get_users(limit=lim, offset=off)
        json_results = map(get_user_json, (user.email for user in users))
        print json_results
        return jsonify(users=json_results)
    if request.method == 'POST':
        name = request.json.get('name')
        email = request.json.get('email')
        password = request.json.get('password')
        img_path = request.json.get('img_path')
        if email is None:
            return "1" # missing arguments
        user_obj = UserDB.query.filter_by(email=email).first()
        if user_obj is not None:
            user_obj.name = user_obj.name if name is None else name
            user_obj.email = user_obj.email if email is None else email
            if password is not None:
                user_obj.hash_password(password)
            user_obj.img_path = user_obj.img_path if img_path is None else img_path
            db.session.commit()
            return "Edited" # user already exists in db
        else:
            return "Bad Request"
        user = UserDB(email=email, name=name, img_path=img_path)
        user.hash_password(password)
        db.session.add(user)
        db.session.commit()
        return jsonify({'email': user.email}), 201, {'Location': \
                url_for('user', email=user.email, _external=True)}


# Get a single user by email
@app.route('/users/<email>', methods=['GET'])
@app.route('/users/<email>/', methods=['GET'])
def user(email):
    if request.method == 'GET':
        print email
        user = UserDB.query.filter_by(email=email).first()
        return jsonify(user=get_user_json(user))


@app.route('/cards', methods=['POST','GET'])
@app.route('/cards/', methods=['POST','GET'])
def cards():
    if request.method == 'GET':
        lim = request.args.get('limit', 100)
        off = request.args.get('offset', 0)

        # Use this when GMap API geocoding is integrated to search by location.
        # /api/cards/?location=33.3942655,-104.5230242&radius=10 example GET
        radius = request.args.get('radius', 10)
        location = request.args.get('location', ',')
        lat, lng = location.split(',')

        if lat and lng and radius:
            all_cards = get_cards_by_location(lat, lng, radius, lim)
        else:
            all_cards = get_cards(limit=lim, offset=off)

        json_cards = map(get_card_json, all_cards)
        return jsonify(cards=json_cards)
    if request.method == 'POST':
        # Not nullable
        email = request.json.get('email')
        position = request.json.get('position')
        type = request.json.get('type')
        # Nullable
        website = request.json.get('website')
        phone_num = request.json.get('phone_num')
        company_email = request.json.get('company_email')
        # True or false, does the request contain an address?
        has_address = request.json.get('has_address')
        # Gallery_id will usually be None. People can still share a gallery_id
        # to their friends so others can have the same gallery
        logo_path = request.json.get('logo_path')
        company = None
        address_id = None

        if email is None or position is None or type is None:
            abort(400) # missing arguments
        if UserDB.query.filter_by(email=email).first() is None:
            abort(400) # card must have an existing owner

        if company_email is not None:
            company = CompanyDB.query.filter_by(company_email=company_email).first()
            if company is None:
                abort(400) # Not a real company
            logo_id = company.logo_id

        if has_address:
            address1 = request.json.get('address1')
            address2 = request.json.get('address2')
            city = request.json.get('city')
            state = request.json.get('state')
            country = request.json.get('country')
            zip = request.json.get('zip')
            if address1 is None or city is None or state is None\
                    or country is None or zip is None:
                abort(400) # missing arguments for address
            # Query database for duplicate addresses
            address = AddressDB.query.filter_by(
                      address1=address1, address2=address2, city=city,
                      state=state, country=country, zip=zip).first()
            if not address: # New address
                address = AddressDB(address1=address1, address2=address2,
                            city=city, state=state, country=country, zip=zip)
                db.session.add(address)
            address_id = address.address_id
        else:
            if company is not None:
                address_id = company.address_id # Default address is company's

        card = VizCardDB(email=email, address_id=address_id,
                         company_email=company_email,
                         position=position, type=type,
                         phone_num=phone_num, website=website,
                         views=0, shares=0, verified=0)

        db.session.add(card)
        db.session.commit()
        return jsonify(get_card_json(card)), 201, {'Location': \
                url_for('card', email=card.email, _external=True)}

# TEST THAT SHIT OUT ^


# By individual email
@app.route('/cards/<email>', methods=['GET'])
@app.route('/cards/<email>/', methods=['GET'])
def card(email):
    if request.method == 'GET':
        cards = VizCardDB.query.filter_by(email=email).all()
        json_results = map(get_card_json, cards)
        return jsonify(cards=json_results)


# Get and post to all companies
@app.route('/companies', methods=['POST','GET'])
@app.route('/companies/', methods=['POST','GET'])
def companies():
    if request.method == 'GET':
        # MAKE THIS EFFICIENT
        companies = CompanyDB.query.all()
        json_companies = map(get_company_json, map(lambda x: x.email, companies))
        return jsonify(companies=json_companies)
    if request.method == 'POST':
        # Not nullable
        email = request.json.get('email')
        name = request.json.get('name')
        # Nullable
        website = request.json.get('website')
        phone_num = request.json.get('phone_num')
        # True or false, does the request contain an address?
        has_address = request.json.get('has_address')
        address_id = request.json.get('address_id')
        # Usually None. Upload logo in a later registration page.
        logo_path = request.json.get('logo_path')

        if name is None or email is None:
            abort(400) # missing argument
        if CompanyDB.query.filter_by(name=name).first() is not None:
            abort(400) # cannot have duplicate company

        if gallery_id is None:
            new_gallery = GalleryDB() # Assign new company a new gallery
            gallery_id = new_gallery.gallery_id
            db.session.add(new_gallery)

        if has_address:
            address1 = request.json.get('address1')
            address2 = request.json.get('address2')
            city = request.json.get('city')
            state = request.json.get('state')
            country = request.json.get('country')
            zip = request.json.get('zip')
            if address1 is None or city is None or state is None\
                    or country is None or zip is None:
                abort(400) # missing arguments for address
            # Query database for duplicate addresses
            address = AddressDB.query.filter_by(
                      address1=address1, address2=address2, city=city,
                      state=state, country=country, zip=zip).first()
            if not address: # New address
                address = AddressDB(address1=address1, address2=address2,
                            city=city, state=state, country=country, zip=zip)
                db.session.add(address)
            address_id = address.address_id

        company = CompanyDB(name=name, address_id=address_id,
                            gallery_id=gallery_id, logo_id=logo_id,
                            phone_num=phone_num, email=email, website=website)

        db.session.add(company)
        db.session.commit()
        return jsonify(get_card_json(card)), 201, {'Location': \
                url_for('company', company_name=company.name, _external=True)}

# TEST THIS SHIT TOO ^


# Search for info for one company
@app.route('/companies/<company_name>', methods=['GET'])
@app.route('/companies/<company_name>/', methods=['GET'])
def company(company_name):
    if request.method == 'GET':
        company = CompanyDB.query.filter_by(name=company_name).first()
        return jsonify(company=get_company_json(company))


# Search for cards related to one company
@app.route('/companies/<company_name>/cards', methods=['GET'])
@app.route('/companies/<company_name>/cards/', methods=['GET'])
def company_users(company_name):
    if request.method == 'GET':
        if CompanyDB.query.filter_by(name=company_name).first() is None:
            return None # not a real company
        cards = VizCardDB.query.filter_by(company_name=company_name).all()
        json_cards = map(get_card_json, cards)
        return jsonify(cards=json_cards)

# Decorator for UserDB.verify_password
@auth.verify_password
def verify_password(email_or_token, password):
    # first try to authenticate the token
    user = UserDB.verify_auth_token(email_or_token)
    if not user:
        # try to authenticate with email and password
        user = UserDB.query.filter_by(email=email_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


# Uploads an image to AWS and returns a file url
@app.route('/upload/image/', methods=['POST'])
@app.route('/upload/image', methods=['POST'])
def upload_image():
    if request.method == 'POST':
        s3 = boto.connect_s3()
        #get file from POST request
        data = request.files['file']
        #generate a random file name, 50 chars
        filename = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(50))
        extension = data.filename.split('.',1)[1]
        filename = filename + '.' + extension
        bucket = s3.get_bucket('vizimages')
        key = bucket.new_key(filename)
        #put file into key
        key.set_contents_from_file(data)
	type = request.form.get('type')
        #put data into user
	if type == 'user':
	   email = request.form.get('email')
	   user = UserDB.query.filter_by(email=email).first()
	   user.img_path = filename
	   db.session.commit()
        #put datas into card
        else:
	   card_id = request.form.get('card_id')
	   card = VizCardDB.query.filter_by(card_id=card_id).first()
	   card.logo_path = filename
           db.session.commit()
        return filename



# Gets an image from AWS servers
@app.route('/images/<file_name>', methods=['GET'])
def get_image(file_name):
    if request.method == 'GET':
        s3 = boto.connect_s3()
        #get aws bucket (are you happy, sakib?)
        bucket = s3.get_bucket('vizimages')
        #find key with matching identifier
        key = bucket.get_key(file_name)
        #check if key exists
        exists = not key is None
        if exists:
            return redirect(key.generate_url(10))
        #404, needs to be replaced later
        else:
            return redirect('http://i.imgur.com/gOQCJxw.png')

# User Directory GET ALL and POST ONE
@app.route('/user_directory', methods=['POST', 'GET'])
@app.route('/user_directory/', methods=['POST', 'GET'])
def user_directories():
    if request.method == 'GET':
        userdirs = UserDirectoryDB.query.all()
        json_userdirs = map(get_userdir_json, map(lambda x: x.id, userdirs))
        return jsonify(userdirs=json_userdirs)

    if request.method == 'POST':
        name = request.json.get('name')
        email = request.json.get('email')
        card_id = request.json.get('card_id')
        address_id = request.json.get('address_id')
        notes = request.json.get('notes')
        if name is None or email is None or card_id is None or address_id is None:
            abort(400)
        if notes is None:
            notes = ''
        dire = UserDirectoryDB(name=name, email=email, card_id=card_id, address_id=address_id, notes=notes)
        db.session.add(dire)
        db.session.commit()
        return jsonify({"name": dire.name})


# Search for user directories pertaining to one user
@app.route('/user_directory/<user_email>', methods=['GET'])
@app.route('/user_directory/<user_email>/', methods=['GET'])
def user_directory(user_email):
    if request.method == 'GET':
        user_dirs = UserDirectoryDB.query.filter_by(email=user_email).all()
        json_userdirs = map(get_userdir_json, map(lambda x: x.id, userdirs))
        return jsonify(userdirs=json_userdirs)


# Search for cards related to one company

# TODO: TESTING SHIT ABOVE. ALSO CREATE USERDIR API FOR INDIVIDUAL CARD notes
