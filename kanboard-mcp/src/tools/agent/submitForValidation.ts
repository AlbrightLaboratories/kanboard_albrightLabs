/**
 * MCP Tool: kanboard_submit_for_validation
 *
 * Submits a story for validation, moving it to the Validation column
 * and triggering the GitHub validation workflow.
 */

import { maestroClient, MaestroError } from '../../clients/maestroClient.js';
import { kanboardClient, KanboardError } from '../../clients/kanboardClient.js';

export interface SubmitForValidationParams {
  story_id: number;
}

export interface SubmitForValidationResult {
  success: boolean;
  story_id?: number;
  workflow_id?: string;
  column?: string;
  error?: string;
}

export async function submitForValidation(
  params: SubmitForValidationParams
): Promise<SubmitForValidationResult> {
  try {
    // Validate required params
    if (!params.story_id) {
      return {
        success: false,
        error: 'story_id is required'
      };
    }

    // Get the story to find project ID
    const story = await kanboardClient.getStory(params.story_id);
    if (!story) {
      return {
        success: false,
        error: `Story ${params.story_id} not found`
      };
    }

    // Find the Validation column
    const validationColumn = await kanboardClient.getColumnByName(
      story.project_id,
      'Validation'
    );

    if (!validationColumn) {
      return {
        success: false,
        error: 'Validation column not found in project'
      };
    }

    // Move story to Validation column
    await kanboardClient.moveStory(params.story_id, validationColumn.id);

    // Trigger validation workflow via Maestro
    const result = await maestroClient.submitForValidation(params.story_id);

    if (!result.success) {
      return {
        success: false,
        story_id: params.story_id,
        error: result.error || 'Failed to trigger validation workflow'
      };
    }

    return {
      success: true,
      story_id: params.story_id,
      workflow_id: result.workflow_id,
      column: 'Validation'
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

export const submitForValidationTool = {
  name: 'kanboard_submit_for_validation',
  description: 'Submit a story for validation. Moves to Validation column and triggers GitHub workflow.',
  inputSchema: {
    type: 'object' as const,
    properties: {
      story_id: {
        type: 'number',
        description: 'The story ID to submit for validation'
      }
    },
    required: ['story_id']
  },
  handler: submitForValidation
};
