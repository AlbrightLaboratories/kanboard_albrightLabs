/**
 * Custom hooks for Kanboard API interactions
 */

import { useState, useEffect, useCallback } from 'react';
import { kanboardAPI, Story, Column, Agent, Worker, ValidationResult, SkillProgress } from '../api/kanboard';

export function useStories(projectId: number) {
  const [stories, setStories] = useState<Story[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      const data = await kanboardAPI.getStories(projectId);
      setStories(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load stories');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const moveStory = useCallback(async (storyId: number, columnId: number, position?: number) => {
    await kanboardAPI.moveStory(storyId, columnId, position);
    await refresh();
  }, [refresh]);

  return { stories, loading, error, refresh, moveStory };
}

export function useColumns(projectId: number) {
  const [columns, setColumns] = useState<Column[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    kanboardAPI.getColumns(projectId)
      .then(setColumns)
      .finally(() => setLoading(false));
  }, [projectId]);

  return { columns, loading };
}

export function useAgents() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    const data = await kanboardAPI.getAgents();
    setAgents(data);
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [refresh]);

  return { agents, loading, refresh };
}

export function useWorkers() {
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await kanboardAPI.getWorkers();
      setWorkers(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load workers');
    }
  }, []);

  useEffect(() => {
    refresh().finally(() => setLoading(false));
    const interval = setInterval(refresh, 30000);
    return () => clearInterval(interval);
  }, [refresh]);

  const registerWorker = useCallback(async (
    worker: Omit<Worker, 'worker_id' | 'status' | 'last_heartbeat'>
  ) => {
    const newWorker = await kanboardAPI.registerWorker(worker);
    await refresh();
    return newWorker;
  }, [refresh]);

  return { workers, loading, error, refresh, registerWorker };
}

export function useValidation(storyId: number) {
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    kanboardAPI.getValidationResult(storyId)
      .then(setResult)
      .finally(() => setLoading(false));
  }, [storyId]);

  const triggerRework = useCallback(async () => {
    await kanboardAPI.triggerRework(storyId);
  }, [storyId]);

  return { result, loading, triggerRework };
}

export function useSkillProgress(storyId: number) {
  const [progress, setProgress] = useState<SkillProgress | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    kanboardAPI.getSkillProgress(storyId)
      .then(setProgress)
      .finally(() => setLoading(false));
  }, [storyId]);

  const isComplete = progress?.skills.every(s => s.status === 'passed') ?? false;
  const canMoveToDone = isComplete;

  return { progress, loading, isComplete, canMoveToDone };
}

export function useDependencyGraph(storyId: number) {
  const [graph, setGraph] = useState<{
    nodes: { id: number; title: string }[];
    edges: { from: number; to: number; type: string }[];
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    kanboardAPI.getDependencyGraph(storyId)
      .then(setGraph)
      .finally(() => setLoading(false));
  }, [storyId]);

  return { graph, loading };
}
