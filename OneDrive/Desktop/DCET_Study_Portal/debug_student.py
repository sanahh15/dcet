from app import app

with app.test_client() as c:
    for slug in ['engineering_mathematics','statistics_analytics','it_skills','feee','pms']:
        resp = c.get(f'/student/test/{slug}')
        data = resp.data.decode('utf-8')
        print(slug, 'status', resp.status_code, 'question divs', data.count('class="question"'))
