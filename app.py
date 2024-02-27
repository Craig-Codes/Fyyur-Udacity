#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import errno
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
   # Get a list of all unique city and states
   cities_and_states = Venue.query.with_entities(Venue.city, Venue.state).distinct().all()
   # returns a list of city and state associated with each venue
   for city_state in cities_and_states:
     # loop through and pull out the city and state properties
     city = city_state[0]
     state = city_state[1]
     # for each city and state combination, we need to find the associated venues
     venues = Venue.query.filter_by(city=city, state=state).all()   

     data.append({
       "city": city,
       "state": state,
       "venues": venues
       })

   return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
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
  venue = Venue.query.get(venue_id) 
  # genres is a string, so it needs the brackets removed, then turned into a comma seperated list
  venue.genres=venue.genres.replace('{', '').replace('}','').split(",")
  # get venue upcoming show count
  shows = venue.shows
  
  upcoming_shows = 0
  past_shows = 0

  for show in shows:
     if show.start_time.timestamp() > datetime.now().timestamp(): # use timestamp to correctly compare
        upcoming_shows += 1
     else:
        past_shows += 1

  venue.upcoming_shows_count = upcoming_shows
  venue.past_shows_count = past_shows

  return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  try:
      form = VenueForm(request.form)
      venue = Venue(
        name=form.name.data,
        city=form.city.data,
        state=form.state.data,
        address=form.address.data,
        phone=form.phone.data,
        genres=form.genres.data,
        facebook_link=form.facebook_link.data,
        image_link=form.image_link.data
      )
      
      db.session.add(venue)
      db.session.commit()
      flash('Venue: {0} created successfully'.format(venue.name))
      return redirect(url_for('show_venue', venue_id=venue.id))
  except Exception as err:
    flash('An error occurred creating the Venue: {0}. Error: {1}'.format(venue.name, err))
    db.session.rollback()
    return redirect(url_for('index'))
  finally:
      db.session.close()

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
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

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.order_by(asc(Artist.name)).all()  # Sort alphabetically ascending
  return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
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
  artist = Artist.query.filter_by(id=artist_id).first()
  artist.genres=artist.genres.replace('{', '').replace('}','').split(",")

  shows = artist.shows
  
  upcoming_shows = 0
  past_shows = 0

  for show in shows:
     if show.start_time.timestamp() > datetime.now().timestamp(): # use timestamp to correctly compare
        upcoming_shows += 1
     else:
        past_shows += 1

  artist.upcoming_shows_count = upcoming_shows
  artist.past_shows_count = past_shows
  
  if artist is None:
    return abort(404)

  return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.filter_by(id=artist_id).first()
  form = ArtistForm(obj=artist) # populate form with query data
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
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
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.filter_by(id=venue_id).first()
  form = VenueForm(obj=venue)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
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
  try:
    form = ArtistForm(request.form)
    artist = Artist(
        name=form.name.data,
        city=form.city.data,
        state=form.state.data,
        phone=form.phone.data,
        genres=form.genres.data,
        facebook_link=form.facebook_link.data,
        image_link=form.image_link.data,
        website_link = form.website_link.data,
        seeking_description = form.seeking_description.data
      )
    
    db.session.add(artist)
    db.session.commit()
    flash('Artist: {0} created successfully'.format(artist.name))
    return redirect(url_for('show_artist', artist_id=artist.id))
  except:
    db.session.rollback()
    flash('An error occurred creating the Artist: {0}. Error: {1}'.format(artist.name, errno))
    return redirect(url_for('index'))
  finally:
    db.session.close()


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows  
    data = []

    shows = Show.query.all()
    for show in shows:
        data.append({
          "venue_id": show.Venue.id,
          "venue_name": show.Venue.name,
          "artist_id": show.Artist.id,
          "artist_name": show.Artist.name,
          "artist_image_link": show.Artist.image_link,
          "start_time": str(show.start_time)
        })
        
    return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
    form = ShowForm()
    form.artist_id.query = Artist.query
    form.venue_id.choices = [(v.id, v.name + ' ({}, {})'.format(v.city, v.state)) for v in Venue.query]
    return render_template('forms/new_show.html', form=form)
  

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']
   
    show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
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

# # Default port:
# if __name__ == '__main__':
#     app.run()


# Or specify port manually:
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
