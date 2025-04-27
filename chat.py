from flask import Flask, request, jsonify, render_template
from interpreter import OpenInterpreter
import json
import os
import threading
import uuid
from datetime import datetime

# Set up Flask with template folder location
template_dir = os.path.abspath('templates')
app = Flask(__name__, template_folder=template_dir)

# ======================
# Agent Manager Class
# ======================
class AgentManager:
    def __init__(self):
        self.agents = {}
        self.assistant_agents = {}  # Track assistant agents mapping
        self.lock = threading.Lock()
        
    def create_agent(self, config=None, is_assistant=False, main_agent_id=None):
        """Create a new agent instance with optional configuration"""
        agent_id = str(uuid.uuid4())
        interpreter = OpenInterpreter()
        
        # Default configuration
        #interpreter.llm.model = "openai/deepseek-chat"
        #interpreter.llm.api_base = "https://api.deepseek.com/v1"
        #interpreter.llm.api_key = "sk-7fd014d945684bf5b00c27c092d8866c"
        interpreter.llm.model = "openai/agent-sin"
        interpreter.llm.api_base = "https://chat.musicheardworldwide.com/api"
        interpreter.llm.api_key = "sk-8c03941b535d4040b677b9fdb4ff4b77"
        interpreter.llm.temperature = 0.05
        interpreter.llm.context_window = 128000
        interpreter.llm.max_tokens = 4096
        interpreter.auto_run = True
        
        # Load system instructions from file if it exists
        try:
            with open('/app/system_instructions.md', 'r') as f:
                interpreter.system_message = f.read()
        except FileNotFoundError:
            # Fallback to default system message
            interpreter.system_message = "You are a helpful AI assistant integrated with MCPO. You can install and use MCP tools to extend your capabilities."
            
        interpreter.loop = True
        interpreter.llm.supports_functions = True
        interpreter.llm.supports_vision = False 
        interpreter.computer.import_computer_api = True
        
        # Set specific system message for assistant agents
        if is_assistant:
            interpreter.system_message = "You are an assistant agent whose purpose is to help the main agent with planning and executing small tasks. Be concise and helpful."
        
        # Apply custom configuration if provided
        if config:
            for key, value in config.items():
                setattr(interpreter, key, value)
        
        # Register default tools
        self._register_default_tools(interpreter)
        
        with self.lock:
            self.agents[agent_id] = {
                'interpreter': interpreter,
                'created_at': datetime.now().isoformat(),
                'last_used': datetime.now().isoformat(),
                'config': config or {},
                'is_assistant': is_assistant,
                'main_agent_id': main_agent_id
            }
            
            # If this is an assistant agent, link it to the main agent
            if is_assistant and main_agent_id:
                if main_agent_id not in self.assistant_agents:
                    self.assistant_agents[main_agent_id] = []
                self.assistant_agents[main_agent_id].append(agent_id)
        
        return agent_id
    
    def create_assistant_for_agent(self, main_agent_id, config=None):
        """Create an assistant agent for a main agent"""
        if main_agent_id not in self.agents:
            return None
        
        return self.create_agent(config, is_assistant=True, main_agent_id=main_agent_id)
    
    def get_agent(self, agent_id):
        """Retrieve an agent by ID"""
        with self.lock:
            agent = self.agents.get(agent_id)
            if agent:
                agent['last_used'] = datetime.now().isoformat()
                return agent
            return None
    
    def get_assistant_agents(self, main_agent_id):
        """Get all assistant agents for a main agent"""
        with self.lock:
            assistant_ids = self.assistant_agents.get(main_agent_id, [])
            return {
                assistant_id: self.agents[assistant_id] 
                for assistant_id in assistant_ids 
                if assistant_id in self.agents
            }
    
    def list_agents(self):
        """List all active agents"""
        with self.lock:
            return {
                agent_id: {
                    'created_at': info['created_at'],
                    'last_used': info['last_used'],
                    'config': info['config'],
                    'is_assistant': info.get('is_assistant', False),
                    'main_agent_id': info.get('main_agent_id'),
                    'has_assistants': agent_id in self.assistant_agents and len(self.assistant_agents[agent_id]) > 0
                }
                for agent_id, info in self.agents.items()
            }
    
    def remove_agent(self, agent_id):
        """Remove an agent by ID"""
        with self.lock:
            agent = self.agents.pop(agent_id, None)
            
            # If this is a main agent, remove all its assistants
            if agent_id in self.assistant_agents:
                for assistant_id in self.assistant_agents[agent_id]:
                    self.agents.pop(assistant_id, None)
                self.assistant_agents.pop(agent_id)
            
            # If this is an assistant agent, remove from main agent's assistant list
            for main_id, assistants in list(self.assistant_agents.items()):
                if agent_id in assistants:
                    self.assistant_agents[main_id].remove(agent_id)
                    if not self.assistant_agents[main_id]:
                        del self.assistant_agents[main_id]
                    break
            
            return agent
    
    def delegate_to_assistant(self, main_agent_id, assistant_agent_id, task):
        """Delegate a task from main agent to assistant agent"""
        main_agent = self.get_agent(main_agent_id)
        assistant_agent = self.get_agent(assistant_agent_id)
        
        if not main_agent or not assistant_agent:
            return None
            
        if not assistant_agent.get('is_assistant') or assistant_agent.get('main_agent_id') != main_agent_id:
            return None
            
        interpreter = assistant_agent['interpreter']
        try:
            response = ""
            for chunk in interpreter.chat(f"Task from main agent: {task}", stream=True, display=False):
                if isinstance(chunk, dict):
                    if chunk.get("type") == "message":
                        response += chunk.get("content", "")
                elif isinstance(chunk, str):
                    try:
                        json_chunk = json.loads(chunk)
                        response += json_chunk.get("response", "")
                    except json.JSONDecodeError:
                        response += chunk
            return response.strip()
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _register_default_tools(self, interpreter):
        """Register default tools for new agents"""
        # Time tool
        time_tool = """
        from datetime import datetime
        import pytz
        
        def get_time(timezone="UTC", format="%Y-%m-%d %H:%M:%S"):
            \"\"\"Get current time in specified timezone\"\"\"
            tz = pytz.timezone(timezone)
            return datetime.now(tz).strftime(format)
        """
        interpreter.computer.run("python", time_tool)

# Initialize agent manager
agent_manager = AgentManager()

# ======================
# API Endpoints
# ======================
@app.route('/agent/create', methods=['POST'])
def create_agent():
    """Create a new agent instance"""
    config = request.json.get('config', {})
    agent_id = agent_manager.create_agent(config)
    return jsonify({"agent_id": agent_id, "status": "created"})

@app.route('/agent/<agent_id>/chat', methods=['POST'])
def agent_chat(agent_id):
    """Chat with a specific agent"""
    agent_info = agent_manager.get_agent(agent_id)
    if not agent_info:
        return jsonify({"error": "Agent not found"}), 404
    
    data = request.json
    prompt = data.get('prompt')
    messages = data.get('messages', [])
    
    if not prompt and not messages:
        return jsonify({"error": "No prompt or messages provided"}), 400
    
    interpreter = agent_info['interpreter']
    
    # Prepare input based on what was provided
    if prompt:
        input_data = prompt
    else:
        input_data = messages
    
    full_response = ""
    try:
        for chunk in interpreter.chat(input_data, stream=True, display=False):
            if isinstance(chunk, dict):
                if chunk.get("type") == "message":
                    full_response += chunk.get("content", "")
            elif isinstance(chunk, str):
                try:
                    json_chunk = json.loads(chunk)
                    full_response += json_chunk.get("response", "")
                except json.JSONDecodeError:
                    full_response += chunk
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"response": full_response.strip(), "agent_id": agent_id})

@app.route('/agent/<agent_id>/multi_agent_chat', methods=['POST'])
def multi_agent_chat(agent_id):
    """Initiate a conversation between multiple agents"""
    data = request.json
    other_agent_ids = data.get('other_agent_ids', [])
    initial_message = data.get('initial_message', "Hello!")
    max_turns = data.get('max_turns', 5)
    
    # Verify all agents exist
    agents = []
    all_agent_ids = [agent_id] + other_agent_ids
    for a_id in all_agent_ids:
        agent = agent_manager.get_agent(a_id)
        if not agent:
            return jsonify({"error": f"Agent {a_id} not found"}), 404
        agents.append(agent['interpreter'])
    
    # Initialize conversation
    messages = [{"role": "user", "message": initial_message}]
    conversation_log = {a_id: [] for a_id in all_agent_ids}
    
    def swap_roles(messages):
        """Swap user and assistant roles for conversation turns"""
        for message in messages:
            if message['role'] == 'user':
                message['role'] = 'assistant'
            elif message['role'] == 'assistant':
                message['role'] = 'user'
        return messages
    
    # Run the conversation
    for turn in range(max_turns):
        for i, agent in enumerate(agents):
            current_agent_id = all_agent_ids[i]
            try:
                response = list(agent.chat(messages, stream=True, display=False))
                last_message = response[-1] if response else {}
                
                if isinstance(last_message, dict) and 'content' in last_message:
                    conversation_log[current_agent_id].append({
                        "turn": turn,
                        "message": last_message['content']
                    })
                    messages = [{"role": "assistant", "message": last_message['content']}]
                messages = swap_roles(messages)
            except Exception as e:
                conversation_log[current_agent_id].append({
                    "turn": turn,
                    "error": str(e)
                })
    
    return jsonify({
        "conversation": conversation_log,
        "turns": max_turns,
        "agents": all_agent_ids
    })

@app.route('/agent/list', methods=['GET'])
def list_agents():
    """List all active agents"""
    return jsonify(agent_manager.list_agents())

@app.route('/agent/<agent_id>/remove', methods=['DELETE'])
def remove_agent(agent_id):
    """Remove an agent"""
    result = agent_manager.remove_agent(agent_id)
    if result:
        return jsonify({"status": "removed", "agent_id": agent_id})
    return jsonify({"error": "Agent not found"}), 404

@app.route('/agent/<agent_id>/create_assistant', methods=['POST'])
def create_assistant_agent(agent_id):
    """Create an assistant agent for a main agent"""
    config = request.json.get('config', {})
    
    assistant_id = agent_manager.create_assistant_for_agent(agent_id, config)
    if not assistant_id:
        return jsonify({"error": "Main agent not found"}), 404
    
    return jsonify({
        "assistant_id": assistant_id, 
        "main_agent_id": agent_id,
        "status": "created"
    })

@app.route('/agent/<agent_id>/assistants', methods=['GET'])
def get_assistant_agents(agent_id):
    """Get all assistant agents for a main agent"""
    assistants = agent_manager.get_assistant_agents(agent_id)
    if assistants is None:
        return jsonify({"error": "Main agent not found"}), 404
    
    # Format the response to exclude interpreter objects
    formatted_assistants = {
        assistant_id: {
            'created_at': info['created_at'],
            'last_used': info['last_used'],
            'config': info['config']
        }
        for assistant_id, info in assistants.items()
    }
    
    return jsonify({
        "main_agent_id": agent_id,
        "assistants": formatted_assistants
    })

@app.route('/agent/<agent_id>/delegate/<assistant_id>', methods=['POST'])
def delegate_to_assistant(agent_id, assistant_id):
    """Delegate a task from main agent to assistant agent"""
    data = request.json
    task = data.get('task')
    
    if not task:
        return jsonify({"error": "No task provided"}), 400
    
    response = agent_manager.delegate_to_assistant(agent_id, assistant_id, task)
    if response is None:
        return jsonify({"error": "Invalid agent IDs or relationship"}), 404
    
    return jsonify({
        "main_agent_id": agent_id,
        "assistant_id": assistant_id,
        "task": task,
        "response": response
    })

# ======================
# Chat UI
# ======================
@app.route('/', methods=['GET'])
def chat_ui():
    """Serve the chat UI at the root path"""
    return render_template('chat.html')

# ======================
# Initialization
# ======================
if __name__ == '__main__':
    print("""
    Open Interpreter Multi-Agent Server is running!
    
    Endpoints:
    - POST   /agent/create             : Create new agent
    - POST   /agent/<id>/chat          : Chat with an agent
    - POST   /agent/<id>/multi_agent_chat : Multiple agents conversation
    - GET    /agent/list               : List all agents
    - DELETE /agent/<id>/remove        : Remove an agent
    - POST   /agent/<id>/create_assistant : Create an assistant agent
    - GET    /agent/<id>/assistants    : Get all assistant agents for a main agent
    - POST   /agent/<id>/delegate/<assistant_id> : Delegate task to assistant agent
    
    Server running on http://0.0.0.0:5001
    """)
    app.run(host='0.0.0.0', port=5001, threaded=True)