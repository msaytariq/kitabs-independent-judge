"""Positive capability evidence section for the Russian comparison report."""
from html import escape


def apparatus_html(evidence: dict | None) -> str:
    if not evidence: return ''
    groups = ''.join(f'<section><h3>{g["count"]} — {escape(g["title_ru"])}</h3>'
                     f'<p>{escape(g["purpose_ru"])}</p>' + ''.join(
                         f'<blockquote dir="auto">{escape(item["text"])}</blockquote>'
                         for item in g['examples']) + '</section>' for g in evidence['groups'])
    return f'''<section style="border:2px solid #155b4b;padding:20px;border-radius:12px">
    <h2>Научный аппарат, созданный Kitabs</h2>
    <p>Платформа формирует справочный материал к переводу. В сохранённом результате уже подготовлены следующие разделы:</p>
    {groups}<p>Область доказательства: {escape(evidence['scope_label_ru'])}.</p>
    <p>Наличие разделов и приведённых записей подтверждено исходным артефактом. Проверка точности справок и достаточности источников — отдельная редакторская задача.</p>
    <p>Хэш результата: <code>{escape(evidence['artifact_sha256'])}</code>.</p></section>'''
