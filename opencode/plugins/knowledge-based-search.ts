type ToolExecutionInput = { tool: string };
type ToolExecutionOutput = { args: Record<string, unknown> };
type Plugin = () => {
	"tool.execute.before": (
		input: ToolExecutionInput,
		output: ToolExecutionOutput,
	) => void;
};

const KBS_COMMAND = /(^|[;&|]\s*)([A-Za-z_][A-Za-z0-9_]*=\S+\s+)*kbs(\s|$)/;
const WEB_SEARCH_DENY_REASON =
	"Built-in web search is disabled. Use kbs through Bash or a configured Linkup tool instead.";
const SKILL_DENY_REASON =
	"Load the knowledge-based-search skill first, then rerun the kbs command.";

export const KnowledgeBasedSearch: Plugin = () => {
	let skillLoaded = false;

	return {
		"tool.execute.before": (input, output) => {
			const args = output.args;
			if (
				input.tool === "skill" &&
				(args.name === "knowledge-based-search" ||
					args.skill === "knowledge-based-search")
			) {
				skillLoaded = true;
				return;
			}
			if (input.tool === "websearch") {
				throw new Error(WEB_SEARCH_DENY_REASON);
			}
			if (
				input.tool === "bash" &&
				typeof args.command === "string" &&
				KBS_COMMAND.test(args.command) &&
				!skillLoaded
			) {
				throw new Error(SKILL_DENY_REASON);
			}
		},
	};
};
