#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import os
import dateutil.parser
import babel
import sys
from flask import Flask, abort, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm, Form
from wtforms import StringField
from wtforms.validators import DataRequired
from forms import *
from database import db
from flask_migrate import Migrate
# import models so that they are known to Flask-Migrate
from models.models import Venue, Artist, Show
from sqlalchemy import asc, exc, desc, func

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#
import sys
sys.path.append('../') # make modules visible to each other

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app) # function links database to app
migrate = Migrate(app, db) # Setup for Flask Migration, linking app and db to Migrate

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
   data= []
  # TODO: replace with real venues data.
   # Get a list of all unique city and states
   cities_and_states = Venue.query.with_entities(Venue.city, Venue.state).distinct().all()
   # returns a list of city and state associated with each venue
   for city_state in cities_and_states:
     # loop through and pull out the city and state properties
     city = city_state[0]
     state = city_state[1]
     # for each city and state combination, we need to find the associated venues
     venues = Venue.query.filter_by(city=city, state=state).all()   
     #shows = venues[0].upcoming_shows --> TODO!!!
     data.append({
       "city": city,
       "state": state,
       "venues": venues
       })

   return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form['search_term']
  # iLike ignores case
  search_result = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()

  response={
    "count": len(search_result),
    "data": search_result
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get(venue_id) 
  # genres is a string, so it needs the brackets removed, then turned into a comma seperated list
  venue.genres=venue.genres.replace('{', '').replace('}','').split(",")
  return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  try:
      name = request.form['name']
      city = request.form['city']
      state = request.form['state']
      address = request.form['address']
      phone = request.form['phone']
      genres = request.form.getlist('genres')
      facebook_link = request.form['facebook_link']
      image_link = request.form['image_link']
      website_link = request.form['website_link']
      seeking_description = request.form['seeking_description']

      # If seeking talent not selected in the form, it wont show up in the request.form
      seeking_talent=''
      try:
        seeking_talent = request.form['seeking_talent']
        seeking_talent = True
      except:
        seeking_talent = False

      venue = Venue(name=name, 
                    city=city, 
                    state=state, 
                    phone=phone, 
                    address=address,
                    genres=genres, 
                    facebook_link=facebook_link, 
                    image_link=image_link, 
                    website_link=website_link, 
                    seeking_talent=seeking_talent, 
                    seeking_description=seeking_description)
      db.session.add(venue)
      db.session.commit()
      flash('Venue ' + name + ' was successfully listed!')
      # TODO: modify data to be the data object returned from db insertion
      return redirect(url_for('show_venue', venue_id=venue.id))
  except:
      # TODO: on unsuccessful db insert, flash an error instead.
      db.session.rollback()
      flash('An error occurred. Venue ' + name + ' could not be listed.')
      print(sys.exc_info())
      return redirect(url_for('index'))
  finally:
      db.session.close()

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  venue = Venue.query.get(venue_id) # query first so that name can be used with flash
  print(venue)
  try:
    db.session.delete(venue)
    db.session.commit()
    flash('Venue ' + venue.name + ' was successfully deleted!')
    return redirect(url_for('index'))
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + venue.name + ' could not be deleted.')
    return redirect(url_for('index'))
  finally:
    db.session.close()

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artists = Artist.query.order_by(asc(Artist.name)).all()  # Sort alphabetically ascending
  return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form['search_term']
  # iLike ignores case
  search_result = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()

  response={
    "count": len(search_result),
    "data": search_result
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  artist = Artist.query.filter_by(id=artist_id).first()
  artist.genres=artist.genres.replace('{', '').replace('}','').split(",")
  
  if artist is None:
    return abort(404)

  return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.filter_by(id=artist_id).first()
  # TODO: populate form with fields from artist with ID <artist_id>
  form = ArtistForm(obj=artist) # populate form with query data
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
    artist = Artist.query.filter_by(id=artist_id).first()
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.facebook_link = request.form['facebook_link']
    artist.image_link = request.form['image_link']
    artist.website_link = request.form['website_link']
    artist.seeking_description = request.form['seeking_description']

    # If seeking venue not selected in the form, it wont show up in the request.form
    try:
      seeking_venue = request.form['seeking_venue']
      artist.seeking_venue = True
    except:
      artist.seeking_venue = False

    db.session.commit()
  # artist record with ID <artist_id> using the new attributes
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.filter_by(id=venue_id).first()
    # TODO: populate form with values from venue with ID <venue_id>
  form = VenueForm(obj=venue)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  venue = Venue.query.filter_by(id=venue_id).first()
  venue.name = request.form['name']
  venue.city = request.form['city']
  venue.state = request.form['state']
  venue.address = request.form['address']
  venue.phone = request.form['phone']
  venue.genres = request.form.getlist('genres')
  venue.facebook_link = request.form['facebook_link']
  venue.image_link = request.form['image_link']
  venue.website_link = request.form['website_link']
  venue.seeking_description = request.form['seeking_description']

  # If seeking talent not selected in the form, it wont show up in the request.form
  try:
    seeking_talent = request.form['seeking_talent']
    venue.seeking_talent = True
  except:
    venue.seeking_talent = False

  db.session.add(venue)
  db.session.commit()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # TODO: insert form data as a new Venue record in the db
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    image_link = request.form['image_link']
    website_link = request.form['website_link']
    seeking_description = request.form['seeking_description']

    # If seeking venue not selected in the form, it wont show up in the request.form
    seeking_venue =''
    try:
      seeking_venue = request.form['seeking_venue']
      seeking_venue = True
    except:
      seeking_venue = False

    artist = Artist(name=name, 
                    city=city, 
                    state=state, 
                    phone=phone, 
                    genres=genres, 
                    facebook_link=facebook_link, 
                    image_link=image_link, 
                    website_link=website_link, 
                    seeking_venue=seeking_venue, 
                    seeking_description=seeking_description)
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + name + ' was successfully listed!')
     # TODO: modify data to be the data object returned from db insertion
    return redirect(url_for('show_artist', artist_id=artist.id))
  except:
    # TODO: on unsuccessful db insert, flash an error instead.
    db.session.rollback()
    flash('An error occurred. Artist ' + name + ' could not be listed.')
    return redirect(url_for('index'))
  finally:
    db.session.close()


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  data=[{
    "venue_id": 1,
    "venue_name": "The Musical Hop",
    "artist_id": 4,
    "artist_name": "Guns N Petals",
    "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    "start_time": "2019-05-21T21:30:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 5,
    "artist_name": "Matt Quevedo",
    "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    "start_time": "2019-06-15T23:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-01T20:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-08T20:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-15T20:00:00.000Z"
  }]
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  # on successful db insert, flash success
  flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
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

# # Default port:
# if __name__ == '__main__':
#     app.run()


# Or specify port manually:
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
