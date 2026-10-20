/**
 * MCP Tool: kanboard_claim_story
 *
 * Claims a story for the Claude agent to work on.
 * Uses Maestro API to coordinate agent claims.
 */

import { maestroClient, MaestroError } from '../../clients/maestroClient.js';
import { kanboardClient, KanboardError } from '../../clients/kanboardClient.js';

export interface ClaimStoryParams {
  story_id: number;
}

export interface ClaimStoryResult {
  success: boolean;
  story_id?: number;
  title?: string;
  agent_id?: string;
  error?: string;
}

export async function claimStory(params: ClaimStoryParams): Promise<ClaimStoryResult> {
  try {
    // Validate required params
    if (!params.story_id) {
      return {
        success: false,
        error: 'story_id is required'
      };
    }

    // Verify story exists in Kanboard
    const story = await kanboardClient.getStory(params.story_id);
    if (!story) {
      return {
        success: false,
        error: `Story ${params.story_id} not found`
      };
    }

    // Claim via Maestro API
    const claimResult = await maestroClient.claimStory(params.story_id);

    if (!claimResult.success) {
      return {
        success: false,
        story_id: params.story_id,
        error: claimResult.error || 'Failed to claim story'
      };
    }

    return {
      success: true,
      story_id: params.story_id,
      title: story.title,
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

export const claimStoryTool = {
  name: 'kanboard_claim_story',
  description: 'Claim a story to work on. Prevents other agents from working on the same story.',
  inputSchema: {
    type: 'object' as const,
    properties: {
      story_id: {
        type: 'number',
        description: 'The story ID to claim'
      }
    },
    required: ['story_id']
  },
  handler: claimStory
};
