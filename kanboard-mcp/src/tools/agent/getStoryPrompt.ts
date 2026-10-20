/**
 * MCP Tool: kanboard_get_story_prompt
 *
 * Returns a structured prompt for a story with acceptance criteria,
 * repo info, dependencies, and required skills.
 */

import { maestroClient, MaestroError, StoryPrompt } from '../../clients/maestroClient.js';

export interface GetStoryPromptParams {
  story_id: number;
}

export interface GetStoryPromptResult {
  success: boolean;
  prompt?: StoryPrompt;
  formatted_prompt?: string;
  error?: string;
}

/**
 * Format the story prompt as a readable string for Claude
 */
function formatPrompt(prompt: StoryPrompt): string {
  const lines: string[] = [
    `# Story ${prompt.story_id}: ${prompt.title}`,
    '',
    '## Description',
    prompt.description || 'No description provided.',
    ''
  ];

  if (prompt.acceptance_criteria.length > 0) {
    lines.push('## Acceptance Criteria');
    for (const ac of prompt.acceptance_criteria) {
      lines.push(`- [ ] ${ac}`);
    }
    lines.push('');
  }

  if (prompt.repo_url) {
    lines.push('## Repository');
    lines.push(`- URL: ${prompt.repo_url}`);
    if (prompt.branch) {
      lines.push(`- Branch: ${prompt.branch}`);
    }
    lines.push('');
  }

  if (prompt.dependencies.length > 0) {
    lines.push('## Dependencies');
    lines.push(`This story depends on: ${prompt.dependencies.join(', ')}`);
    lines.push('Ensure these are complete before proceeding.');
    lines.push('');
  }

  if (prompt.required_skills.length > 0) {
    lines.push('## Required Skills');
    lines.push('Execute these skills in order:');
    for (const skill of prompt.required_skills) {
      lines.push(`1. /${skill}`);
    }
    lines.push('');
  }

  if (prompt.context) {
    lines.push('## Additional Context');
    lines.push(prompt.context);
    lines.push('');
  }

  return lines.join('\n');
}

export async function getStoryPrompt(params: GetStoryPromptParams): Promise<GetStoryPromptResult> {
  try {
    // Validate required params
    if (!params.story_id) {
      return {
        success: false,
        error: 'story_id is required'
      };
    }

    // Get prompt from Maestro API
    const prompt = await maestroClient.getStoryPrompt(params.story_id);

    return {
      success: true,
      prompt,
      formatted_prompt: formatPrompt(prompt)
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

export const getStoryPromptTool = {
  name: 'kanboard_get_story_prompt',
  description: 'Get structured prompt for a story with acceptance criteria, repo, deps, and required skills.',
  inputSchema: {
    type: 'object' as const,
    properties: {
      story_id: {
        type: 'number',
        description: 'The story ID to get prompt for'
      }
    },
    required: ['story_id']
  },
  handler: getStoryPrompt
};
