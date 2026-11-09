import assert from 'node:assert/strict';
import test from 'node:test';
import { areaStateReducer, initialAreaState } from '../src/utils/areaState.js';
import en from '../../backend/locales/en.json' with { type: 'json' };
import it from '../../backend/locales/it.json' with { type: 'json' };

const work = { id: 1, name: 'Work' };
const home = { id: 2, name: 'Home' };

function loadedAreas(areas = [work, home]) {
  return areaStateReducer(initialAreaState, { type: 'loaded', areas });
}

test('an initial load failure leaves no areas and identifies a read error', () => {
  const failed = areaStateReducer(initialAreaState, { type: 'loadFailed' });
  assert.equal(failed.areas, null);
  assert.equal(failed.currentArea, null);
  assert.equal(failed.error, 'load');
});

test('a failed read after saving retains the list and the selected area', () => {
  const selected = areaStateReducer(loadedAreas(), { type: 'selected', id: home.id });
  const saved = areaStateReducer(selected, { type: 'saved' });
  const failed = areaStateReducer(saved, { type: 'loadFailed' });
  assert.equal(failed.areas, selected.areas);
  assert.equal(failed.currentArea, home);
  assert.equal(failed.error, 'afterWrite');

  const retryFailed = areaStateReducer(failed, { type: 'loadFailed' });
  assert.deepEqual(retryFailed, failed);

  const renamed = { ...home, name: 'Personal' };
  const refreshed = areaStateReducer(failed, { type: 'loaded', areas: [work, renamed] });
  assert.equal(refreshed.currentArea, renamed);
  assert.equal(refreshed.error, null);
  assert.equal(refreshed.pendingChanges, false);
  assert.equal(areaStateReducer(refreshed, { type: 'loadFailed' }).error, 'load');
});

test('a confirmed deletion cannot leave the deleted area selectable after a read failure', () => {
  const deleted = areaStateReducer(loadedAreas(), { type: 'deleted', id: work.id });
  const failed = areaStateReducer(deleted, { type: 'loadFailed' });
  assert.deepEqual(failed.areas, [home]);
  assert.equal(failed.currentArea, home);
  assert.equal(failed.error, 'afterWrite');
  assert.equal(areaStateReducer(failed, { type: 'selected', id: work.id }), failed);
});

test('deleting the last known area leaves a retryable error until the replacement is loaded', () => {
  const deleted = areaStateReducer(loadedAreas([work]), { type: 'deleted', id: work.id });
  const failed = areaStateReducer(deleted, { type: 'loadFailed' });
  assert.deepEqual(failed.areas, []);
  assert.equal(failed.currentArea, null);
  assert.equal(failed.error, 'afterWrite');

  const replacement = { id: 3, name: 'utente' };
  const refreshed = areaStateReducer(failed, { type: 'loaded', areas: [replacement] });
  assert.equal(refreshed.currentArea, replacement);
  assert.equal(refreshed.error, null);
});

test('the area load notices and retry button are available in both dictionaries', () => {
  for (const dictionary of [it, en]) {
    for (const key of ['actions.retry', 'errors.load', 'errors.refresh', 'errors.afterWrite']) {
      assert.ok(dictionary[`areaSwitcher.${key}`]?.trim(), key);
    }
  }
});
