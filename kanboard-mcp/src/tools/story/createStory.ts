/**
 * MCP Tool: kanboard_create_story
 *
 * Creates a new story in the Kanboard Backlog.
 */

import { kanboardClient, KanboardError } from '../../clients/kanboardClient.js';

export interface CreateStoryParams {
  project_id: number;
  title: string;
  description?: string;
  column_name?: string;
}

export interface CreateStoryResult {
  success: boolean;
  story_id?: number;
  error?: string;
}

export async function createStory(params: CreateStoryParams): Promise<CreateStoryResult> {
  try {
    // Validate required params
    if (!params.project_id || !params.title) {
      return {
        success: false,
        error: 'project_id and title are required'
      };
    }

    // Get column ID if column_name provided, default to "Backlog"
    let columnId: number | undefined;
    const columnName = params.column_name || 'Backlog';

    const column = await kanboardClient.getColumnByName(params.project_id, columnName);
    if (column) {
      columnId = column.id;
    }

    // Create the story
    const storyId = await kanboardClient.createStory(
      params.project_id,
      params.title,
      params.description,
      columnId
    );

    return {
      success: true,
      story_id: storyId
    };
  } catch (error) {
    if (error instanceof KanboardError) {
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

export const createStoryTool = {
  name: 'kanboard_create_story',
  description: 'Create a new story in the Kanboard. Defaults to Backlog column.',
  inputSchema: {
    type: 'object' as const,
    properties: {
      project_id: {
        type: 'number',
        description: 'The project ID to create the story in'
      },
      title: {
        type: 'string',
        description: 'Title of the story'
      },
      description: {
        type: 'string',
        description: 'Description and acceptance criteria for the story'
      },
      column_name: {
        type: 'string',
        description: 'Column name to place story (default: Backlog)'
      }
    },
    required: ['project_id', 'title']
  },
  handler: createStory
};
