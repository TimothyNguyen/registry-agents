# GitHub MCP

Remote GitHub MCP configuration for repository, issue, pull request, Actions,
Dependabot, and code-security workflows.

Default policy: allowlist required toolsets and keep write operations disabled.
Enable writes only for an explicitly approved workflow. See GitHub's server
configuration guidance for read-only and toolset controls:
<https://github.com/github/github-mcp-server/blob/main/docs/server-configuration.md>.
