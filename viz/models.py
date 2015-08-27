from __init__ import app, db
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)


"""
There will be options on a business card view to "connect to company" and also
"inherit info from company" as in sync the logo, email, contact, address, gallery
There should be pages such as view-company, view-user, view-my-card-directory, etc.
"""


class UserDB(db.Model):
    """User object stores all necessary information for a site user.
    """
    __tablename__ = 'users'
    email = db.Column(db.String(50), primary_key=True, index=True, nullable=False)
    name = db.Column(db.String(50))
    img_path = db.Column(db.String(50))
    pass_hash = db.Column(db.String(128))

    def hash_password(self, password):
        self.pass_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.pass_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'email': self.email})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None # valid token, but expired
        except BadSignature:
            return None # invalid token
        user = UserDB.query.get(data['email'])
        return user


class VizCardDB(db.Model):
    """Card object stores all necessary information for a card on the app
    card_id     : integer   -> primary key
    email       : string    -> owner of the card, not required
    position    : string    -> position in the company
    address_id  : integer   -> foreignkey into address DB, company addr by default
    phone_num   : string    -> part of the contact info
    email       : string    -> part of the contact info
    verified    : string    -> did the user confirm that this is his/her card?
    company_email : string  -> foreignkey into company DB
    logo_path   : string    -> URL path for the image
    type        : integer   -> 1 for public, 0 for private
    """
    __tablename__ = 'cards'
    card_id = db.Column(db.Integer, primary_key=True, nullable=False)
    email = db.Column(db.String(50), db.ForeignKey('users.email'))
    address_id = db.Column(db.Integer, db.ForeignKey('addresses.address_id'))
    company_email = db.Column(db.String(50), db.ForeignKey('companies.email'))
    logo_path = db.Column(db.String(50))
    position = db.Column(db.String(50), nullable=False)
    type = db.Column(db.Integer, nullable=False)
    verified = db.Column(db.Integer, nullable=False)
    phone_num = db.Column(db.String(30))
    website = db.Column(db.String(50))
    views = db.Column(db.Integer)
    shares = db.Column(db.Integer)


class UserDirectoryDB(db.Model):
    """User specific information regarding various business cards
    name        : string    -> unique identifier of the directory
    email       : string    -> foreignkey to the owner's profile
    card_id     : integer   -> foreignkey to a specific viz card
    address_id  : integer   -> foreignkey to the address of where these people met
    notes       : string    -> customized notes a user has about a specific card
    """
    __tablename__ = 'userdir'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(200),  nullable=False)
    email = db.Column(db.String(50), db.ForeignKey('users.email'), nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey('cards.card_id'), nullable=False)
    address_id = db.Column(db.Integer, db.ForeignKey('addresses.address_id'))
    notes = db.Column(db.String(500))


class CompanyDB(db.Model):
    """Company info object
    """
    __tablename__ = 'companies'
    email = db.Column(db.String(50), primary_key=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    website = db.Column(db.String(100), nullable=False)
    logo_path = db.Column(db.String(50))
    address_id = db.Column(db.Integer, db.ForeignKey('addresses.address_id'))
    phone_num = db.Column(db.String(30))
    # Insert closest address list


class AddressDB(db.Model):
    """Address object to store necessary information. All cards have this.
    latitude and longitude are used for actual interaction.
    all other fields are for GUI and user responsiveness
    """
    __tablename__ = 'addresses'
    address_id = db.Column(db.Integer, primary_key=True, nullable=False)
    address1 = db.Column(db.String(50))
    address2 = db.Column(db.String(50))
    city = db.Column(db.String(25))
    state = db.Column(db.String(25))
    country = db.Column(db.String(50))
    zip = db.Column(db.String(25))
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
