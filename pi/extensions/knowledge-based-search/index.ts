type ToolCallEvent = {
	toolName: string;
	input: { command?: string };
};

type ExtensionContext = {
	sessionManager: { getEntries(): unknown };
};

type ExtensionAPI = {
	on(
		event: "tool_call",
		handler: (
			event: ToolCallEvent,
			ctx: ExtensionContext,
		) => { block: true; reason: string } | undefined,
	): void;
};

const KBS_COMMAND = /(^|[;&|]\s*)([A-Za-z_][A-Za-z0-9_]*=\S+\s+)*kbs(\s|$)/;
const WEB_SEARCH_TOOLS = new Set(["WebSearch", "web_search", "websearch"]);
const SKILL_PATH = "knowledge-based-search/SKILL.md";
const SKILL_DENY_REASON =
	"Load the knowledge-based-search skill first, then rerun the kbs command.";
const WEB_SEARCH_DENY_REASON =
	"Built-in web search is disabled. Use kbs through Bash or a configured Linkup tool instead.";

function hasLoadedKbsSkill(entries: unknown): boolean {
	return JSON.stringify(entries).includes(SKILL_PATH);
}

export default function (pi: ExtensionAPI) {
	pi.on("tool_call", (event, ctx) => {
		if (WEB_SEARCH_TOOLS.has(event.toolName)) {
			return { block: true, reason: WEB_SEARCH_DENY_REASON };
		}
		if (
			event.toolName === "bash" &&
			KBS_COMMAND.test(event.input.command ?? "") &&
			!hasLoadedKbsSkill(ctx.sessionManager.getEntries())
		) {
			return { block: true, reason: SKILL_DENY_REASON };
		}
		return undefined;
	});
}
