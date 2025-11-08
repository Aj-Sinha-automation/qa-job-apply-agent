import requests, json

def fetch_jobs(config):
    job_list = []
    for source in config['job_search']['sources']:
        resp = requests.get(source)
        if resp.status_code == 200:
            data = resp.json()
            if 'jobs' in data:
                job_list.extend(data['jobs'])
            elif isinstance(data, list):
                job_list.extend(data)
    with open('data/job_cache.json', 'w') as f:
        json.dump(job_list, f, indent=2)
    return job_list
