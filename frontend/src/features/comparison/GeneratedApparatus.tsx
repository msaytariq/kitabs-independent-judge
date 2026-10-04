import type {GeneratedApparatusEvidence} from '../../shared/types/comparison';

export function GeneratedApparatus({evidence}:{evidence:GeneratedApparatusEvidence}) {
  return <section className="panel generated-apparatus">
    <span className="eyebrow">Возможности платформы</span>
    <h2>Научный аппарат, созданный Kitabs</h2>
    <p>Платформа формирует справочный материал к переводу. В сохранённом результате уже подготовлены:</p>
    <div className="apparatus-capabilities">{evidence.groups.map(group=><section key={group.id}>
      <div className="capability-count">{group.count}</div><h3>{group.title_ru}</h3>
      <p>{group.purpose_ru}</p><details><summary>Примеры из результата</summary>
        {group.examples.map(item=><blockquote key={item.start} dir="auto">{item.text}</blockquote>)}
      </details></section>)}</div>
    <p className="muted">Область доказательства: {evidence.scope_label_ru}. Сводка замечаний относится к выбранному фрагменту.</p>
    <details><summary>Что подтверждает это доказательство</summary>
      <p>Наличие разделов и записей подтверждено сохранённым артефактом. Их подготовка показывает возможность Kitabs создавать научный аппарат. Редактор получает уже собранные материалы для дальнейшей работы.</p>
      <p>Точность справок и достаточность источников требуют отдельной проверки. Количество записей не является числом уникальных персон или подтверждённых научных выводов.</p>
      <p>Хэш результата: <code>{evidence.artifact_sha256}</code></p>
    </details>
  </section>;
}
