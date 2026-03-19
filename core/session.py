import json
import os
import time
from dataclasses import dataclass, field
from .model_state import ModelState

SCHEMA_VERSION = 1

class SessionManager:
    def __init__(self):
        self.conversation: list[dict] = []
        self.model_state: ModelState = ModelState()
        self._key_decision_indices: set[int] = set()

    def add_message(self, role, content, intents_executed=None):
        msg = {"role": role, "content": content, "timestamp": time.time(), "is_key_decision": False}
        if intents_executed:
            msg["intents_executed"] = intents_executed
        self.conversation.append(msg)

    def mark_key_decision(self, index):
        if 0 <= index < len(self.conversation):
            self.conversation[index]["is_key_decision"] = True
            self._key_decision_indices.add(index)

    def get_context_messages(self, max_turns=10):
        # Key decisions + recent N turns, deduped
        messages = []
        key_msgs = [m for m in self.conversation if m.get("is_key_decision")]
        max_messages = max_turns * 2
        recent_start = max(0, len(self.conversation) - max_messages)
        recent_msgs = self.conversation[recent_start:]
        seen = set()
        for msg in key_msgs:
            key = (msg["role"], msg["content"])
            if key not in seen:
                messages.append({"role": msg["role"], "content": msg["content"]})
                seen.add(key)
        for msg in recent_msgs:
            key = (msg["role"], msg["content"])
            if key not in seen:
                messages.append({"role": msg["role"], "content": msg["content"]})
                seen.add(key)
        return messages

    def save_project(self, base_dir, project_name):
        project_dir = os.path.join(base_dir, project_name)
        os.makedirs(project_dir, exist_ok=True)
        with open(os.path.join(project_dir, "project.json"), "w", encoding="utf-8") as f:
            json.dump({"schema_version": SCHEMA_VERSION, "name": project_name, "created": time.time()}, f, ensure_ascii=False, indent=2)
        with open(os.path.join(project_dir, "session.json"), "w", encoding="utf-8") as f:
            json.dump({"schema_version": SCHEMA_VERSION, "conversation": self.conversation, "model_state": self.model_state.to_dict()}, f, ensure_ascii=False, indent=2)

    def load_project(self, base_dir, project_name):
        session_path = os.path.join(base_dir, project_name, "session.json")
        if not os.path.exists(session_path):
            return False
        with open(session_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.conversation = data.get("conversation", [])
        if "model_state" in data:
            self.model_state = ModelState.from_dict(data["model_state"])
        self._key_decision_indices = {i for i, m in enumerate(self.conversation) if m.get("is_key_decision")}
        return True

    def clear(self):
        self.conversation.clear()
        self.model_state = ModelState()
        self._key_decision_indices.clear()
