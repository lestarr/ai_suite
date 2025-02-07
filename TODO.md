# Pipeline Architecture Cleanup TODOs

1. Resource Manager - this has to be discussed
   - Create ResourceManager class to handle:
     - LLM client initialization and config
     - Token tracking
     - Output directory structure and paths
     - Logging setup and configuration
   - Move all resource handling from BaseAgent/PipelineController to ResourceManager
   - Add proper cleanup methods

# Code Cleanup TODOs - this has to be done

1. BaseAgent Redundancy

   - Remove duplicated output_dir from child agents (currently set in both base and child)
   - Move all LLM, token_tracker, logger handling to base initialization
   - Create standard get_dir() methods in base for common paths
   - Consider making BaseAgent handle all common file operations

2. Agent Initialization

   - Simplify agent constructors by using base class properly
   - Remove redundant parameter passing (output_dir, model_name etc.)
   - Make BaseAgent.**init** handle all common parameters
   - Consider making some agents not need LLM client if they don't use it!!!

3. Pipeline Controller

   - Move agent creation logic to factory completely
   - Make factory handle all common agent parameters
   - Consider making agent configuration more declarative
   - Remove redundant parameter passing through pipeline layers

4. Directory Structure
   - Standardize directory creation and access
   - Move all path handling to one place
   - Make directory structure configurable but with sensible defaults
   - Consider making paths relative to base_output_dir

5. logging into file
   - move logging into file
