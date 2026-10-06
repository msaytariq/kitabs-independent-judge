"""Resolve three independent input methods before atomic draft creation."""
from independent_judge.application.intake import Upload
from independent_judge.domain.errors import InputError
from independent_judge.url_ports import DocumentRetriever


class MixedIntake:
    def __init__(self, intake, retriever: DocumentRetriever):
        self.intake, self.retriever = intake, retriever

    def create(self, entries, files, source_language, target_language):
        # Validate all requested methods before fetching any document.
        for role in ('source', 'a', 'b'):
            item = entries[role]
            if item['kind'] not in ('text', 'url', 'file'):
                raise InputError('invalid_input_method', 'Choose text, file or URL for each input.')
            if item['kind'] == 'file' and role not in files:
                raise InputError('missing_input', 'Provide all three input materials.')
            if item['kind'] != 'file' and not item['value'].strip():
                raise InputError('missing_input', 'Provide all three input materials.')
        uploads = []
        for role in ('source', 'a', 'b'):
            item = entries[role]
            if item['kind'] == 'file':
                uploads.append(files[role])
            elif item['kind'] == 'text':
                # A browser sends form line breaks as CRLF; the text on the screen has LF.
                text = item['value'].replace('\r\n', '\n')
                uploads.append(Upload(text.encode('utf-8'), role + '.txt', 'text/plain'))
            else:
                remote = self.retriever.fetch(item['value'])
                uploads.append(Upload(remote.content, remote.filename, remote.content_type, remote.provenance))
        return self.intake.create(*uploads, source_language, target_language)
