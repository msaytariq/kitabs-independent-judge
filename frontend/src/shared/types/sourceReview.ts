export type Proof = {evidence_ids:string[];source_ids?:string[]};
export type SourceReviewData = {
  id:string;version:number;checked_on:string;status:'desk_review';summary_ru:string;
  sources:{id:string;label:string;url:string;summary_ru:string}[];
  evidence:{id:string;role:string;label_ru:string;text:string;start:number;end:number;sha256:string}[];
  benefits:({title_ru:string;detail_ru:string}&Proof)[];
  checks:({id:string;title_ru:string;a_ru:string;b_ru:string;conclusion_ru:string}&Proof)[];
  tasks:({id:string;side:'a'|'b'|'both';title_ru:string;reason_ru:string;draft_ru?:string}&Proof)[];
  limitations_ru:string[];
};
