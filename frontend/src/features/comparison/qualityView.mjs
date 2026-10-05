/** Only a provisional index leader. Missing evidence never becomes a tie. */
export function conclusionKey(ratings) {
  if(ratings.sides.a.total===null||ratings.sides.b.total===null)return 'unknown';
  return ratings.sides.a.total===ratings.sides.b.total?'tie':ratings.sides.a.total>ratings.sides.b.total?'a':'b';
}
export const qualityRows=['total','accuracy','terminology','readability','apparatus'];
