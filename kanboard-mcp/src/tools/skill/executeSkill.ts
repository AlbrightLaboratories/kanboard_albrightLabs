/**
 * MCP Tool: kanboard_execute_skill
 *
 * Triggers execution of a mandatory skill (plan, design-a-prd, tdd, prove-it, release-it)
 * and returns an execution ID for tracking.
 */

import { maestroClient, MaestroError, SkillExecution } from '../../clients/maestroClient.js';

export interface ExecuteSkillParams {
  story_id: number;
  skill_name: string;
  params?: Record<string, unknown>;
}

export interface ExecuteSkillResult {
  success: boolean;
  execution_id?: string;
  skill_name?: string;
  status?: string;
  error?: string;
}

const VALID_SKILLS = ['plan', 'design-a-prd', 'tdd', 'prove-it', 'release-it'];

export async function executeSkill(params: ExecuteSkillParams): Promise<ExecuteSkillResult> {
  try {
    // Validate required params
    if (!params.story_id || !params.skill_name) {
      return {
        success: false,
        error: 'story_id and skill_name are required'
      };
    }

    // Validate skill name
    if (!VALID_SKILLS.includes(params.skill_name)) {
      return {
        success: false,
        error: `Invalid skill: ${params.skill_name}. Valid skills: ${VALID_SKILLS.join(', ')}`
      };
    }

    // Execute skill via Maestro API
    const execution = await maestroClient.executeSkill(
      params.story_id,
      params.skill_name,
      params.params
    );

    return {
      success: true,
      execution_id: execution.execution_id,
      skill_name: execution.skill_name,
      status: execution.status
    };
  } catch (error) {
    if (error instanceof MaestroError) {
      return {
        success: false,
        error: error.message
      };
    }
    return {
      success: false,
      error: String(error)
    };
  }
}

export const executeSkillTool = {
  name: 'kanboard_execute_skill',
  description: 'Execute a mandatory skill (plan, design-a-prd, tdd, prove-it, release-it) and get execution ID.',
  inputSchema: {
    type: 'object' as const,
    properties: {
      story_id: {
        type: 'number',
        description: 'The story ID to execute skill for'
      },
      skill_name: {
        type: 'string',
        description: 'Name of the skill to execute',
        enum: VALID_SKILLS
      },
      params: {
        type: 'object',
        description: 'Optional parameters for the skill'
      }
    },
    required: ['story_id', 'skill_name']
  },
  handler: executeSkill
};
