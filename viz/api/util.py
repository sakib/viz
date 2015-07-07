import os
from ..models import UserDB, VizCardDB, ImageDB, UserDirectoryDB,\
                   CompanyDB, GalleryDB, ImageDB, AddressDB

# Return user's info including the path on the webserver to the user's profile picture
def get_user_json(user):
    if user is None:
        return None
    img_path = get_image_path(user.img_id, os.path.join("users", user.email))
    return {'email': user.email,
            'name': user.name,
            'email': user.email,
            'img_path': img_path}


# Return card info, including owner, contact address, phone, email, photo galleries, etc
def get_card_json(card):
    if card is None:
        return None
    if card.type is 0:
        type = "private"
    else:
        type = "public"
    address_json = get_address_json(card.address_id)
    logo_path = get_image_path(card.logo_id, card.email)
    gallery_json = get_gallery_json(card.gallery_id)
    company = CompanyDB.query.filter_by(name=card.company_name).first()
    company_json = get_company_json(company)
    return {'email': card.email,
            'email': card.email,
            'phone_num': card.phone_num,
            'address': address_json,
            'galleries': gallery_json,
            'company': company_json,
            'logo_path': logo_path,
            'position': card.position,
            'type': type }


# Return information regarding a company
def get_company_json(company):
    if company is None:
        return None
    address_json = get_address_json(company.address_id)
    gallery_json = get_gallery_json(company.gallery_id)
    logo_path = get_image_path(company.logo_id,\
                os.path.join("companies", company.name))
    return {'name': company.name,
            'logo_path': logo_path,
            'address': address_json,
            'gallery': gallery_json,
            'email': company.email,
            'phone_num': company.phone_num }


def get_gallery_json(gallery_id):
    gallery = GalleryDB.query.filter_by(gallery_id=gallery_id).first()
    if gallery:
        img1_path = get_image_path(gallery.image_1,\
                os.path.join("galleries", str(gallery.gallery_id)))
        img2_path = get_image_path(gallery.image_2,\
                os.path.join("galleries", str(gallery.gallery_id)))
        img3_path = get_image_path(gallery.image_3,\
                os.path.join("galleries", str(gallery.gallery_id)))
        img4_path = get_image_path(gallery.image_4,\
                os.path.join("galleries", str(gallery.gallery_id)))
        img5_path = get_image_path(gallery.image_5,\
                os.path.join("galleries", str(gallery.gallery_id)))
    return {'img1_path': img1_path,
            'img2_path': img2_path,
            'img3_path': img3_path,
            'img4_path': img4_path,
            'img5_path': img5_path }

def get_image_path(image_id, secondir=None):
    image = ImageDB.query.filter_by(img_id=image_id).first()
    if image:
        return os.path.join('photos', secondir, image.img_name)

def get_address_json(address_id):
    address = AddressDB.query.filter_by(address_id=address_id).first()
    return {'Address 1': address.address1,
            'Address 2': address.address2,
            'City': address.city,
            'State': address.state,
            'Country': address.country,
            'Zipcode': address.zip }
