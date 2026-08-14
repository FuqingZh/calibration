#!/usr/bin/env bun

/**
 * Configure the pinned upstream MCP adapter without spending a model turn.
 *
 * The preview and one-time confirmation must execute in this same process;
 * splitting them would discard the upstream server's in-memory confirmation
 * record and would no longer test the real installation contract.
 */

import { pathToFileURL } from "node:url";

const [serverPath, workspace, model, effort] = Bun.argv.slice(2);
if (!serverPath || !workspace || !model || !effort) {
  throw new Error("usage: configure_advisor.ts SERVER WORKSPACE MODEL EFFORT");
}

const server = await import(pathToFileURL(serverPath).href);
const saved = await server.callTool("save_preferences", {
  client: "codex",
  scope: "project",
  workspace,
  orchestrator: {
    model: "inherit",
    recommendation: { model, effort },
  },
  roles: {
    routine: { model, effort },
    high: { model, effort },
    advisor: { model, effort, readonly: true },
  },
});
const preview = await server.callTool("render_client_adapter", { workspace });
const installed = await server.callTool("install_client_adapter", {
  workspace,
  confirmationToken: preview.confirmationToken,
});
const validated = await server.callTool("validate_configuration", { workspace });

process.stdout.write(
  JSON.stringify(
    {
      profileKey: saved.profileKey,
      planDigest: preview.planDigest,
      installed: installed.installed,
      status: validated.status,
      valid: validated.valid,
    },
    null,
    2,
  ) + "\n",
);
