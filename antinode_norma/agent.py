import json
import logging
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from .utils.llm_factory import create_llm_callable

logger = logging.getLogger(__name__)


@dataclass
class AgentState:
    goal: str
    history: List[Dict] = field(default_factory=list)
    current_story_id: Optional[str] = None
    current_story_text: Optional[str] = None  # store the last submitted story text
    current_story: Optional[Dict] = None
    feature_path: Optional[str] = None
    test_results: Optional[Dict] = None
    pr_url: Optional[str] = None
    iteration: int = 0
    done: bool = False
    errors: int = 0
    last_action: Optional[str] = None


class BDDAgent:
    def __init__(
        self, llm_config: Dict[str, Any], tool_registry: Dict[str, Any], max_iterations: int = 10
    ):
        self.llm = create_llm_callable(llm_config)
        self.tools = tool_registry
        self.max_iterations = max_iterations
        self.state = AgentState(goal="")

    def run(self, goal: str) -> Dict:
        self.state = AgentState(goal=goal)
        while not self.state.done and self.state.iteration < self.max_iterations:
            self.state.iteration += 1
            action = self._plan()
            if action.get("type") == "finish":
                self.state.done = True
                break
            # Auto‑fix common issues: if improve_story is called without raw_text, inject it from state
            if action.get("tool") == "improve_story":
                args = action.get("args", {})
                if "raw_text" not in args and "story" not in args and "text" not in args:
                    if self.state.current_story_text:
                        args["raw_text"] = self.state.current_story_text
                        action["args"] = args
                        logger.info("Auto‑injected raw_text for improve_story")
            result = self._execute(action)
            self.state.history.append({"action": action, "result": result})
            self._update_state(action, result)
            if isinstance(result, dict) and "error" in result:
                self.state.errors += 1
            else:
                self.state.errors = 0
            if self.state.errors >= 3:
                self.state.done = True
                self.state.history.append(
                    {
                        "action": {"type": "finish"},
                        "result": "Too many consecutive errors, aborting.",
                    }
                )
                break
        if not self.state.done:
            self.state.done = True
            self.state.history.append(
                {"action": {"type": "finish"}, "result": "Max iterations reached."}
            )
        return self._final_state()

    def _plan(self) -> Dict:
        logging.basicConfig(level=logging.DEBUG)
        prompt = self._build_planner_prompt()
        response = self.llm(prompt)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            match = re.search(r"```json\s*([\s\S]*?)\s*```", response)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            match = re.search(r"\{[\s\S]*\}", response)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            return {"type": "finish", "reason": "Could not parse LLM response."}

    def _execute(self, action: Dict) -> Any:
        logging.basicConfig(level=logging.DEBUG)
        tool_name = action.get("tool")
        args = action.get("args", {})
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}
        try:
            result = self.tools[tool_name](**args)
            return result
        except Exception as e:
            logger.exception(f"Tool {tool_name} failed")
            return {"error": str(e)}

    def _update_state(self, action: Dict, result: Any):
        if action.get("tool") == "submit_story" and isinstance(result, dict):
            if "story_id" in result:
                self.state.current_story_id = result["story_id"]
            if "story" in result:
                self.state.current_story = result["story"]
            if "raw_text" in action.get("args", {}):
                self.state.current_story_text = action["args"]["raw_text"]
        elif action.get("tool") == "generate_feature" and isinstance(result, dict):
            self.state.feature_path = result.get("feature_path")
        elif action.get("tool") == "run_tests" and isinstance(result, dict):
            self.state.test_results = result
        elif action.get("tool") == "create_pr" and isinstance(result, dict):
            self.state.pr_url = result.get("pr_url")

    def _final_state(self) -> Dict:
        return {
            "done": self.state.done,
            "iteration": self.state.iteration,
            "story_id": self.state.current_story_id,
            "feature_path": self.state.feature_path,
            "test_results": self.state.test_results,
            "pr_url": self.state.pr_url,
            "history": self.state.history,
        }

    def _build_planner_prompt(self) -> str:
        tools_desc = "\n".join(
            [
                f"- {name}: {self.tools[name].__doc__ or 'No description provided.'}"
                for name in self.tools
            ]
        )
        history = (
            "\n".join(
                [
                    f"Step {i+1}: {h['action'].get('tool', 'unknown')} -> {str(h['result'])[:200]}"
                    for i, h in enumerate(self.state.history)
                ]
            )
            if self.state.history
            else "No actions taken yet."
        )

        return f"""
You are a BDD automation assistant. Your goal: {self.state.goal}

Available tools:
{tools_desc}

IMPORTANT:
- When calling submit_story, use parameter 'raw_text' for the story.
- When calling improve_story, use parameter 'raw_text' for the story you want to improve.
- If a tool returns an error, try a different approach or finish.

Current history:
{history}

Based on the goal and history, decide the next action. Return ONLY a JSON object:
- To call a tool: {{"type": "tool", "tool": "<name>", "args": {{...}}}}
- If the goal is complete: {{"type": "finish", "reason": "..."}}

If the story fails quality twice, consider finishing and report the issues.
"""
