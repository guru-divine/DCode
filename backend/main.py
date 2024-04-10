from flask import Flask, request, redirect, render_template, render_template_string
from flask.helpers import url_for
from config import API_CODEFORCES_USER_INFO, API_CODEFORCES_USER_PROBLEM_STATUS, API_ATCODER_USER_INFO
from dotenv import load_dotenv
from collections import Counter

import os
import json, requests


# Load environment variables from .env file
load_dotenv()

app = Flask("DCODE")
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

print(os.environ.get("FLASK_SECRET_KEY"))

def get_handle_color(rating):
    if rating<1200:
        return "#36454F"
    elif 1200<=rating<1400:
        return "green"
    elif 1400<=rating<1600:
        return "cyan"
    elif 1600<=rating<1900:
        return "#00008B"
    elif 1900<=rating<2100:
        return "violet"
    elif 2100<=rating<2400:
        return "orange"
    else:
        return "red"
    
def get_atcoder_handle_rank_color(rating):
    color = ""
    rank = ""
    if rating<400:
        color = "#36454F"
    elif 400<=rating<800:
        color = "#3C2A21"
    elif 800<=rating<1200:
        color = "green"
    elif 1200<=rating<1600:
        color = "cyan"
    elif 1600<=rating<2000:
        color = "blue"
    elif 2000<=rating<2400:
        color = "yellow"
    elif 2400<=rating<2800:
        color = "orange"
    else:
        color = "red"
    
    if rating<2000:
        if rating<400:
            rank = "Unrated"
        else:
            num = (2000-rating)//200 + (rating%200 != 0)
            rank = f"{num} Kyu"
        # print(rank)
    else:
        num = (rating-2000)//200 + 1
        rank = f"{num} Dan"

    return rank, color
    
def user__Verdict(probs, problems):
    user_verdicts = {}
    key_counter = 1
    correct_cnt = 0

    for problem in problems:
        verdict = "NA"
        for prob in probs:
            if prob["problem"]["contestId"] == problem["contestId"] and prob["problem"]["index"] == problem["index"]:
                if prob["verdict"] == "OK":
                    verdict = "AC"
                    correct_cnt += 1
                    break
                else:
                    verdict = "WA"

        user_verdicts[key_counter] = verdict
        key_counter += 1

    return user_verdicts, correct_cnt

def tag_find(probs):
    visited = set()
    tag_frequencies = []

    for prob in probs["result"]:
        if prob["verdict"] == "OK":
            contest_id = prob["problem"]["contestId"]
            index = prob["problem"]["index"]
            if (contest_id, index) not in visited:
                visited.add((contest_id, index))
                tags = prob["problem"]["tags"]
                tag_frequencies.extend(tags)

    # Count the frequencies of each tag
    tag_counts = Counter(tag_frequencies)
    # Sort the tag frequencies in decreasing order
    sorted_tag_frequencies = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_tag_frequencies

def find_max_and_cur_rating_Atcoder(data):
    max_rating = max(result['NewRating'] for result in data)
    cur_rating = data[-1]['NewRating']
    return max_rating, cur_rating

def get_visit_count():
    if os.path.exists("visit_count.txt"):
        with open("visit_count.txt", "r") as file:
            return int(file.read())
    else:
        return 0

def update_visit_count(visit_count):
    with open("visit_count.txt", "w") as file:
        file.write(str(visit_count))



@app.route("/")
def home():

    visit_count = get_visit_count()
    visit_count += 1
    # Update the visit count in the persistent storage
    update_visit_count(visit_count)

    return render_template("home.html", visit_count=visit_count)

@app.route("/codeforces", methods=['POST', 'GET'])
def codeforces():
    visit_count = get_visit_count()
    visit_count += 1
    # Update the visit count in the persistent storage
    update_visit_count(visit_count)

    userhandle = request.form.get('userhandle', '')  # Get userhandle from form data
    user_rating = 1500
    with open(f'cf-rating-problems/{user_rating}.json', 'r') as f:
        problems = json.load(f)[:100]  # Load the first hundred problems
    
    with open(f'cf-problem-tags/tags.json', 'r') as f:
        tags = json.load(f)

    if request.method == "POST" and userhandle:
        url = API_CODEFORCES_USER_INFO.format(userhandle)
        response = requests.get(url)
        # Parse JSON response
        data = response.json()
        
        # Check if API response is successful
        if data.get("status") == "OK":
            # Accessing rank, maxRating, and rating
            if "rank" in data["result"][0]:
                rank = data["result"][0]["rank"]
                max_rating = data["result"][0]["maxRating"]
                rating = data["result"][0]["rating"]
                ratingColor = get_handle_color(rating)
            else:
                rank = "Unrated"
                rating = 0
                max_rating = 0
                ratingColor = get_handle_color(rating)

            url = API_CODEFORCES_USER_PROBLEM_STATUS.format(userhandle)
            response = requests.get(url)
            probs = response.json()

            # user_rating = 1700
            list_rating = min(max(800, (rating - rating%100)+200), 3500)

            with open(f'cf-rating-problems/{list_rating}.json', 'r') as f:
                problems = json.load(f)[:100]  # Load the first hundred problems

            correct_cnt = 0
            user_verdicts, correct_cnt = user__Verdict(probs["result"], problems)
            # for verdict in user_verdicts:
            #     print(user_verdicts[verdict])
            
            # Render the template with userhandle included
            return render_template("codeforces.html", userhandle=userhandle, rank=rank, max_rating=max_rating, rating=rating, problems=problems, tags=tags['tags'], probs=probs["result"], ratingColor=ratingColor, user_verdicts=user_verdicts, correct_cnt=correct_cnt, visit_count=visit_count)
    # Render the template with userhandle unchanged
    return render_template("codeforces.html", userhandle='', problems=problems, tags=tags['tags'], correct_cnt=0, user_verdicts={}, visit_count=visit_count)



@app.route("/atcoder", methods=['POST', 'GET'])
def atcoder():
    visit_count = get_visit_count()
    visit_count += 1
    # Update the visit count in the persistent storage
    update_visit_count(visit_count)

    userhandle = request.form.get('userhandle', '')  # Get userhandle from form data
    user_rating = 1400
    with open(f'atcoder-rating-problems/{user_rating}.json', 'r') as f:
        problems = json.load(f)[:100]  # Load the first hundred problems

    if request.method == "POST" and userhandle:
        url = API_ATCODER_USER_INFO.format(userhandle)
        response = requests.get(url)
  
        # Check if API response is successful
        if response.status_code == 200:
            # Parse JSON response
            data = response.json()

            max_rating, rating = find_max_and_cur_rating_Atcoder(data)
            # print("HEllo")

            rank, ratingColor = get_atcoder_handle_rank_color(rating)


            return render_template("atcoder.html", userhandle=userhandle, rank=rank, ratingColor=ratingColor, visit_count=visit_count, max_rating=max_rating, rating=rating, problems=problems, user_verdicts={}, correct_cnt=0)

    return render_template("atcoder.html", userhandle='', visit_count=visit_count, correct_cnt=0)


@app.route("/codechef", methods=['POST', 'GET'])
def codechef():
    visit_count = get_visit_count()
    visit_count += 1
    # Update the visit count in the persistent storage
    update_visit_count(visit_count)

    return render_template("codechef.html")


@app.route("/cfvisualizer", methods=['POST', 'GET'])
def cfvisualizer():
    visit_count = get_visit_count()
    visit_count += 1
    # Update the visit count in the persistent storage
    update_visit_count(visit_count)

    userhandle = request.form.get('userhandle', '')  # Get userhandle from form data

    if request.method == "POST" and userhandle:
        url = API_CODEFORCES_USER_INFO.format(userhandle)
        response = requests.get(url)
        # Parse JSON response
        data = response.json()
        
        # Check if API response is successful
        if data.get("status") == "OK":
            url = API_CODEFORCES_USER_PROBLEM_STATUS.format(userhandle)
            response = requests.get(url)
            probs = response.json()

            tag_frequencies = tag_find(probs)

            for tag, frequency in tag_frequencies:
                print(f"Tag: {tag}, Frequency: {frequency}")

            # tag_frequencies = [
            #     {"tag": "Tag1", "frequency": 30},
            #     {"tag": "Tag2", "frequency": 20},
            #     {"tag": "Tag3", "frequency": 10},
            #     # Add more tag frequencies as needed
            # ]
            return render_template("cfvisualizer.html", userhandle=userhandle, tag_frequencies=tag_frequencies, visit_count=visit_count)


    return render_template("cfvisualizer.html", userhandle='', visit_count=visit_count)



app.run(debug=True)