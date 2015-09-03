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


# Get:  return users with limit or offset fields.
# Post: creates a new user
@app.route('/users', methods=['POST','GET'])
@app.route('/users/', methods=['POST','GET'])
def users():
    if request.method == 'GET': # take limits or offsets
        lim = request.args.get('limit', 100)
        off = request.args.get('offset', 0)
        users = get_users(limit=lim, offset=off)
        json_results = map(get_user_json, (user.email for user in users))
        return jsonify(users=json_results)
    if request.method == 'POST': # create new user
        name = request.json.get('name')
        email = request.json.get('email')
        password = request.json.get('password')
        img_path = request.json.get('img_path')
        if email is None or password is None: # missing args.
            return "Missing arguments"
        user = UserDB(email=email, name=name, img_path=img_path)
        user.hash_password(password)
        db.session.add(user)
        db.session.commit()
        return jsonify({'email': user.email}), 201, {'Location': \
                url_for('user', email=user.email, _external=True)}
    return "Bad request"


# Get:  returns info on a single user
# Post: edits an existing user
@app.route('/users/<email>', methods=['GET','POST'])
@app.route('/users/<email>/', methods=['GET','POST'])
def user(email):
    if request.method == 'GET': # return user info
        return jsonify(user=get_user_json(email))
    if request.method == 'POST': # edit user
        user = UserDB.query.filter_by(email=email).first()
        if user is None:
            return "A user by that email not exist"
        user.name = request.json.get('name')
        user.img_path = request.json.get('img_path')
        user.hash_password(request.json.get('password'))
        db.session.commit()
        return jsonify({'email': user.email}), 201, {'Location': \
                url_for('user', email=user.email, _external=True)}
    return "Bad request"


# Get:  return cards with limit or offset fields. Also by radius+lat+long
# Post: creates a new card
@app.route('/cards', methods=['POST','GET'])
@app.route('/cards/', methods=['POST','GET'])
def cards():
    if request.method == 'GET': # return all cards based on location or lim/off
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
    if request.method == 'POST': # create new card
        position = request.json.get('position')
        type = request.json.get('type')
        verified = request.json.get('verified')
        email = request.json.get('email')
        website = request.json.get('website')
        phone_num = request.json.get('phone_num')
        company_email = request.json.get('company_email')
        logo_path = request.json.get('logo_path')

        latitude = request.json.get('latitude')
        longitude = request.json.get('longitude')
        address1 = request.json.get('address1')
        address2 = request.json.get('address2')
        city = request.json.get('city')
        state = request.json.get('state')
        country = request.json.get('country')
        zip = request.json.get('zip')

        if email is None or position is None or type is None\
                or latitude is None or longitude is None:
            return "Missing arguments" # missing arguments

        # query database for duplicate addresses
        address = AddressDB.query.filter_by(latitude=latitude,
            longitude=longitude, address1=address1, address2=address2,
            city=city, state=state, country=country, zip=zip).first()

        if not address: # create new address
            address = AddressDB(address1=address1, address2=address2,
                city=city, state=state, country=country, zip=zip,
                latitude=latitude, longitude=longitude)
            db.session.add(address)

        card = VizCardDB(email=email, address_id=address.address_id,
                         company_email=company_email, logo_path=logo_path,
                         position=position, type=type,
                         phone_num=phone_num, website=website,
                         views=0, shares=0, verified=0)

        db.session.add(card)
        db.session.commit()
        return jsonify(get_card_json(card)), 201, {'Location': \
                url_for('card', email_or_card_id=card.email, _external=True)}


# Get:  returns info on the cards owned by a user
# Post: edits an existing user
@app.route('/cards/<email_or_card_id>', methods=['GET'])
@app.route('/cards/<email_or_card_id>/', methods=['GET'])
def card(email_or_card_id):

    if request.method == 'GET': # get cards by card_id, then owner's email
        card = VizCardDB.query.filter_by(card_id=email_or_card_id).first()
        if card is None: # try searching by email
            cards = VizCardDB.query.filter_by(email=email).all()
            return jsonify(cards=map(get_card_json, cards))
        return jsonify(card=map(get_card_json, card))

    if request.method == 'POST': # edit cards by owner
        card_id = request.json.get('card_id')
        if card_id is None:
            return "Missing arguments"

        # Edit the card
        card = VizCardDB.query.filter_by(card_id=card_id).first()

        position = request.json.get('position')
        type = request.json.get('type')
        verified = request.json.get('verified')

        if position is not None:
            card.position = position
        if type is not None:
            card.type = type
        if verified is not None:
            card.verified = verified

        card.email = request.json.get('email')
        card.website = request.json.get('website')
        card.phone_num = request.json.get('phone_num')
        card.company_email = request.json.get('company_email')
        card.logo_path = request.json.get('logo_path')

        # Edit card address
        address = AddressDB.query.filter_by(address_id=card.address_id).first()

        latitude = request.json.get('latitude')
        longitude = request.json.get('longitude')

        if latitude is not None and longitude is not None:
            address.latitude = latitude
            address.longitude = longitude
            address.address1 = request.json.get('address1')
            address.address2 = request.json.get('address2')
            address.city = request.json.get('city')
            address.state = request.json.get('state')
            address.country = request.json.get('country')
            address.zip = request.json.get('zip')

        db.session.commit()

        return jsonify(get_card_json(card)), 201, {'Location': \
                url_for('card', email_or_card_id=card.email, _external=True)}

    return "Bad request"


# Get:  return all companies by lim/off.
# Post: creates a new company
@app.route('/companies', methods=['POST','GET'])
@app.route('/companies/', methods=['POST','GET'])
def companies():

    if request.method == 'GET': # return companies by limit and/or offset
        lim = request.args.get('limit', 100)
        off = request.args.get('offset', 0)
        companies = CompanyDB.query.limit(limit).offset(offset).all()
        return jsonify(companies=map(get_company_json, map(lambda x: x.email, companies)))

    if request.method == 'POST':

        email = request.json.get('email')
        name = request.json.get('name')
        website = request.json.get('website')
        phone_num = request.json.get('phone_num')
        logo_path = request.json.get('logo_path')

        latitude = request.json.get('latitude')
        longitude = request.json.get('longitude')
        address1 = request.json.get('address1')
        address2 = request.json.get('address2')
        city = request.json.get('city')
        state = request.json.get('state')
        country = request.json.get('country')
        zip = request.json.get('zip')

        if email is None or name is None or website is None\
                or latitude is None or longitude is None:
            return "Missing arguments" # missing args in request
        if UserDB.query.filter_by(email=email).first() is None:
            return "User by that email does not exist"
        if CompanyDB.query.filter_by(name=name).first() is not None:
            return "Company with that name already exists"

        # query database for duplicate addresses
        address = AddressDB.query.filter_by(latitude=latitude,
            longitude=longitude, address1=address1, address2=address2,
            city=city, state=state, country=country, zip=zip).first()

        if not address: # create new address
            address = AddressDB(address1=address1, address2=address2,
                city=city, state=state, country=country, zip=zip,
                latitude=latitude, longitude=longitude)
            db.session.add(address)

        company = CompanyDB(email=email, name=name, website=website,
                            logo_path=logo_path, phone_num=phone_num,
                            address_id=address.address_id)

        db.session.add(company)
        db.session.commit()

        return jsonify(get_card_json(card)), 201, {'Location': \
                url_for('company', company_name=company.name, _external=True)}

    return "Bad request"


# Get:  returns info on a company by a name
# Post: edits an existing company
@app.route('/companies/<company_name>', methods=['GET'])
@app.route('/companies/<company_name>/', methods=['GET'])
def company(company_name):
    if request.method == 'GET': # return info on company by name
        company = CompanyDB.query.filter_by(name=company_name).first()
        if company is None: # does not exist
            return "A company by that name does not exist"
        return jsonify(company=get_company_json(company))
    if request.method == 'POST': # edit company by that name
        # Authentication to be done later
        name = request.json.get('name')
        email = request.json.get('email')
        website = request.json.get('website')

        if name is None:
            return "Missing arguments"

        company = CompanyDB.query.filter_by(name=name).first()

        if company is None: # company to edit must exist
            return "A company by that name does not exist"
        if email is not None: # check for auth here
            company.email = email
        if website is not None: # not nullable
            company.website = website

        company.phone_num = request.json.get('phone_num')
        company.logo_path = request.json.get('logo_path')

        # Edit company address
        address = AddressDB.query.filter_by(address_id=company.address_id).first()

        latitude = request.json.get('latitude')
        longitude = request.json.get('longitude')

        if latitude is not None and longitude is not None:
            address.latitude = latitude
            address.longitude = longitude
            address.address1 = request.json.get('address1')
            address.address2 = request.json.get('address2')
            address.city = request.json.get('city')
            address.state = request.json.get('state')

        db.session.commit()

        return jsonify(get_company_json(company.email)), 201, {'Location': \
                url_for('company', company_name=company.name, _external=True)}

    return "Bad request"


# Get:  search for cards related to one company
@app.route('/companies/<company_name>/cards', methods=['GET'])
@app.route('/companies/<company_name>/cards/', methods=['GET'])
def company_users(company_name):
    if request.method == 'GET':
        company = CompanyDB.query.filter_by(name=company_name).first()
        if company is None: # does not exist
            return "A company by that name does not exist"
        cards = VizCardDB.query.filter_by(company_email=company.email).all()
        return jsonify(cards=map(get_card_json, cards))


# Get:  return user_directories by lim/off
# Post: creates a new user_directory
@app.route('/user_directory', methods=['POST', 'GET'])
@app.route('/user_directory/', methods=['POST', 'GET'])
def user_directories():
    if request.method == 'GET': # get all userdirs by lim/off
        lim = request.args.get('limit', 100)
        off = request.args.get('offset', 0)
        userdirs = UserDirectoryDB.query.limit(lim).offset(off).all()
        json_userdirs = map(get_userdir_json, map(lambda x: x.id, userdirs))
        return jsonify(userdirs=json_userdirs)

    if request.method == 'POST': # create a userdir entry
        name = request.json.get('name')
        email = request.json.get('email')
        notes = request.json.get('notes')
        card_id = request.json.get('card_id') # send id of card to connect to

        if name is None or email is None or card_id is None:
            return "Missing arguments"
        if notes is None:
            notes = ''

        latitude = request.json.get('latitude')
        longitude = request.json.get('longitude')
        address1 = request.json.get('address1')
        address2 = request.json.get('address2')
        city = request.json.get('city')
        state = request.json.get('state')
        country = request.json.get('country')
        zip = request.json.get('zip')

        # query database for duplicate addresses
        address = AddressDB.query.filter_by(latitude=latitude,
            longitude=longitude, address1=address1, address2=address2,
            city=city, state=state, country=country, zip=zip).first()

        if not address: # create new address
            address = AddressDB(address1=address1, address2=address2,
                city=city, state=state, country=country, zip=zip,
                latitude=latitude, longitude=longitude)
            db.session.add(address)

        udir = UserDirectoryDB(name=name, email=email, card_id=card_id,
                               address_id=address.address_id, notes=notes)
        db.session.add(udir)
        db.session.commit()

        return jsonify(get_userdir_json(udir.id)), 201, {'Location': \
                url_for('user_directory', user_email_or_id=udir.id, _external=True)}

    return "Bad request"

# Get:  returns info on a user_directory by email
# Post: edits an existing user_directory
@app.route('/user_directory/<user_email_or_id>', methods=['GET'])
@app.route('/user_directory/<user_email_or_id>/', methods=['GET'])
def user_directory(user_email):
    if request.method == 'GET': # get a bunch of userdirs by email
        udir = UserDirectoryDB.query.filter_by(user_email_or_id).first()
        if udir is None:
            udirs = UserDirectoryDB.query.filter_by(email=user_email_or_id).all()
            return jsonify(user_dirs=map(get_userdir_json, map(lambda x: x.id, userdirs)))
        return jsonify(user_dir=get_userdir_json(udir.id))

    if request.method == 'POST': # edit a current userdir by user_directory id
        # to do: allow removal of userdirs
        udir_id = request.json.get('udir_id')
        if udir_id is None:
            return "Missing arguments"

        # Edit the udir
        udir = VizCardDB.query.filter_by(id=udir_id).first()

        if udir is None:
            return "A user directory by that id does not exist"

        # If delete flag is yes, delete from DB.
        delete = request.json.get('delete')
        if request.json.get('delete') == "yes":
            email = udir.email
            db.session.delete(udir)
            db.session.commit()
            return jsonify(get_userdir_json(udir_id)), 201, {'Location': \
                url_for('user_directory', user_email_or_id=email, _external=True)}

        udir.notes = request.json.get('notes')
        name = request.json.get('name')
        if name is not None:
            udir.name = name

        # Edit udir address
        address = AddressDB.query.filter_by(address_id=udir.address_id).first()

        latitude = request.json.get('latitude')
        longitude = request.json.get('longitude')

        if latitude is not None and longitude is not None:
            address.latitude = latitude
            address.longitude = longitude
            address.address1 = request.json.get('address1')
            address.address2 = request.json.get('address2')
            address.city = request.json.get('city')
            address.state = request.json.get('state')
            address.country = request.json.get('country')
            address.zip = request.json.get('zip')

        db.session.commit()

        return jsonify(get_userdir_json(udir.id)), 201, {'Location': \
                url_for('user_directory', user_email_or_id=udir.id, _external=True)}

    return "Bad request"


############ ABOVE DONE BUT NOT TESTED ############

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
