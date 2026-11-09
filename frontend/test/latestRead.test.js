import assert from 'node:assert/strict';
import test from 'node:test';
import { createLatestRead } from '../src/utils/latestRead.js';

test('only the latest response is applied when reads finish out of order', async () => {
  const reader = createLatestRead();
  const first = Promise.withResolvers();
  const second = Promise.withResolvers();
  const received = [];
  let firstSignal;

  const firstRun = reader.run((signal) => {
    firstSignal = signal;
    return first.promise;
  }, (data) => received.push(data), assert.fail);
  const secondRun = reader.run(() => second.promise, (data) => received.push(data), assert.fail);

  assert.equal(firstSignal.aborted, true);
  second.resolve('new data');
  await secondRun;
  first.resolve('old data');
  await firstRun;
  assert.deepEqual(received, ['new data']);
});

test('switching scope prevents old data and delayed reloads from being applied', async () => {
  const firstScope = createLatestRead();
  const secondScope = createLatestRead();
  const pending = Promise.withResolvers();
  let signal;
  const run = firstScope.run((currentSignal) => {
    signal = currentSignal;
    return pending.promise;
  }, assert.fail, assert.fail);

  firstScope.dispose();
  assert.equal(signal.aborted, true);
  await firstScope.run(assert.fail, assert.fail, assert.fail);

  const received = [];
  await secondScope.run(async () => 'new scope', (data) => received.push(data), assert.fail);
  pending.resolve('old scope');
  await run;
  assert.deepEqual(received, ['new scope']);
});

test('only errors from the current request are reported', async () => {
  const reader = createLatestRead();
  const pending = Promise.withResolvers();
  const errors = [];
  const onError = (error) => errors.push(error);
  const obsolete = reader.run(() => pending.promise, assert.fail, onError);
  const currentError = new Error('Current request failed');

  await reader.run(async () => { throw currentError; }, assert.fail, onError);
  pending.reject(new Error('Obsolete request failed'));
  await obsolete;
  assert.deepEqual(errors, [currentError]);
});

test('an old request finishing does not prevent cancellation of the current one', async () => {
  const reader = createLatestRead();
  const first = Promise.withResolvers();
  const second = Promise.withResolvers();
  let secondSignal;
  const firstRun = reader.run(() => first.promise, assert.fail, assert.fail);
  const secondRun = reader.run((signal) => {
    secondSignal = signal;
    return second.promise;
  }, assert.fail, assert.fail);

  first.resolve('old data');
  await firstRun;
  reader.dispose();
  assert.equal(secondSignal.aborted, true);
  second.resolve('data after leaving');
  await secondRun;
});

test('refreshing one resource does not cancel the other resource', async () => {
  const project = createLatestRead();
  const tasks = createLatestRead();
  const pending = Promise.withResolvers();
  let projectSignal;
  const projectData = [];
  const taskData = [];
  const projectRun = project.run((signal) => {
    projectSignal = signal;
    return pending.promise;
  }, (data) => projectData.push(data), assert.fail);

  await tasks.run(async () => ['task'], (data) => taskData.push(data), assert.fail);
  assert.equal(projectSignal.aborted, false);
  pending.resolve('project');
  await projectRun;
  assert.deepEqual(projectData, ['project']);
  assert.deepEqual(taskData, [['task']]);
});
