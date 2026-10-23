/**
 * WorkerRegistration Component
 *
 * Form to register new LLM worker.
 * Implements UI-12.
 */

import { useState } from 'react';
import { useWorkers } from '../../hooks/useKanboard';

export interface WorkerRegistrationProps {
  onSuccess?: () => void;
  onCancel?: () => void;
}

const WORKER_TYPES = ['claude', 'gemini', 'codex', 'ollama', 'vllm', 'custom'];
const CAPABILITIES = [
  'code_generation',
  'code_review',
  'terminal_execution',
  'file_operations',
  'git_operations',
  'test_execution',
  'skill_execution',
  'validation'
];

export function WorkerRegistration({ onSuccess, onCancel }: WorkerRegistrationProps) {
  const { registerWorker } = useWorkers();
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const [name, setName] = useState('');
  const [type, setType] = useState('ollama');
  const [labels, setLabels] = useState('');
  const [capabilities, setCapabilities] = useState<string[]>(['code_generation']);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!type) {
      newErrors.type = 'Type is required';
    }

    if (capabilities.length === 0) {
      newErrors.capabilities = 'At least one capability is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    setSubmitting(true);
    try {
      await registerWorker({
        name: name.trim(),
        type,
        labels: labels.split(',').map(l => l.trim()).filter(l => l),
        capabilities
      });
      onSuccess?.();
    } catch (error) {
      setErrors({
        submit: error instanceof Error ? error.message : 'Failed to register worker'
      });
    } finally {
      setSubmitting(false);
    }
  };

  const toggleCapability = (cap: string) => {
    setCapabilities(prev =>
      prev.includes(cap)
        ? prev.filter(c => c !== cap)
        : [...prev, cap]
    );
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="worker-registration"
      data-testid="worker-registration"
    >
      <h3>Register New Worker</h3>

      <div className="field">
        <label htmlFor="worker-name">Name *</label>
        <input
          id="worker-name"
          type="text"
          value={name}
          onChange={e => setName(e.target.value)}
          placeholder="e.g., Ollama-Llama3-70B"
          data-testid="name-input"
        />
        {errors.name && <span className="error">{errors.name}</span>}
      </div>

      <div className="field">
        <label htmlFor="worker-type">Type *</label>
        <select
          id="worker-type"
          value={type}
          onChange={e => setType(e.target.value)}
          data-testid="type-select"
        >
          {WORKER_TYPES.map(t => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
        {errors.type && <span className="error">{errors.type}</span>}
      </div>

      <div className="field">
        <label htmlFor="worker-labels">Labels (comma-separated)</label>
        <input
          id="worker-labels"
          type="text"
          value={labels}
          onChange={e => setLabels(e.target.value)}
          placeholder="python, backend, gpu-required"
          data-testid="labels-input"
        />
      </div>

      <div className="field">
        <label>Capabilities *</label>
        <div className="capability-checkboxes" data-testid="capabilities">
          {CAPABILITIES.map(cap => (
            <label key={cap} className="checkbox-label">
              <input
                type="checkbox"
                checked={capabilities.includes(cap)}
                onChange={() => toggleCapability(cap)}
                data-testid={`cap-${cap}`}
              />
              {cap.replace(/_/g, ' ')}
            </label>
          ))}
        </div>
        {errors.capabilities && <span className="error">{errors.capabilities}</span>}
      </div>

      {errors.submit && (
        <div className="submit-error" data-testid="submit-error">
          {errors.submit}
        </div>
      )}

      <div className="form-actions">
        <button
          type="submit"
          disabled={submitting}
          className="submit-button"
          data-testid="submit-button"
        >
          {submitting ? 'Registering...' : 'Register Worker'}
        </button>
        {onCancel && (
          <button type="button" onClick={onCancel} className="cancel-button">
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}

export default WorkerRegistration;
