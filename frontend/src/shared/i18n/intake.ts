export const intakeErrors: Record<string,string> = {
  invalid_language:'Укажите код языка: например ar, en или ru.',
  empty_text:'В файле нет читаемого текста. Проверьте документ.',
  unsupported_format:'Поддерживаются TXT, MD, DOCX и PDF с текстовым слоем.',
  file_too_large:'Размер каждого файла — не более 20 МБ.',
  request_too_large:'Общий размер загружаемых файлов слишком велик.',
  scope_too_large:'Выберите соответствующие фрагменты: оригинал — не более 18 000 знаков.',
  pdf_requires_ocr:'В PDF нет текстового слоя. Загрузите распознанный текст.',
  pdf_missing_text_pages:'В PDF есть страницы без текста. Проверьте сканы или пустые страницы и загрузите полный текст. Частичный результат не сохранён.',
  encrypted_pdf:'PDF защищён паролем. Сначала разблокируйте его на своём компьютере.',
  invalid_document:'Не удалось прочитать документ. Сохраните его заново в DOCX, PDF с текстовым слоем или TXT.',
  invalid_utf8:'Сохраните текстовый файл в кодировке UTF-8.',
  invalid_text:'В тексте обнаружены двоичные управляющие символы.',
  invalid_filename:'Укажите корректное имя файла.',
  docx_pending_revisions:'Примите или отклоните отслеживаемые исправления в DOCX перед загрузкой.',
  docx_expansion_limit:'Распакованный DOCX превышает 80 МБ. Загрузите меньший фрагмент или TXT.',
  local_only:'Стенд доступен только на этом компьютере.',
};
const warnings: Record<string,string> = {
  'PDF reading order and character extraction can differ from the page. Review the extracted text before comparison.':'Порядок и символы извлечённого PDF могут отличаться от страницы. Проверьте текст перед сравнением.',
  'DOCX body, table paragraphs, footnotes and endnotes are extracted in document order. Review the preview.':'Извлечены основной текст, абзацы таблиц, обычные и концевые сноски в порядке документа. Проверьте предпросмотр.',
  'Headers, footers, comments and text inside images are not extracted; no OCR is performed.':'Колонтитулы, комментарии и текст на изображениях не извлекаются. OCR не выполнялся.',
};
export const inputWarning = (message:string) => warnings[message] || message;
