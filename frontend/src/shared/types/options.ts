export type Effort = {reduction_percent:number|null;edit_reduction_percent:number|null;
  sensitivity_percent:[number,number]|null;sides:Record<'a'|'b',{edits:number|null;units:number|null;excluded:number}>};
export type HadithCandidate = {id:string;collection:string;number:number|string;text:string;url:string;
  edition:string;retrieved_at:string;snapshot_sha256:string;english_text?:string;grade?:string};
export type HadithResult = {status:string;library?:string;detected_count?:number;checked_count?:number;
  official?:{source:string;status:string;limit_reached?:boolean;records:{quote:string;status:string;record:HadithCandidate|null}[]};
  verified_count:number|null;limit_reached?:boolean;items:{quote:string;status:string;candidate_count:number;
    candidates:HadithCandidate[]}[]};
export type RunState = {id:string|null;status:string;error:string|null};
