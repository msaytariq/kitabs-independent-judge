export const intakeErrors: Record<string,string> = {
  invalid_language:'Укажите код языка: например ar, en или ru.',
  empty_text:'В файле нет читаемого текста. Проверьте документ.',
  unsupported_format:'Поддерживаются TXT, MD, DOCX и PDF с текстовым слоем.',
  file_too_large:'Размер каждого файла — не более 20 МБ.',
  request_too_large:'Общий размер загружаемых файлов слишком велик.',
  scope_too_large:'Выберите соответствующие фрагменты: оригинал — не более 18 000 знаков.',
  pdf_requires_ocr:'В PDF нет текстового слоя. Загрузите распознанный текст.',
  pdf_missing_text_pages:'В PDF есть страницы без текста. Проверьте сканы или пустые страницы и загрузите полный текст. Частичный результат не сохранён.',
  pdf_arabic_order_damaged:'В текстовом слое PDF арабские буквы стоят в неправильном порядке (например, «هللا» вместо «الله»). Загрузите DOCX или TXT либо PDF с правильным текстовым слоем. Ничего не сохранено.',
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

const englishErrors:Record<string,string>={
  scope_too_large:'Select matching passages with at most 18,000 source characters.',
  source_page_limit:'Use at most 10 physical source PDF pages. Nothing was truncated.',
  private_url:'Local and private network URLs are not allowed.',
  url_unavailable:'Cannot retrieve this URL. Upload the document instead.',
  unsupported_url_content:'Use a text, HTML, DOCX or PDF document URL.',
  file_too_large:'Each document must be at most 20 MiB.',
  missing_input:'Provide all three materials before comparison.',
  judge_disabled:'Live judging requires an operator-configured model and approved budget.',
  network:'The local server is unavailable. Your materials remain on screen.',
  polling:'Cannot read the run status. Work continues on the server.',
  references:'Cannot check sources now. Try again later.',
};
Object.assign(intakeErrors,{
  source_page_limit:'Загрузите не более 10 физических страниц оригинала PDF. Ничего не обрезано.',
  private_url:'Ссылки на локальные и частные сетевые адреса запрещены.',
  url_unavailable:'Не удалось получить документ по ссылке. Загрузите файл.',
  unsupported_url_content:'Нужна ссылка на TXT, HTML, DOCX или PDF.',
  missing_input:'Добавьте все три материала перед сравнением.',
  network:'Локальный сервер недоступен. Материалы на экране сохранены.',
  polling:'Не удалось получить состояние. Запуск продолжается на сервере.',
  references:'Не удалось проверить источники. Повторите позднее.',
});
export function intakeError(code:string,message:string,locale:string):string{
  if(locale==='ru')return intakeErrors[code]||message||'Не удалось выполнить действие.';
  return englishErrors[code]||(!/[А-Яа-я]/.test(message)&&message)||`Cannot complete this action (${code||'request failed'}).`;
}
export const currentError=(code:string,message='')=>intakeError(code,message,
  typeof document==='undefined'?'en':document.documentElement.lang);
