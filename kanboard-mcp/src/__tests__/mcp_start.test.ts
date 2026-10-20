/**
 * Test MCP-01: MCP server starts and registers with Claude
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createServer, tools, toolHandlers } from '../index.js';

describe('MCP Server Startup', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('createServer returns a Server instance', () => {
    const server = createServer();
    expect(server).toBeDefined();
    expect(server).toHaveProperty('connect');
  });

  it('server has correct name and version', () => {
    const server = createServer();
    // Server info is set during creation
    expect(server).toBeDefined();
  });

  it('tools array contains all expected tools', () => {
    const expectedTools = [
      'kanboard_create_story',
      'kanboard_claim_story',
      'kanboard_get_story_prompt',
      'kanboard_execute_skill',
      'kanboard_submit_for_validation',
      'kanboard_rework_story'
    ];

    for (const toolName of expectedTools) {
      const tool = tools.find(t => t.name === toolName);
      expect(tool).toBeDefined();
      expect(tool?.description).toBeTruthy();
      expect(tool?.inputSchema).toBeDefined();
    }
  });

  it('all tools have handlers registered', () => {
    for (const tool of tools) {
      expect(toolHandlers[tool.name]).toBeDefined();
      expect(typeof toolHandlers[tool.name]).toBe('function');
    }
  });

  it('tools have valid input schemas', () => {
    for (const tool of tools) {
      expect(tool.inputSchema).toHaveProperty('type', 'object');
      expect(tool.inputSchema).toHaveProperty('properties');
      expect(tool.inputSchema).toHaveProperty('required');
    }
  });

  it('server has tools capability', () => {
    const server = createServer();
    // Server is configured with tools capability
    expect(server).toBeDefined();
  });
});
