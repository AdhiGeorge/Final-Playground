---
trigger: manual
---

# Agentic Researcher - OpenAI Swarm Rules

## 🤖 Agent Architecture
- **Maximum 150 lines per file** (including comments)
- One agent class per file with clear responsibilities
- Separate agent definitions, tools, and orchestration logic
- Use descriptive agent names (SearchAgent, AnalysisAgent)
- Implement agent handoff patterns with proper context transfer
- Create agent hierarchies: Coordinator → Specialists → Validators
- Use factory patterns for agent creation with configuration

## 🔧 Swarm Framework Standards
- Define agents with clear `instructions` and `functions`
- Use `transfer_to_agent()` for proper handoffs with context
- Implement context preservation across agent transfers
- Keep agent tools focused and atomic (single purpose)
- Use `context_variables` for shared state management
- Implement proper message threading for conversation continuity
- Use agent.name consistently for routing decisions
- Handle agent initialization parameters properly

## 🛠️ Tool Design
- One tool per function with single responsibility
- Tools under 20 lines when possible
- Return structured data (JSON/dict) from tools
- Implement proper error handling in all tools
- Use type hints for tool parameters and returns
- Include docstrings with parameter descriptions
- Validate input parameters before processing
- Use descriptive tool names (search_arxiv, analyze_sentiment)

## 🔍 Research-Specific Patterns
- **Search agents**: Web search, academic databases, document retrieval
- **Analysis agents**: Data processing, summarization, fact-checking
- **Synthesis agents**: Report generation, insight compilation
- **Validation agents**: Source verification, quality control
- Implement citation tracking and source management
- Use research methodology validation (peer review simulation)
- Implement multi-source cross-referencing
- Create research session state management

## 🔒 API & Security
- Store OpenAI API keys in environment variables
- Implement rate limiting for API calls (requests per minute)
- Use exponential backoff for retries (2^n seconds)
- Validate all external API responses before processing
- Never log API keys or sensitive research data
- Implement token usage monitoring and budget controls
- Sanitize research queries to prevent prompt injection
- Use secure storage for research artifacts and findings

## 🚀 Performance & Reliability
- Cache expensive research operations
- Implement async operations for concurrent research
- Use connection pooling for database operations
- Handle API timeouts gracefully
- Implement circuit breakers for external services
- Monitor agent execution times

## 📊 Data Management
- Use structured data formats (JSON, Pydantic models)
- Implement proper data validation schemas (Pydantic BaseModel)
- Store research artifacts with metadata (timestamps, sources)
- Use vector databases for semantic search (Chroma, Pinecone)
- Implement proper database indexing for fast retrieval
- Handle large document processing efficiently (chunking)
- Implement data versioning for research iterations

## 🧪 Testing Multi-Agent Systems
- Unit tests for individual agent functions
- Integration tests for agent handoff flows
- Mock external APIs in tests
- Test error propagation across agents
- Validate context preservation
- Test concurrent agent execution

## 📝 Documentation & Logging
- Document agent responsibilities and capabilities
- Log agent transitions and decision points
- Track research progress and intermediate results
- Use structured logging (JSON format)
- Implement conversation/research session tracking
- Document tool usage and parameters

## 🔄 Orchestration Patterns
- Use client.run() with proper message handling
- Implement conversation state management with persistence
- Handle agent switching logic cleanly with decision trees
- Use context variables for cross-agent data sharing
- Implement proper error recovery flows and fallback agents
- Track research workflow progress with status indicators
- Use event-driven architecture for agent communication

## 🎯 Research Quality
- Implement source credibility scoring (domain authority, date)
- Use multiple agents for fact verification and cross-validation
- Implement bias detection mechanisms and perspective analysis
- Track information provenance and citation chains
- Validate research completeness against predefined criteria
- Implement quality metrics tracking (accuracy, relevance)
- Use confidence scoring for research findings

## 🚫 Prohibited Practices
- Hardcoded API keys or credentials
- Infinite agent loops without exit conditions
- Blocking operations in async contexts
- Unhandled exceptions in agent functions
- Mixing research logic with UI code
- Direct database access from agents

## ✅ Pre-Commit Checklist
- [ ] File under 150 lines with focused responsibility
- [ ] Agent responsibilities clearly defined with instructions
- [ ] All API calls have error handling and retries
- [ ] Context variables used properly for state sharing
- [ ] Tools return structured data with type hints
- [ ] Agent handoffs tested with proper context transfer
- [ ] No hardcoded credentials or API keys
- [ ] Research artifacts properly stored with metadata
- [ ] Logging implemented for debugging and monitoring
- [ ] Performance optimizations applied (caching, async)
- [ ] Input validation implemented for all tools
- [ ] Research quality checks implemented