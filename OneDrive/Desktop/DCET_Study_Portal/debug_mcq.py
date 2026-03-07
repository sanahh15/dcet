from app import app, db, MCQ, sample_mcqs

with app.test_client() as c:
    for slug in ['engineering_mathematics','statistics_analytics','it_skills','feee','pms']:
        resp = c.get(f'/instructor/generate_mcqs/{slug}')
        print(slug, '->', resp.data.decode())

print("\nsample_mcqs lengths:")
for subj, lst in sample_mcqs.items():
    print(subj, len(lst))

with app.app_context():
    for subj in ['Engineering Mathematics','Statistics & Analytics','IT Skills','FEEE','PMS']:
        count = MCQ.query.filter_by(subject=subj).count()
        print(subj, 'count', count)
