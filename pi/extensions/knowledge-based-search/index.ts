import { execFile } from "node:child_process";
import { promisify } from "node:util";
import * as path from "node:path";

const run = promisify(execFile);
const ROOT = path.resolve(__dirname, "../../..");
const HOOKS = path.join(ROOT, "hooks");

async function pythonHook(script: string, input: unknown): Promise<string | undefined> {
  try {
    const child = execFile("python3", [path.join(HOOKS, script)], {
      cwd: HOOKS,
      env: { ...process.env, PYTHONPATH: HOOKS },
    });
    child.stdin?.end(JSON.stringify(input ?? {}));
    const stdout = await new Promise<string>((resolve, reject) => {
      let out = "";
      let err = "";
      child.stdout?.on("data", chunk => {
        out += chunk;
      });
      child.stderr?.on("data", chunk => {
        err += chunk;
      });
      child.on("error", reject);
      child.on("close", code => {
        if (code === 0) resolve(out.trim());
        else reject(new Error(err || `hook exited ${code}`));
      });
    });
    return stdout || undefined;
  } catch {
    return undefined;
  }
}

function contextFromHook(stdout: string | undefined): string | undefined {
  if (!stdout) return undefined;
  try {
    const data = JSON.parse(stdout);
    return data?.hookSpecificOutput?.additionalContext;
  } catch {
    return undefined;
  }
}

export default function (pi: any) {
  pi.on("before_agent_start", async (event: any) => {
    const stdout = await pythonHook("session_start.py", event ?? {});
    const primer = contextFromHook(stdout);
    if (!primer) return undefined;
    return { systemPrompt: `${event.systemPrompt}\n\n${primer}` };
  });

  pi.on("prompt", async (event: any) => {
    const prompt = event?.prompt ?? event?.message ?? event?.input ?? "";
    const stdout = await pythonHook("prompt_inject.py", { prompt });
    const nudge = contextFromHook(stdout);
    if (!nudge) return undefined;
    return { systemPrompt: `${event.systemPrompt ?? ""}\n\n${nudge}` };
  });
}
