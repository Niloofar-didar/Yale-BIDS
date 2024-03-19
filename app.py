# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import datetime
import time


from flask import Flask, render_template, request
from flask import jsonify, redirect, url_for
from urllib.request import urlopen
import requests
from bs4 import BeautifulSoup


from flask_restx import Resource, Api
import uuid



app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
      action = request.form['action']
      if action=='api':
          return redirect("/api/")

      elif action == 'search':

        term = request.form['term']

        return redirect(url_for('search', term=term))


      elif action == 'fetch':
          start_time = time.time()

          taskID = request.form['taskID']

          if taskID not in background_jobs_term:
              return jsonify({"error": "This Task ID is not found, please enter the ID of the task you searched a term for"}), 400
          return redirect(url_for('fetch', taskID=taskID))

    else:
      return render_template('index.html')

# Set configurations
#app.config['SERVER_NAME'] = 'localhost:5000'  # Update with your server name app.config['SERVER_NAME'] = 'localhost:5000'
app.config['APPLICATION_ROOT'] = '/'  # Update with your application root
app.config['PREFERRED_URL_SCHEME'] = 'http'  # Update with your preferred URL scheme

# Dummy data to simulate background job status
background_jobs = {}
background_jobs_term = {}


@app.route('/search')
def search():
    term = request.args.get('term')
    if term is None:
        return jsonify({"error": "No search term provided"}), 400
    records = perform_search(term)
    task_id = str(uuid.uuid4())
    background_jobs[task_id] = {
        "task_id": task_id,
        "status": "processing",
        "created_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    background_jobs_term[task_id] = {
        "task_id": task_id,
        "term":term
    }

    response = {
        "records": records,
        "query": term,
        "task_id": task_id
    }
    return jsonify(response)

@app.route('/fetch')
def fetch():
          start_time = time.time()
          taskID = request.args.get('taskID')


          job_term=background_jobs_term[taskID]
          job = background_jobs[taskID]
          search_term = job_term["term"]
          pmids=retrieve_pmids(search_term)
          status="complete"
          # Record the end time
          end_time = time.time()

          # Calculate the elapsed time
          elapsed_time_seconds = end_time - start_time
          response = {
              "task_id": taskID,
              "status": status, "result":{ "pmids": pmids },
              "created_time": job["created_time"],
              "run_seconds": elapsed_time_seconds
          }

          return jsonify(response)

with app.app_context():
  api = Api(app, doc='/api/', title="Yale BIDS APIs",  # Set your custom title here
            description="Two APIs for searching terms (e.g., kidney disease) in PubMed and retrieving information based on the task ID (which is generated from search tasks)." ,
  default="Click to search and retrieve information",  # Set your custom default namespace here
          default_label="API endpoints for BIDS functionalities", swagger_ui=True)  # Set your custom default namespace description here





def perform_search(term):
    try:
        # Construct the URL for PubMed search
        url = f"https://pubmed.ncbi.nlm.nih.gov/?term={term.replace(' ', '+')}"

        # Send HTTP GET request to PubMed website
        response = requests.get(url)

        # Check if request was successful (status code 200)
        if response.status_code == 200:
            # Parse HTML response to extract the number of records
            records = extract_records(response.text)
            return records
        else:
            print(f"Error: Failed to retrieve search results. Status code: {response.status_code}")
            return 0
    except Exception as e:
        print(f"Error performing PubMed search: {e}")
        return 0



def retrieve_pmids(search_term):
    try:
        # Construct the PubMed search URL
        url = f"https://pubmed.ncbi.nlm.nih.gov/?term={search_term.replace(' ', '+')}"

        # Send HTTP GET request to PubMed website
        response = requests.get(url)

        # Check if request was successful (status code 200)
        if response.status_code == 200:
            # Parse HTML response to extract PubMed IDs (pmids)
            soup = BeautifulSoup(response.text, 'html.parser')
            pmids = [int(tag['data-article-id']) for tag in soup.find_all(attrs={"data-article-id": True})]
            return pmids
        else:
            print(f"Error: Failed to retrieve PubMed search results. Status code: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error retrieving PubMed search results: {e}")
        return []



@api.route('/searchapi/<term>')
@api.doc(params={'term': 'The search term'})
class searchapi(Resource):
    def get(self, term):
        records = perform_search(term)
        task_id = str(uuid.uuid4())
        background_jobs[task_id] = {
            "task_id": task_id,
            "status": "processing",
            "created_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        background_jobs_term[task_id] = {
            "task_id": task_id,
            "term": term
        }
        response = {
            "records": records,
            "query": term,
            "task_id": task_id
        }
        return jsonify(response)



@api.route('/fetchapi/<task_id>')
class fetchapi(Resource):
    def post(self, task_id):

        start_time = time.time()

        if task_id not in background_jobs_term:
            return jsonify({"error": "This Task ID is not found, please enter the ID of the task you searched a term for"})

        job_term = background_jobs_term[task_id]
        job = background_jobs[task_id]
        search_term = job_term["term"]

        pmids = retrieve_pmids(search_term)
        status = "complete"
        # Record the end time
        end_time = time.time()
        # Calculate the elapsed time
        elapsed_time_seconds = end_time - start_time

        response = {
            "task_id": task_id,
            "status": status, "result": {"pmids": pmids},
            "created_time": job["created_time"],
            "run_seconds": elapsed_time_seconds
        }

        return jsonify(response)


def extract_records(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        result_div = soup.find('div', class_='results-amount')
        if result_div:
            records_text = result_div.get_text()
            records = int(records_text.split()[0].replace(',', ''))
            return records
        else:
            print("Error: Results div not found in HTML content")
            return 0
    except Exception as e:
        print(f"Error extracting records: {e}")
        return 0


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app.run()
