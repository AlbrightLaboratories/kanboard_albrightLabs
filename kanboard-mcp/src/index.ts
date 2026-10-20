/**
 * Kanboard MCP Server
 *
 * MCP Server for integrating Kanboard with Claude.
 * Provides tools for story management, skill execution, and validation.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
  TextContent
} from '@modelcontextprotocol/sdk/types.js';

import { createStoryTool, createStory } from './tools/story/createStory.js';
import { claimStoryTool, claimStory } from './tools/agent/claimStory.js';
import { getStoryPromptTool, getStoryPrompt } from './tools/agent/getStoryPrompt.js';
import { executeSkillTool, executeSkill } from './tools/skill/executeSkill.js';
import { submitForValidationTool, submitForValidation } from './tools/agent/submitForValidation.js';
import { reworkStoryTool, reworkStory } from './tools/agent/reworkStory.js';

// Type for tool handlers
type ToolHandler = (params: Record<string, unknown>) => Promise<unknown>;

// Map tool names to handlers
const toolHandlers: Record<string, ToolHandler> = {
  kanboard_create_story: createStory as ToolHandler,
  kanboard_claim_story: claimStory as ToolHandler,
  kanboard_get_story_prompt: getStoryPrompt as ToolHandler,
  kanboard_execute_skill: executeSkill as ToolHandler,
  kanboard_submit_for_validation: submitForValidation as ToolHandler,
  kanboard_rework_story: reworkStory as ToolHandler
};

// All available tools
const tools: Tool[] = [
  {
    name: createStoryTool.name,
    description: createStoryTool.description,
    inputSchema: createStoryTool.inputSchema
  },
  {
    name: claimStoryTool.name,
    description: claimStoryTool.description,
    inputSchema: claimStoryTool.inputSchema
  },
  {
    name: getStoryPromptTool.name,
    description: getStoryPromptTool.description,
    inputSchema: getStoryPromptTool.inputSchema
  },
  {
    name: executeSkillTool.name,
    description: executeSkillTool.description,
    inputSchema: executeSkillTool.inputSchema
  },
  {
    name: submitForValidationTool.name,
    description: submitForValidationTool.description,
    inputSchema: submitForValidationTool.inputSchema
  },
  {
    name: reworkStoryTool.name,
    description: reworkStoryTool.description,
    inputSchema: reworkStoryTool.inputSchema
  }
];

/**
 * Create and configure the MCP server
 */
export function createServer(): Server {
  const server = new Server(
    {
      name: 'kanboard-mcp',
      version: '1.0.0'
    },
    {
      capabilities: {
        tools: {}
      }
    }
  );

  // Handle tool listing
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return { tools };
  });

  // Handle tool calls
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    const handler = toolHandlers[name];
    if (!handler) {
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: false,
              error: `Unknown tool: ${name}`
            })
          } as TextContent
        ]
      };
    }

    try {
      const result = await handler(args as Record<string, unknown>);
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(result, null, 2)
          } as TextContent
        ]
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: false,
              error: error instanceof Error ? error.message : String(error)
            })
          } as TextContent
        ]
      };
    }
  });

  return server;
}

/**
 * Main entry point
 */
async function main(): Promise<void> {
  const server = createServer();
  const transport = new StdioServerTransport();

  await server.connect(transport);

  // Log startup (to stderr so it doesn't interfere with MCP protocol)
  console.error('Kanboard MCP Server started');
  console.error(`Tools available: ${tools.map(t => t.name).join(', ')}`);
}

// Run if executed directly
main().catch((error) => {
  console.error('Failed to start server:', error);
  process.exit(1);
});

export { tools, toolHandlers };
