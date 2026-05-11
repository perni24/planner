export interface Area {
  id: number;
  name: string;
}

export type AreaCreate = Omit<Area, 'id'>;

export type AreaUpdate = Partial<AreaCreate>;
