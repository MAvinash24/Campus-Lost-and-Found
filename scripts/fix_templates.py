from pathlib import Path
p=Path('templates/inbox.html')
p.write_text(p.read_text().replace("{% if m.recipient_id==user.id %}","{% if m.recipient_id==user.id and m.status=='open' and m.moderation=='verified' %}"))
p=Path('templates/admin.html')
p.write_text(p.read_text().replace('<h2>Recent security activity</h2>',"<div class='form-actions'>{% if page>1 %}<a href=\"{{ url_for('admin',page=page-1) }}\">Previous page</a>{% endif %}<span>Page {{ page }}</span>{% if has_next %}<a href=\"{{ url_for('admin',page=page+1) }}\">Next page</a>{% endif %}</div><h2>Recent security activity</h2>"))
