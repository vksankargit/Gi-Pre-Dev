with open(r'C:\GI-Pre-Dev\temp_update_project_status_view.py') as f:
    content = f.read()

with open(r'C:\GI-Pre-Dev\reviews\views.py', 'a') as v:
    v.write('\n\n')
    v.write(content)

print('View appended successfully')