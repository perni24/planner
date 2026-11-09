export const initialAreaState = {
  areas: null,
  currentArea: null,
  error: null,
  pendingChanges: false,
};

export function areaStateReducer(state, action) {
  switch (action.type) {
    case 'loaded': {
      const areas = action.areas;
      return {
        areas,
        currentArea: areas.find((area) => area.id === state.currentArea?.id) ?? areas[0] ?? null,
        error: null,
        pendingChanges: false,
      };
    }
    case 'loadFailed':
      return { ...state, error: state.pendingChanges ? 'afterWrite' : 'load' };
    case 'selected': {
      const area = state.areas?.find((area) => area.id === action.id);
      return area ? { ...state, currentArea: area } : state;
    }
    case 'saved':
      return { ...state, pendingChanges: true };
    case 'deleted': {
      const areas = state.areas?.filter((area) => area.id !== action.id) ?? null;
      const currentArea = state.currentArea?.id === action.id
        ? areas?.[0] ?? null
        : state.currentArea;
      return { ...state, areas, currentArea, pendingChanges: true };
    }
    default:
      return state;
  }
}
