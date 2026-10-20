/**
 * MCP Tool: kanboard_rework_story
 *
 * Picks up a failed story for rework after validation failure.
 * Returns the failure information so agent can fix the issues.
 */

import { maestroClient, MaestroError } from '../../clients/maestroClient.js';
import { kanboardClient, KanboardError } from '../../clients/kanboardClient.js';

export interface ReworkStoryParams {
  story_id: number;
}

export interface ReworkStoryResult {
  success: boolean;
  story_id?: number;
  title?: string;
  failures?: string[];
  agent_id?: string;
  error?: string;
}

export async function reworkStory(params: ReworkStoryParams): Promise<ReworkStoryResult> {
  try {
    // Validate required params
    if (!params.story_id) {
      return {
        success: false,
        error: 'story_id is required'
      };
    }

    // Verify story exists
    const story = await kanboardClient.getStory(params.story_id);
    if (!story) {
      return {
        success: false,
        error: `Story ${params.story_id} not found`
      };
    }

    // Rework via Maestro API
    const result = await maestroClient.reworkStory(params.story_id);

    if (!result.success) {
      return {
        success: false,
        story_id: params.story_id,
        error: result.error || 'Failed to pick up story for rework'
      };
    }

    return {
      success: true,
      story_id: params.story_id,
      title: story.title,
      failures: result.failures,
      agent_id: maestroClient.currentAgentId
    };
  } catch (error) {
    if (error instanceof MaestroError || error instanceof KanboardError) {
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

export const reworkStoryTool = {
  name: 'kanboard_rework_story',
  description: 'Pick up a failed story for rework. Returns failure details to fix.',
  inputSchema: {
    type: 'object' as const,
    properties: {
      story_id: {
        type: 'number',
        description: 'The failed story ID to rework'
      }
    },
    required: ['story_id']
  },
  handler: reworkStory
};
