export type RubricEvidence={id:string;source_quote:string;translation_quote:string;kind:string;
  explanation_en:string;explanation_ru:string;verified:boolean};
export type RubricSide={score:number|null;status:string;explanation_en:string;explanation_ru:string;evidence:RubricEvidence[]};
export type RubricResult={version:string;winner:'a'|'b'|'tie'|null;totals:Record<'a'|'b',number|null>;
  criteria:{criterion:string;a:RubricSide;b:RubricSide}[];unique_defects:Record<'a'|'b',number>};
export type ProcessingSide={pipeline_seconds:number|null;audit_operations:number|null;editor_operations:number|null;
  simulated_seconds:number|null;total_seconds:number|null;reason?:string|null;job_id?:string|null;
  operations:{stage:string;chunk_id:string;edit_id:string;before:string;after:string}[]};
export type ProcessingEffort={sides:Record<'a'|'b',ProcessingSide>;version:string};
