from flask import Flask, render_template, request, make_response, g
from redis import Redis
import os
import socket
import random
import json
import logging

option_a = os.getenv('OPTION_A', "Manhatan")
option_b = os.getenv('OPTION_B', "Pearson")
hostname = socket.gethostname()

def manhattan(rating1, rating2):
    distance = 0
    total = 0
    for key in rating1:
        if key in rating2:
            distance += abs(rating1[key] - rating2[key])
            total += 1
    if total > 0:
        return distance / total
    else:
        return -1 #Indicates no ratings in common

def pearson(rating1, rating2):
    sum_xy = 0
    sum_x = 0
    sum_y = 0
    sum_x2 = 0
    sum_y2 = 0
    n = 0
    for key in rating1:
        if key in rating2:
            n += 1
            x = rating1[key]
            y = rating2[key]
            sum_xy += x * y
            sum_x += x
            sum_y += y
            sum_x2 += pow(x, 2)
            sum_y2 += pow(y, 2)
    # now compute denominator
    denominator = sqrt(sum_x2 - pow(sum_x, 2) / n) * sqrt(sum_y2 - pow(sum_y, 2) / n)
    if denominator == 0:
        return 0
    else:
            return (sum_xy - (sum_x * sum_y) / n) / denominator


app = Flask(__name__)

gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.INFO)

def get_redis():
    if not hasattr(g, 'redis'):
        g.redis = Redis(host="redis", db=0, socket_timeout=5)
    return g.redis
    

# @app.route("/", methods=['POST','GET'])
# def hello():
#     voter_id = request.cookies.get('voter_id')
#     if not voter_id:
#         voter_id = hex(random.getrandbits(64))[2:-1]

#     vote = None

#     if request.method == 'POST':
#         redis = get_redis()
#         vote = request.form['vote']
#         app.logger.info('Received vote for %s', vote)
#         data = json.dumps({'voter_id': voter_id, 'vote': vote})
#         redis.rpush('votes', data)

#     resp = make_response(render_template(
#         'index.html',
#         option_a=option_a,
#         option_b=option_b,
#         hostname=hostname,
#         vote=vote,
#     ))
#     resp.set_cookie('voter_id', voter_id)
#     return resp
    
    
@app.route("/", methods=['POST','GET'])
def distancias():

    users = {"Angelica":{'Blues Traveler': 3.5, 'Broken Bells': 2.0, 'Norah Jones': 4.5, 'Phoenix': 5.0, 'Sligtly Stoopid': 1.5, 'The Strokes': 2.5, 'Vampire Weekend': 2.0},"Bill":{'Blues Traveler': 2.0, 'Broken Bells': 3.5, 'Deadmau5': 4.0, 'Phoenix': 2.0, 'Sligtly Stoopid': 3.5, 'Vampire Weekend': 3.0}}
    
    distancia_pearson = pearson(users['Angelica'], users["Bill"])
    distancia_manhattan = manhattan(users['Angelica'], users["Bill"])
    
    
    voter_id = request.cookies.get('voter_id')
    if not voter_id:
        voter_id = hex(random.getrandbits(64))[2:-1]

    vote = None

    if request.method == 'POST':
        redis = get_redis()
        

        user_1 = request.form['option_a']
        user_2 = request.form['option_b']

        distancia_pearson = str(pearson(users[user_1], users[user_2]))
        distancia_manhattan = str(manhattan(users[user_1], users[user_2])) 

        data = json.dumps({'voter_id': voter_id,'distancia_manhattan': distancia_manhattan, 'distancia_pearson': distancia_pearson})
        redis.rpush('distancias', data)

    resp = make_response(render_template(
        'index.html',
        option_a=option_a,
        option_b=option_b,
        hostname=hostname,
    ))
    resp.set_cookie('voter_id', voter_id)
    return resp


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
