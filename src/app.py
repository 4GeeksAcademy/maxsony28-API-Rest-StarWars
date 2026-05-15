import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planet, Favorite

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

@app.route('/')
def sitemap():
    return generate_sitemap(app)


@app.route("/users", methods=["GET"])
def get_all_users():
    try:
        users = User.query.all()
        return jsonify({"users": [user.serialize() for user in users]}), 200
    except Exception as err:
        return jsonify({"message": f"Error: {err.args}"}), 500

@app.route('/users', methods=['POST'])
def create_user():
    body = request.get_json(silent=True) or {}
    email = body.get("email")
    password = body.get("password")

    if not isinstance(email, str) or email.strip() == '':
        raise APIException("email required and must be a string", status_code=400)
    if not isinstance(password, str) or password.strip() == '':
        raise APIException("password required and must be a string", status_code=400)

    existing_user = User.query.filter_by(email=email.lower().strip()).first()
    if existing_user is not None:
        return jsonify({"message": "user already exists"}), 400

    user = User(email=email.lower().strip(), password=password)
    db.session.add(user)
    
    try:
        db.session.commit()
        return jsonify(user.serialize()), 201
    except Exception as err:
        db.session.rollback()
        return jsonify({"error": f"Error: {err.args}"}), 500


@app.route('/people', methods=['GET'])
def get_all_people():
    try:
        people = People.query.all()
        return jsonify({"people": [person.serialize() for person in people]}), 200
    except Exception as err:
        return jsonify({"message": f"Error: {err.args}"}), 500

@app.route('/people/<int:people_id>', methods=['GET'])
def get_person(people_id):
    person = People.query.get(people_id)
    if person is None:
        return jsonify({"message": "Person not found"}), 404
    return jsonify(person.serialize()), 200

@app.route('/people', methods=['POST'])
def create_person():
    body = request.get_json(silent=True) or {}
    name = body.get("name")

    if not isinstance(name, str) or name.strip() == '':
        raise APIException("name required and must be a string", status_code=400)

    existing_person = People.query.filter_by(name=name.strip()).first()
    if existing_person:
        return jsonify({"message": "Person already exists"}), 400

    person = People(
        name=name.strip(),
        gender=body.get("gender"),
        eye_color=body.get("eye_color")
    )
    db.session.add(person)
    try:
        db.session.commit()
        return jsonify(person.serialize()), 201
    except Exception as err:
        db.session.rollback()
        return jsonify({"error": f"Error: {err.args}"}), 500

@app.route('/people/<int:people_id>', methods=['DELETE'])
def delete_person(people_id):
    person = People.query.get(people_id)
    if person is None:
        return jsonify({"message": "Person not found"}), 404

    db.session.delete(person)
    try:
        db.session.commit()
        return jsonify({}), 204
    except Exception as err:
        db.session.rollback()
        return jsonify({"error": f"Error: {err.args}"}), 500


@app.route('/planets', methods=['GET'])
def get_all_planets():
    try:
        planets = Planet.query.all()
        return jsonify({"planets": [planet.serialize() for planet in planets]}), 200
    except Exception as err:
        return jsonify({"message": f"Error: {err.args}"}), 500

@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if planet is None:
        return jsonify({"message": "Planet not found"}), 404
    return jsonify(planet.serialize()), 200

@app.route('/planets', methods=['POST'])
def create_planet():
    body = request.get_json(silent=True) or {}
    name = body.get("name")

    if not isinstance(name, str) or name.strip() == '':
        raise APIException("name required and must be a string", status_code=400)

    existing_planet = Planet.query.filter_by(name=name.strip()).first()
    if existing_planet:
        return jsonify({"message": "Planet already exists"}), 400

    planet = Planet(
        name=name.strip(),
        population=body.get("population"),
        terrain=body.get("terrain")
    )
    db.session.add(planet)
    try:
        db.session.commit()
        return jsonify(planet.serialize()), 201
    except Exception as err:
        db.session.rollback()
        return jsonify({"error": f"Error: {err.args}"}), 500

@app.route('/planets/<int:planet_id>', methods=['DELETE'])
def delete_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if planet is None:
        return jsonify({"message": "Planet not found"}), 404

    db.session.delete(planet)
    try:
        db.session.commit()
        return jsonify({}), 204
    except Exception as err:
        db.session.rollback()
        return jsonify({"error": f"Error: {err.args}"}), 500


@app.route('/users/<int:user_id>/favorites', methods=['GET'])
def get_user_favorites(user_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"message": "User not found"}), 404

    favorites = Favorite.query.filter_by(user_id=user_id).all()
    return jsonify({"favorites": [fav.serialize() for fav in favorites]}), 200

@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    # Simulamos que el user_id viene del token, por ahora forzamos 1
    current_user_id = 1 
    
    planet = Planet.query.get(planet_id)
    if planet is None:
        return jsonify({"message": "Planet not found"}), 404
        
    exist = Favorite.query.filter_by(user_id=current_user_id, planet_id=planet_id).first()
    if exist:
        return jsonify({"message": "Planet already in favorites"}), 400

    new_fav = Favorite(user_id=current_user_id, planet_id=planet_id)
    db.session.add(new_fav)
    try:
        db.session.commit()
        return jsonify(new_fav.serialize()), 201
    except Exception as err:
        db.session.rollback()
        return jsonify({"error": f"Error: {err.args}"}), 500

@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):
    current_user_id = 1 
    
    fav = Favorite.query.filter_by(user_id=current_user_id, planet_id=planet_id).first()
    if fav is None:
        return jsonify({"message": "Favorite not found"}), 404
        
    db.session.delete(fav)
    try:
        db.session.commit()
        return jsonify({}), 204
    except Exception as err:
        db.session.rollback()
        return jsonify({"error": f"Error: {err.args}"}), 500

@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_people(people_id):
    current_user_id = 1 
    
    person = People.query.get(people_id)
    if person is None:
        return jsonify({"message": "Person not found"}), 404
        
    exist = Favorite.query.filter_by(user_id=current_user_id, people_id=people_id).first()
    if exist:
        return jsonify({"message": "Person already in favorites"}), 400

    new_fav = Favorite(user_id=current_user_id, people_id=people_id)
    db.session.add(new_fav)
    try:
        db.session.commit()
        return jsonify(new_fav.serialize()), 201
    except Exception as err:
        db.session.rollback()
        return jsonify({"error": f"Error: {err.args}"}), 500

@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def delete_favorite_people(people_id):
    current_user_id = 1 
    
    fav = Favorite.query.filter_by(user_id=current_user_id, people_id=people_id).first()
    if fav is None:
        return jsonify({"message": "Favorite not found"}), 404
        
    db.session.delete(fav)
    try:
        db.session.commit()
        return jsonify({}), 204
    except Exception as err:
        db.session.rollback()
        return jsonify({"error": f"Error: {err.args}"}), 500


if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)