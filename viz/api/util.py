import os
from ..models import UserDB, VizCardDB, \
                   CompanyDB, UserDirectoryDB, AddressDB

# Return users by normal query
def get_users(limit, offset):
    return UserDB.query.limit(limit).offset(offset).all()


# Return cards by location query
def get_cards_by_location(lat, lng, radius, lim):
    query = "SELECT id, location, ( 3959 * acos( cos( radians( \
            %(latitude)s ) ) * cos( radians( lat ) ) * cos( radians( \
            lng ) - radians( %(longitude)s ) ) + sin( radians( \
            %(latitude)s ) ) * sin( radians( lat ) ) ) ) AS distance \
            FROM sightings HAVING distance < %(radius)s ORDER BY \
            distance LIMIT %(limit)s" % {"latitude": lat, \
            "longitude": lng, "radius": radius, "limit": lim}
    return VizCardDB.query.from_statement(query).all()


# Return cards by normal query
def get_cards(limit, offset):
    return VizCardDB.query.limit(limit).offset(offset).all()


# Return user's info including the path on the webserver to the user's profile picture
def get_user_json(user_email):
    if user_email is None:
        return None
    user = UserDB.query.filter_by(email=user_email).first()
    if user is None:
      return None
    return {'email': user.email,
            'name': user.name,
            'img_path': img_path }


# Return card info, including owner, contact address, phone, email, photo galleries, etc
def get_card_json(card):
    if card is None:
        return None
    if card.type is 0:
        type = "private"
    else:
        type = "public"
    address_json = get_address_json(card.address_id)
    company_json = get_company_json(card.company_email)
    return {'email': card.email,
            'name': card.name,
            'phone_num': card.phone_num,
            'logo_path': card.logo_path,
            'position': card.position,
            'views': card.views,
            'shares': card.shares,
            'verified': card.verified,
            'type': type,
            'address': address_json,
            'company': company_json }


# Return information regarding a company
def get_company_json(company_email):
    if company_email is None:
        return None
    company = CompanyDB.query.filter_by(email=company_email).first()
    if company is None:
        return None
    address_json = get_address_json(company.address_id)
    return {'name': company.name,
            'email': company.email,
            'website': company.website,
            'logo_path': company.logo_path,
            'phone_num': company.phone_num,
            'address': address_json }


def get_address_json(address_id):
    address = AddressDB.query.filter_by(address_id=address_id).first()
    if address is None:
        return None
    return {'Address 1': address.address1,
            'Address 2': address.address2,
            'City': address.city,
            'State': address.state,
            'Country': address.country,
            'Zipcode': address.zip }
