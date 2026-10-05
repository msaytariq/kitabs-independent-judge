// The public build is served under a path prefix (for example /judge); the local stand has none.
export const apiUrl=(path:string)=>(process.env.NEXT_PUBLIC_BASE_PATH||'')+path;
