#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import sys
from urllib import response
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost:5432/fyyurapp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

migrate = Migrate(app, db)



#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

from models import *
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  response_data = []

  # Getting the unique cities and state for all venues
  states_cities = db.session.query(Venue.state, Venue.city)
  
  # filtering the venues base on city and state
  for data in states_cities:
    show_result = Venue.query.filter(Venue.state == data.state).filter(Venue.city==data.city).all()
    
    # Querying for upcoming shows by filtering with time greater than current time
    upcoming_shows = len(db.session.query(Show).filter(Show.start_time > datetime.now()).all())
    # creating response data for venues
    show_venue_data = [{
        'id': venue.id,
        'name': venue.name,
        'num_upcoming_shows': upcoming_shows
      } for venue in show_result]

    response_data.append({
        'city': data.city,
        'state': data.state,
        'venues': show_venue_data
      })


  return render_template('pages/venues.html', areas=response_data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  
  search_term = request.form.get('search_term', '')

  # performing a case insensitive maching on venue names
  data = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).order_by('name').all()
 
  response={
    "count": len(data),
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue_data = Venue.query.filter(Venue.id == venue_id).first()

  

 

  past_show_data = db.session.query(Show, Artist).join(Artist, Artist.id==Show.artist_id).filter(Show.venue_id==venue_id).filter(Show.start_time < datetime.now())
  upcoming_show_data =  db.session.query(Show, Artist).join(Artist, Artist.id==Show.artist_id).filter(Show.venue_id==venue_id).filter(Show.start_time > datetime.now())
  
  
  upcoming_shows = []
  for show, artist in upcoming_show_data.all():
      upcoming_shows.append({
        'artist_id': artist.id,
        'artist_name': artist.name,
        'artist_image_link': artist.image_link,
        'start_time': show.start_time
      })
  
  past_shows = []
  for show, artist in past_show_data.all():
      past_shows.append({
        'artist_id': artist.id,
        'artist_name': artist.name,
        'artist_image_link': artist.image_link,
        'start_time': show.start_time
      })
  
  data = {
    
    "id": venue_data.id,
    "name": venue_data.name,
    "genres": [venue_data.genres ],
    "address": venue_data.address,
    "city": venue_data.city,
    "state": venue_data.state,
    "phone": venue_data.phone,
    "website": venue_data.website,
    "facebook_link": venue_data.facebook_link,
    "seeking_talent": venue_data.seeking_talent,
    "seeking_description": venue_data.seeking_discription,
    "image_link": venue_data.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_show_data.all()),
    "upcoming_shows_count": len(upcoming_show_data.all()),
  }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # insert form data as a new Venue record in the db, instead
  try:
        new_venue = Venue(
        name=request.form['name'],
        city=request.form['city'],
        state=request.form['state'],
        address=request.form['address'],
        phone=request.form['phone'],
        genres=request.form.getlist('genres'),
        facebook_link=request.form['facebook_link'],
        image_link=request.form['image_link'],
        website=request.form['website_link'],
        seeking_talent= True if request.form['seeking_talent'] else False,
        seeking_discription=request.form['seeking_description'],
        )
        db.session.add(new_venue)
        db.session.commit()
        flash(f"Venue {request.form['name']} was successfully listed!")
  except:
        print(sys.exc_info())
        flash(f"An error occurred {sys.exc_info()} Venue {request.form.getlist('seeking_talent')}  could not be listed.")
        db.session.rollback()
  finally:
        db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # taking a venue_id, and using SQLAlchemy ORM to delete a record.
  #  Handle cases where the session commit could fail.
  try:
        Venue.query.filter(Venue.id==venue_id).delete()
        db.session.commit()
  except:
        print(sys.exc_info())
        db.session.rollback()

  finally:
        db.session.close()
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # replace with real data returned from querying the database
  data = db.session.query(Artist.id, Artist.name).all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # implement search on artists with partial string search. Ensure it is case-insensitive.
  search_term = request.form.get('search_term', '')

  # performing a case insensitive maching on artist names
  data = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).order_by('name').all()
 
  response={
    "count": len(data),
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # replace with real artist data from the artist table, using artist_id
  artist_data = Artist.query.filter(Artist.id == artist_id).first()
  past_show_data = db.session.query(Show, Artist).join(Artist, Artist.id==Show.artist_id).filter(Show.artist_id==artist_id).filter(Show.start_time < datetime.now())
  upcoming_show_data =  db.session.query(Show, Artist).join(Artist, Artist.id==Show.artist_id).filter(Show.artist_id==artist_id).filter(Show.start_time > datetime.now())
  upcoming_shows = []
  for show, artist in upcoming_show_data.all():
      upcoming_shows.append({
        'artist_id': artist.id,
        'artist_name': artist.name,
        'artist_image_link': artist.image_link,
        'start_time': show.start_time
      })
  
  past_shows = []
  for show, artist in past_show_data.all():
      past_shows.append({
        'artist_id': artist.id,
        'artist_name': artist.name,
        'artist_image_link': artist.image_link,
        'start_time': show.start_time
      })
  
  data = {
    
    "id": artist_data.id,
    "name": artist_data.name,
    "genres": [artist_data.genres ],
    "city": artist_data.city,
    "state": artist_data.state,
    "phone": artist_data.phone,
    "website": artist_data.website,
    "facebook_link": artist_data.facebook_link,
    "seeking_venue": artist_data.seeking_venue,
    "seeking_description": artist_data.seeking_discription,
    "image_link": artist_data.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_show_data.all()),
    "upcoming_shows_count": len(upcoming_show_data.all()),
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.filter(Artist.id==artist_id).first()
  if artist:
    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.genres.data = artist.genres
    form.phone.data = artist.phone
    form.website_link.data = artist.website
    form.facebook_link.data = artist.facebook_link
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_discription
    form.image_link.data = artist.image_link
   
  # populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  artist = Artist.query.filter(Artist.id==artist_id).first()
  try:
      artist.name = request.form['name'],
      artist.city = request.form['city'],
      artist.state = request.form['state'],
      artist.phone = request.form['phone'],
      artist.genres = request.form.getlist('genres'),
      artist.facebook_link = request.form['facebook_link'],
      artist.image_link = request.form['image_link'],
      artist.website = request.form['website_link'],
      artist.seeking_venue = True if request.form['seeking_venue'] else False
      artist.seeking_discription = request.form['seeking_description']
      db.session.commit()
      flash(f"Artist {request.form.get('name')} was updated successfully!")
  except:
      flash(f"An error occurred Artist{request.form.get('name')} could not be updated")
      db.session.rollback()
      print(sys.exc_info())
  finally:
      db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.filter(Venue.id==venue_id).first()

  if venue:
    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.address.data = venue.address
    form.genres.data = venue.genres
    form.phone.data = venue.phone
    form.website_link.data = venue.website
    form.facebook_link.data = venue.facebook_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_discription
    form.image_link.data = venue.image_link
  
  # populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue = Venue.query.filter(Venue.id==venue_id).first()
  try:
      venue.name = request.form['name'],
      venue.city = request.form['city'],
      venue.state = request.form['state'],
      venue.address = request.form['address'],
      venue.phone = request.form['phone'],
      venue.genres = request.form.getlist('genres'),
      venue.facebook_link = request.form['facebook_link'],
      venue.image_link = request.form['image_link'],
      venue.website = request.form['website_link'],
      venue.seeking_talent = True if request.form['seeking_talent'] else False
      venue.seeking_discription = request.form['seeking_description']
      db.session.commit()
      flash(f"Venue {request.form.get('name')} was updated updated successfully!")
  except:
      sys.exc_info()
      flash(f"An error occurred Venue {request.form.get('name')} could not be updated")
      db.session.rollback()
  finally:
      db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  try:
        new_artist = Artist(
        name=request.form['name'],
        city=request.form['city'],
        state=request.form['state'],
        phone=request.form['phone'],
        genres=request.form.getlist('genres'),
        facebook_link=request.form['facebook_link'],
        image_link=request.form['image_link'],
        website=request.form['website_link'],
        seeking_venue= True if request.form['seeking_venue'] else False,
        seeking_discription=request.form['seeking_description'],
        )
        db.session.add(new_artist)
        db.session.commit()
        flash(f"Artist {request.form['name']} was successfully listed!")
  except:
        flash(f"An error occurred  Artist {request.form.get('name')}  could not be listed.")
        db.session.rollback()
        print(sys.exc_info())
  finally:
        db.session.close()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # replace with real venues data.
  shows_data = db.session.query(Show).join(Venue, Venue.id==Show.venue_id).join(Artist, Artist.id==Show.artist_id).all()

  data = []
  for show in shows_data:
    data.append({
    'venue_id': show.venue_id,
    'venue_name': show.venue.name,
    'artist_id': show.artist_id,
    'artist_name': show.artist.name,
    'artist_image_link': show.artist.image_link,
    'start_time': str(show.start_time)
  })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  try:
        new_show = Show(
        artist_id=request.form['artist_id'],
        venue_id=request.form['venue_id'],
        start_time=request.form['start_time']
        )
        db.session.add(new_show)
        db.session.commit()
        flash(f"Show was successfully listed!")
  except:
        flash(f"An error occurred {sys.exc_info()}  Show could not be listed.")
        db.session.rollback()
        print(sys.exc_info())
  finally:
        db.session.close()
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
